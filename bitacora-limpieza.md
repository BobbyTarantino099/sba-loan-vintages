<!-- Phase 3 deliverable. Raw data is NEVER modified in place: every transformation
     produces a new file and is logged here. Written as you clean, not afterwards. -->

# Cleaning log — SBA 7(a) loan vintages

**Input datasets:** `datos/crudos/sba_7a_{1991-1999,2000-2009,2010-2019,2020-2026}_2026-06-30.csv`
— 1,961,455 loan approvals × 42 columns, 901 MB, publisher's cut-off 2026-06-30.

**Output dataset:** `datos/limpios/sba-loan-vintages.duckdb` — table `prestamos`, **1,697,539 rows**
(1 row = one disbursed loan), plus the faithful load `raw_7a` (1,961,455 rows).

**Tool: SQL on DuckDB.** Chosen because the work is one flat table of two million rows that needs
filtering, banding and a window function for within-cohort quartiles — exactly what SQL does well —
and because DuckDB reads the four CSVs straight off disk with no import step and no server. Nothing
here needs a dataframe: there is no reshaping, no merging of heterogeneous sources, no iteration.
Python appears only as a thin runner (`notebooks/procesar.py`) that resolves paths, counts rows and
asserts; every transformation is in `consultas/*.sql`, where it can be read and audited.

**Reproduce:** `python notebooks/procesar.py`. It rebuilds the database from scratch — it deletes
any previous one first, because a pipeline that reuses state is not reproducible — and fails loudly
if the counts stop matching what phase 2 closed with.

---

## Transformations

| # | What | Why | How | Rows in → out |
|---|---|---|---|---|
| **T1** | Load the four CSVs into `raw_7a`, cast to types | Separate "loss caused by a decision" from "loss caused by loading". Read as `all_varchar` and cast explicitly, because letting DuckDB infer across four files can resolve differently in each and the difference is invisible until a sum comes out wrong | `consultas/01_construir_base.sql`, glob over the four files with `filename = true` to keep `archivo_origen` | 1,961,455 → 1,961,455 |
| **T2** | Drop `CANCLD` and `COMMIT` | Neither ever put money at risk — the official dictionary defines `COMMIT` as "Undisbursed". A loss rate cannot have them in numerator or denominator | `WHERE estado IN ('P I F','CHGOFF','EXEMPT')` | 1,961,455 → 1,697,542 (−242,790 cancelled, −21,123 undisbursed) |
| **T3** | Drop non-positive approval amounts | 3 rows, one at −$120,000. Noise, but counted rather than silently dropped | `AND importe_aprobado > 0` | 1,697,542 → **1,697,539** |
| **T4** | Label cohort, age, and the three cuts | The analysis needs age at default, not just default | `consultas/02_poblacion.sql` | 1,697,539 → 1,697,539 (no rows lost; every row labelled) |

Reconciliation: 1,961,455 − 242,790 − 21,123 − 3 = 1,697,539. ✅ Checked in code, not by hand:
`procesar.py` raises and stops if it does not balance.

---

## The decisions, and why they went the way they did

### 1. `EXEMPT` stays in the denominator

The decision the whole case rests on. The publisher's dictionary defines `EXEMPT` as a loan
**disbursed but not cancelled, paid in full or charged off** — i.e. still alive at the cut-off,
withheld under FOIA Exemption 4. It is not missing data; it is the censoring indicator, handed over
explicitly.

297,494 loans (17.5% of the population) are `EXEMPT`, and their share rises from 0.7% of FY1991 to
76.8% of FY2024. Dropping them as "unknown outcome" would delete most of the recent population and
make new cohorts look nearly default-free. They stay, as population at risk that has not yet
experienced the event.

### 2. Charge-offs whose date cannot be used — 90 loans

Two populations, same treatment:

- **58** are marked `CHGOFF` with no charge-off date at all.
- **32** carry a charge-off date **later than the file's own cut-off** — 31 on 2026-07-01, one day
  after, and one on 2026-10-22, nearly four months after. The file contradicts its own `AsOfDate`
  of 2026-06-30.

Both count in the terminal loss rate — they defaulted — but neither can be placed on the maturation
curve, because the timing is unknown or untrustworthy. They are flagged `fallido_sin_fecha_util`
and excluded from the age numerator without leaving the population. 90 of 220,688 charge-offs:
0.04%.

**What was deliberately not done:** clamping those dates to the cut-off. That would invent an age
nobody observed and pile all 32 into a single month at the far right of the curve — precisely where
the case makes its claim.

> Found by a guard in `procesar.py`, not by inspection. The phase 2 integrity test checked for
> charge-offs *before* approval and found none; it never thought to check for charge-offs *after*
> the cut-off. The assertion is now permanent.

### 3. Duplicates are not removed

The file carries no loan number, so "duplicate" has to be defined by a composite key. On
borrower + approval date + amount + bank, 3,581 keys repeat, covering 7,393 rows (0.4%).

The evidence says these are mostly **distinct loans**: of those 3,581 keys, 2,147 differ in term,
457 in guaranteed amount, 453 in processing method, and 235 have different outcomes. One example —
same business, same day, same $5,000, same bank, but one loan of 16 months that charged off and one
of 84 months that paid in full.

Only **403 groups (519 surplus rows, 0.03% of the population)** are identical across all 42 columns,
and even those may be genuine twin loans rather than duplicated records. Nothing is removed. The
bound is stated instead: if all 519 were false charge-offs, the aggregate rate would move by less
than 0.04 pp against a rate of 13.0%. `procesar.py` prints this bound on every run.

Reproduce the diagnosis directly against the raw files (`BorrName` is not carried into the clean
table — see decision 7):

```sql
WITH g AS (
  SELECT BorrName, ApprovalDate, GrossApproval, BankName, count(*) AS n
  FROM read_csv('datos/crudos/sba_7a_*.csv', all_varchar = true)
  WHERE LoanStatus IN ('P I F','CHGOFF','EXEMPT')
  GROUP BY 1,2,3,4 HAVING count(*) > 1)
SELECT count(*) AS claves, sum(n) AS filas FROM g;
```

### 4. Implausible terms become `unknown`, the loans stay

1,442 loans fall outside a believable term: 1,359 with a term of 0 months (850 term loans and 509
revolvers, where "no fixed term" is at least meaningful) and 85 with terms from 361 to 569 months —
none of them revolvers, and against a 99th percentile of 300 months.

They are real disbursed loans and belong in the overall curve. Term is only needed for one cut, so
they get `tramo_plazo = 'unknown'`: they count everywhere except in the term breakdown. Dropping
them would have removed real defaults to tidy up a cut they do not participate in.

### 5. Sector is `unknown` before FY2001, and the cut is restricted

`NaicsCode` is null for 176,913 disbursed loans — 55–57% of every year before FY2001 and ~0%
afterwards, because SBA adopted NAICS at that boundary. Nothing is imputed: there is nothing to
impute from. The rows keep `sector = 'unknown'`, stay in the overall curve, and **the sector cut is
restricted to FY2001+**, which the case page has to say out loud.

Three NAICS sectors are published as ranges and are collapsed, or Manufacturing would appear split
across three bars that nobody would know to add up: `31,32,33 → 31-33`, `44,45 → 44-45`,
`48,49 → 48-49`.

### 6. FY2026 is marked as a partial cohort

The US federal fiscal year runs 1 October to 30 September, but the data stops on 2026-06-30. FY2026
therefore holds nine months of approvals (23,243 disbursed), not twelve. It is flagged
`cohorte_parcial` — kept in the counts, excluded from every comparison between vintages, where it
would put nine months against twelve.

### 7. Size bands are quartiles *within* the cohort

A $100,000 loan was large in 1993 and mid-sized in 2025. Quartiling across the whole history would
turn the size band into a disguised clock, and the cut would measure inflation and programme growth
rather than risk. `ntile(4) OVER (PARTITION BY anio_fiscal ORDER BY importe_aprobado)`.

### 8. Borrower-identifying columns are never loaded

`BorrName`, `BorrStreet`, `BorrCity`, `BorrZip` and the bank address block are not carried from the
raw file into `raw_7a` at all. Not loading them is a stronger guarantee than loading them and
promising not to use them. Also dropped: `InitialInterestRate` (51% null — it cannot support a
pricing cut), `Program` (constant, since the 504 files were never downloaded), `JobsSupported`
(lender-reported and explicitly unaudited by the publisher) and other columns the analysis does not
touch.

---

## Dirty-data review — every type checked, including the ones that came back clean

| Type | Result | Action |
|---|---|---|
| **Missing values** | `ApprovalDate`, `ApprovalFY`, `GrossApproval`, `TermInMonths`, `LoanStatus`: zero nulls. `NaicsCode` 10.4% (decision 5). `ChargeOffDate` null on 58 charge-offs (decision 2) | Documented; nothing imputed |
| **Type / cast losses** | Zero. Every date, amount and term cast without producing a null that was not already one | Asserted in `procesar.py` |
| **Duplicates** | 403 fully identical groups, 519 surplus rows (0.03%) | Kept, with the bound stated (decision 3) |
| **Inconsistent categories** | None. `estado` has exactly 3 values in the population, `revolvente` and `con_garantia_real` are `Y`/`N`, `tipo_negocio` has 3. No case or spelling variants | No action |
| **Whitespace** | 62 bank names and 5 state codes carry stray whitespace. `NaicsCode` clean | No action: neither column is a grouping key in this analysis. If a geography cut is ever added, `trim()` first |
| **Inconsistent formats** | None. All `NaicsCode` values are exactly 6 digits; all 61 state codes are 2 letters; all dates arrive ISO `YYYY-MM-DD` | No action |
| **Out-of-range values** | 3 approvals ≤ 0 (removed, T3); 1,442 implausible terms (decision 4); 32 charge-offs after the cut-off (decision 2) | See decisions |
| **Impossible values** | Zero charge-offs dated before their own approval | Asserted in `procesar.py` |
| **Internal contradictions** | Status and dates agree almost perfectly: every `P I F` has a payoff date and no charge-off date; every `CHGOFF` has a charge-off date (bar the 58) and no payoff date. **One** `EXEMPT` loan carries a payoff date | 1 row in 1.7 M; noted, not acted on |
| **Joins** | **None in this pipeline.** Single source, single flat table, no key to match on — so there is no before/after join count to reconcile | Stated for the record |
| **Case sensitivity** | DuckDB compares strings case-sensitively. The status value is `'P I F'`, with spaces, not `'PIF'`; `revolvente` is `Y`/`N` although the official dictionary documents it as `0`/`1`. Both verified 2026-08-31 and written into the query header | Literals match the file, not the dictionary |

### One finding for phase 4, not for phase 3

**180 charged-off loans carry a charge-off amount of zero** (220,688 charge-offs, 220,508 with a
positive amount). It changes nothing about the count-weighted rate, which is the case's primary
metric, but the dollar-weighted cross-check (V2) has to decide whether those are zero-loss
charge-offs or missing amounts before it can be read. Recorded here so phase 4 does not rediscover
it as a surprise.

---

## Exit gate — phase 3

- [x] **Tool chosen and justified** — SQL on DuckDB, reasoning at the top of this file.
- [x] **Every type of dirty data explicitly reviewed** — the table above, including the types that
      came back clean and the joins that do not exist.
- [x] **Log complete with what, why, how and how many rows** — the transformation table plus eight
      decisions.
- [x] **Count reconciliation balances** — 1,961,455 − 242,790 − 21,123 − 3 = 1,697,539, asserted in
      code.
- [x] **Outliers investigated and the decision justified** — terms, amounts, duplicates and
      post-cut-off charge-off dates, each with its own decision above.
- [x] **Process reproducible from raw** — `python notebooks/procesar.py` rebuilds from scratch and
      reproduces all six numbers that closed phase 2.
- [x] **The clean dataset still answers the question** — 220,598 charge-offs placed on the age axis
      across 35 cohorts, with 297,494 live loans as the censored population.

## Exit gate — SQL annex

- [x] Every published query carries a header with date, analyst and purpose.
- [x] Every computed column is aliased in `snake_case`.
- [x] Join counts before/after: **not applicable, and stated as such** — this pipeline has no joins.
- [x] Every `CASE` has an `ELSE` — four of them: `tramo_plazo`, `sector`, `edad_al_fallido`,
      `tramo_importe`.
- [x] No `COALESCE` imputation anywhere. Absent values stay absent and are labelled `unknown`.
- [x] Dialect case-sensitivity verified and documented in the query header.
- [x] Multi-step queries written as CTEs, not nested subqueries — `02_poblacion.sql` is
      `desembolsados` → `etiquetados` → final projection.
- [x] The queries run from scratch against the raw files and reproduce the result.
