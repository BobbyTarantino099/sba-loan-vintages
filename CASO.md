<!-- The living artefact of the case. It grows phase by phase; it is not written at the end.
     Each phase closes only when its exit gate passes point by point. If one fails, go BACK
     to an earlier phase instead of improvising forwards.
     Gates: site/framework/caso-de-estudio-datos/references/0X-*.md -->

# Case: SBA 7(a) loan vintages

**Status:** Phase 7 — Portfolio (next). Phases 0 to 6 closed.
**Last updated:** 2026-09-02

## 0. Choose (decision sheet)

**Date:** 2026-08-31

### The case
- **Sector / fictional client:** a private credit fund underwriting a portfolio of US small-business
  loans. The vantage point matters: a fund buying in *today* has to price loss it has not yet seen,
  which is exactly the question an originator reviewing its own back book never has to ask.
- **Business problem in one sentence:** the fund cannot set the expected loss in its underwriting
  model, because the charge-off rate observed for recent origination years is flattered by their
  age — those loans have not had time to default.
- **Decision it unlocks:** what expected-loss figure goes into the underwriting model, and which
  origination mix to avoid if a shock lands within the next three years.
- **Audience:** the investment committee (decides, not technical) and the analyst who inherits the
  model (reproduces it, technical). Two audiences, two registers — the site page serves the first,
  this repository the second.

### The data

| Source | Job in this case | Period / volume | Licence |
|---|---|---|---|
| [SBA 7(a) FOIA](https://data.sba.gov/dataset/7a-504-foia) | The whole analysis: one row per approved loan, with approval date, charge-off date and charge-off amount | FY1991–FY2026, as of 2026-06-30 · 4 CSV files · 901 MB | U.S. Government Works (public domain) |

- **Initial integrity test:** partial, run 2026-08-31 on the first 400 KB of each file *before*
  committing to the source. The four files share an **identical 42-column header**, so there is no
  schema reconciliation to do. `ChargeOffDate` is populated for essentially every `CHGOFF` row
  (107/109, 100/100, 87/87, 51/51 across the four samples) and dates arrive as ISO `YYYY-MM-DD`,
  not in mixed formats. `LoanStatus` shows four values in the sample: `P I F`, `CANCLD`, `CHGOFF`,
  `EXEMPT` — the full test found a fifth, `COMMIT`, which the sample missed. See phase 2.
  <!-- Caveat recorded deliberately: the files are ordered by approval date, so a leading slice is
       the first days of a fiscal year, not a random sample. Good enough for schema and for field
       coverage; useless for distributions. -->
- **Does it carry the fields the question demands?** Yes. `ApprovalDate` and `ChargeOffDate`
  together give age at default, which is the entire mechanism of the case. `TermInMonths`,
  `NaicsCode`, `GrossApproval` and `BankName` give the cuts; `GrossChargeOffAmount` allows a
  dollar-weighted rate alongside the count-weighted one.
- **What this source cannot answer:** these loans carry a **partial government guarantee**, so their
  loss behaviour is not identical to unguaranteed private credit — the shape of the maturation curve
  transfers, the level does not. The file records no recoveries after charge-off, so every figure
  here is gross loss, never net. And it holds approvals, not disbursements: a loan can be approved
  and never drawn.

### Calibration
- **Effort estimate:** ~5 days. The volume is large but single-source and single-key; the hard part
  is the maturation correction, which is thinking rather than plumbing.
- **Enough for a 30-minute talk?** Yes. The censoring correction alone carries ten minutes, and the
  2007 and 2020 cohorts carry another ten.
- **Real cleaning to document?** Yes — though less than expected, now that the headers turn out to
  match. What remains is real: `CANCLD` and `EXEMPT` are **not** defaults and poison the denominator
  if nobody looks; NAICS changes revision across 35 years; and the `EXEMPT` share looks far higher
  in recent years than in old ones, which would bite exactly where the case makes its claim.

### Portfolio fit
- **Why this one:** it fills three empty cells of the coverage matrix at once — a financial domain
  (the first two cases are video games and football), a problem type other than *find patterns*, and
  the first interactive piece on the site.
- **What it demonstrates that the others don't:** that a raw default rate **lies** when the cohorts
  being compared are of different ages, and that the analyst knew to correct for it. That single
  reflex is what separates a credit analyst from someone who can group rows in SQL.
- **Primary tool:** SQL on DuckDB, plus a vanilla-JS vintage explorer on the site.
- **Dataset saturation:** low. The Kaggle derivative of this data is used almost exclusively for
  binary approve/deny classification; the vintage-and-maturation angle is essentially unoccupied.

### Decision
- [x] Go
- [ ] Dropped — reason:

## 1. Ask

**Status:** closed — 2026-08-31

- **Business problem:** a private credit fund has to commit to an expected-loss assumption for US
  small-business loans **now**, and the only evidence available to it — charge-off rates by
  origination year — systematically understates loss for every cohort young enough to still be
  paying.
- **Analytical question (SMART):** across US SBA 7(a) loans approved between FY1991 and FY2026,
  **how does the cumulative charge-off rate evolve with months elapsed since approval, for each
  annual origination cohort — and once cohorts are compared at equal age rather than at a common
  observation date, what terminal loss do the immature cohorts imply?** Cuts: contracted term, loan
  size, NAICS sector. The denominator excludes cancelled loans.
- **Decision this unlocks:** the expected-loss figure entered into the underwriting model, and the
  origination mix the fund declines to buy.
- **Problem type:** `predict`. Projecting an immature cohort's terminal loss from the maturation
  curve of the completed ones is a prediction — made by actuarial extrapolation, with no machine
  learning involved. <!-- If phase 4 ends up purely descriptive, relabel as `find patterns` and do
  not force it. -->
- **Initial hypothesis** — written 2026-08-31, before any analysis:
  1. Cohorts originated **just before** a shock (FY2006–FY2007, FY2019) lose more than those
     originated during or just after it, because credit tightens once risk is already visible.
  2. Ranking cohorts by raw charge-off rate gives a **different ordering** than ranking them at
     equal age, and the recent cohorts fall sharply once corrected.
  3. Most charge-offs concentrate in the first three to four years after approval, so a cohort
     younger than that carries almost no information about its own terminal loss.
- **Out of scope:** the 504 programme (a different product with a different structure); recoveries
  after charge-off; any causal claim about *why* a cohort performed as it did; and borrower credit
  characteristics, which this file does not carry.

- **Stakeholders:**

| Who | What they decide / need | Format |
|---|---|---|
| Investment committee | The expected-loss number to underwrite with, and whether to proceed | One figure, one table, one page |
| Fund risk analyst | To reproduce and re-run the curve on a later quarter's file | Repository, scripts, data dictionary |
| Site reader (recruiter, hiring analyst) | To follow the reasoning, not just read the result | Case page plus interactive explorer |

- **Metrics:**

| Metric | Formula | Unit | Granularity | Window |
|---|---|---|---|---|
| Age at charge-off | `ChargeOffDate − ApprovalDate` | months | loan | FY1991–FY2026 |
| Cumulative charge-off rate at age *n* | loans in cohort charged off by age *n* ÷ loans in cohort | % (count-weighted) | cohort × age | age 0–120 months |
| Dollar charge-off rate at age *n* | `GrossChargeOffAmount` charged off by age *n* ÷ cohort `GrossApproval` | % (dollar-weighted) | cohort × age | age 0–120 months |
| Observable age of a cohort | `2026-06-30 − cohort start` | months | cohort | — |
| Projected terminal loss | cumulative rate at maximum common age, extended by the completed cohorts' remaining-loss shape | % | cohort | — |

<!-- Denominator note, decided before analysis: CANCLD loans never funded, so they belong in
     neither numerator nor denominator. EXEMPT is a disclosure status, not an outcome; how it is
     treated is a phase 2 decision and lands in the log below once the full files are read. -->

## 2. Prepare

**Status:** closed — 2026-08-31

- **Sources:** ROCCC records in `documentacion/fichas-de-fuente.md`. The FOIA extract scores High on
  all five letters.
  <!-- A second source was added in phase 6: SBA's quarterly performance report, used only by
       verificar.py V1 and V1b and never by the analysis. It is recorded here because sources belong
       in phase 2, not because phase 2 knew about it — at the time its download link was returning
       404 and the reconciliation was declared impossible. See §6. -->
- **Second source (added 2026-09-02):** [SBA quarterly performance report](https://legacy.sba.gov/document/report-small-business-administration-loan-program-performance),
  transcribed to `datos/crudos/sba_desempeno_2016-2025_2025-06-30.csv`. **Reconciliation only** — it
  never enters the analysis, which is what keeps the check independent rather than circular.
- **Data dictionary:** `documentacion/diccionario-de-datos.md`, all 42 columns, built from the
  official `sba_diccionario_oficial.xlsx` kept alongside it.
- **Licence and privacy:** U.S. Government Works, public domain, publication allowed. The file does
  carry borrower name and street address; **no borrower-identifying column is used, published or
  committed** — the analysis needs dates, amounts, term and sector, nothing else.
- **Raw filenames:** `datos/crudos/sba_7a_<period>_2026-06-30.csv`, four files, 901 MB, gitignored.

### What the full integrity test changed

Three things the phase 0 sample got wrong or missed, corrected here rather than left to drift:

1. **`LoanStatus` has five values, not four.** The sample missed `COMMIT` (21,123 rows) because it
   is rare in the opening days of a fiscal year. The official dictionary defines it as
   "Undisbursed" — so, like `CANCLD`, it never put money at risk.
2. **`EXEMPT` is not a hole in the data.** The publisher defines it as a loan **disbursed but not
   yet cancelled, paid in full or charged off**, withheld under FOIA Exemption 4. It means *still
   alive at the cut-off*: the censoring indicator, handed over explicitly. Its share rises from
   0.7% of FY1991 to 76.8% of FY2024, exactly as that definition predicts. This turns the risk
   flagged in phase 0 into the case's best material.
3. **Sector is unavailable before FY2001.** `NaicsCode` is null for 55–57% of disbursed loans
   approved FY1991–FY2000 and ~0% afterwards. The sector cut is therefore restricted to FY2001+;
   the whole-portfolio curve still uses all 35 years.

**Population at risk, fixed before any analysis:** `P I F` + `CHGOFF` + `EXEMPT` = **1,697,542**
disbursed loans, of 1,961,455 approvals. Excluded: `CANCLD` (242,790) and `COMMIT` (21,123).

**Anomalies for phase 3**, all bounded: 3 loans with `GrossApproval` ≤ 0, 1,359 with
`TermInMonths` = 0, 85 with a term above 360 months, 20,155 rows (1.2%) sharing a composite
borrower-date-amount-bank key. Together the amount and term anomalies are 0.09% of the population.

### Exit gate — validated point by point, 2026-08-31

- [x] **Source record complete** — origin, licence, period, granularity, access, all in
      `fichas-de-fuente.md`.
- [x] **ROCCC assessed, failures declared** — five High; the failures are not credibility failures
      but coverage ones (no recoveries, no sector before FY2001, no borrower financials), each
      written down.
- [x] **Potential biases identified in writing** — six, in `fichas-de-fuente.md`. The one that most
      threatens the conclusion is not censoring, which the case handles by design, but **CARES Act
      section 1112 debt relief**, which paid instalments on many 7(a) loans in FY2020–FY2021 and so
      suppressed defaults there by policy rather than by credit quality. Phase 4 must check whether
      those cohorts' early curve is visibly flatter than their neighbours' before saying a word
      about them.
- [x] **Licence, privacy, security, accessibility resolved** — public domain; no borrower-level
      column used or published; raw files gitignored.
- [x] **Data dictionary written** — 42 columns, publisher's definitions, null rates measured over
      the population at risk rather than over all rows.
- [x] **Immutable raw copy saved with the naming convention** —
      `sba_7a_<period>_2026-06-30.csv`, never edited in place.
- [x] **Initial integrity test run and recorded** — schema, partition overlap, null rates, key
      uniqueness, extremes, and `ChargeOffDate` coverage at 99.97% of `CHGOFF` rows with zero
      negative ages.
- [x] **These data can answer the phase 1 question.** `ApprovalDate` and `ChargeOffDate` give age at
      default on 220,630 events across 35 cohorts, and `EXEMPT` gives the surviving population. That
      is everything the maturation curve needs.

<!-- Deliberately NOT recorded as a finding: the pooled age-at-charge-off distribution came out of
     the integrity test (p25 35 months, median 51, p75 75). It hints that hypothesis 3 — "most
     charge-offs land in the first three to four years" — is too early. It is not evidence yet: the
     pooled figure mixes cohorts of different maturity and is itself censored. Phase 4 settles it,
     per cohort, or not at all. -->


## 3. Process

**Status:** closed — 2026-09-01

Every transformation is in `bitacora-limpieza.md`, with its rationale and its row counts. Raw data
was never modified in place: the pipeline reads the four CSVs and writes a new database.

- **Tool:** SQL on DuckDB. One flat table of two million rows that needs filtering, banding and a
  window function — no reshaping, no merging, no iteration, so nothing here needs a dataframe.
  Python is a thin runner that resolves paths, counts rows and asserts.
- **Pipeline:** `consultas/01_construir_base.sql` (faithful typed load) →
  `consultas/02_poblacion.sql` (population and labels), run by `notebooks/procesar.py`.
  `notebooks/descargar.py` reconstructs the raw files and records their sha256.
- **Result:** `datos/limpios/sba-loan-vintages.duckdb`, table `prestamos`, **1,697,539 rows**.
- **Reconciliation:** 1,961,455 − 242,790 cancelled − 21,123 undisbursed − 3 non-positive amounts
  = 1,697,539. Asserted in code; the script stops if it stops balancing.
- **Regression against phase 2:** all six closing numbers reproduced exactly.

### What phase 3 found that phase 2 had missed

**32 charge-offs carry a date later than the file's own cut-off** — 31 on 2026-07-01 and one on
2026-10-22, against an `AsOfDate` of 2026-06-30. The phase 2 integrity test checked for charge-offs
*before* approval and found none; it never checked for charge-offs *after* the cut-off. Caught by a
guard in `procesar.py`, not by inspection, and the guard is now permanent.

They join the 58 charge-offs with no date at all under `fallido_sin_fecha_util`: both count in the
terminal loss rate but neither can be placed on the curve. 90 of 220,688 charge-offs, 0.04%. The
dates were **not** clamped to the cut-off — that would invent an age nobody observed and pile all 32
into one month at the far right of the curve, which is exactly where the case makes its claim.

**Carried into phase 4:** 180 charged-off loans have a charge-off amount of zero. Irrelevant to the
count-weighted rate, which is the primary metric, but V2 (the dollar-weighted cross-check) has to
decide whether those are zero-loss charge-offs or missing amounts before it can be read.

### Exit gates

Both validated point by point at the end of `bitacora-limpieza.md`: the phase 3 gate and the SQL
annex gate. Two entries worth noting because they are easy to fake and were not: the dirty-data
review lists the types that came back **clean**, and the join reconciliation is recorded as **not
applicable** — this pipeline has a single source and no joins at all.

## 4. Analyse

**Status:** closed — 2026-09-01

**Pipeline:** `consultas/03_curvas.sql` (the vintage × age matrix) → `consultas/04_proyeccion.sql`
(development factors and projection), run by `notebooks/analizar.py`; checks in
`notebooks/verificar.py`. Aggregates exported to `salidas/tablas/`, 330 KB in total.

### The finding

> **Corrected for age, the FY2023 vintage is on track for a 12.2% cumulative charge-off rate — the
> worst since 2009 — while its raw rate of 3.5% makes it look like one of the best in the
> programme's history.**

The mechanism in one number: **at 36 months a vintage has realised only 23.5% of the charge-offs it
will eventually suffer.** A three-year-old book shows you less than a quarter of what it will cost.

| Vintage | Raw rate | % of loss realised | Projected terminal | Band (Q1–Q3) |
|---|---|---|---|---|
| FY2019 | 6.69% | 80.5% | 7.62% | 7.42 – 7.93 |
| FY2020 | 4.01% | 67.6% | 5.06% | 4.66 – 5.15 |
| FY2021 | 2.83% | 52.8% | 4.41% | 3.96 – 4.57 |
| FY2022 | 4.08% | 36.7% | 8.81% | 7.83 – 9.26 |
| **FY2023** | **3.46%** | **19.5%** | **12.23%** | **10.28 – 13.35** |
| FY2024 | 1.05% | 5.9% | **not projectable** | — |
| FY2025 | 0.14% | 0.2% | **not projectable** | — |

Every completed vintage from FY2010 to FY2014 landed between 5.99% and 9.20%. FY2023's projection
exceeds all of them, and so does the *bottom* of its band.

**The two youngest vintages are published as a gap, not a number.** FY2025 has realised 0.2% of its
eventual loss, which makes its development factor 606×; multiplying its observed 0.005% by that
would produce a precise-looking 3.0% built on nothing. Publishing that would repeat, in the last
figure of the case, exactly the error the case denounces in the first one. The threshold — a
vintage needs at least 10% of its loss realised to be projectable — was set *after* seeing the
factors explode, and that is stated rather than hidden.

### Secondary finding: the correction changes the level, not the order

Rank correlation between the raw ranking and the equal-age ranking is 0.92–0.96, and the five worst
vintages are the same either way: FY2007, FY2006, FY2008, FY2005, FY2004. This **contradicts what I
wrote down in phase 1**, and it sharpens the case rather than weakening it: censoring does not
scramble the league table, it deflates the recent end of it. The error a fund makes is not ranking
the wrong vintage worst — it is believing a young vintage's *number*.

### Checks — `notebooks/verificar.py`

| # | What it rules out | Result |
|---|---|---|
| **V0** | That the 180 zero-amount charge-offs sit in one place and corrupt the dollar metric | ✅ Spread across 25 vintages, worst is 36 loans in FY1991 (1.7% of its charge-offs). The dollar metric is readable |
| **V1** | That the population was built wrong | ✅ **Reconciled against SBA's own published performance tables** (a different reporting pipeline from the FOIA extract): maximum deviation **4 loans** across FY2016–FY2024, exact in three years. Amounts sit 0.7–1.7% low with a constant sign, explained by the report counting subsequent loan increases. Also re-counted off the raw CSVs, and programme rules hold. *Closed in phase 6 — see below* |
| **V1b** | That "gross, not net" is an unbounded caveat | ✅ SBA's Table 10 puts mature recovery cohorts at **34–39%** of purchased amount. Bounds the gross-to-net gap at roughly a third; does **not** permit a net figure, and none is computed |
| **V2** | That the finding is about loan size rather than vintage | ✅ Spearman 0.939 between count-weighted and dollar-weighted rates at 60 months |
| **V3** | That FY2020–21 look good on credit quality | ⚠️ **Confirmed the bias.** At 36 months FY2020 (0.85%) and FY2021 (0.77%) sit at roughly half of FY2018 (1.72%), FY2019 (1.58%) and FY2022 (1.98%). CARES Act §1112 paid instalments on many 7(a) loans; those two vintages are policy-flattered and must not be read as good underwriting |
| **V4** | That the pattern is a change of mix, not of vintage | ✅ Direct standardisation on a fixed term × size mix: Spearman 0.972 against the unadjusted rate. The reordering is not composition |
| **V5** | That the conclusion depends on the age cut chosen | ✅ Rank correlations 0.92–0.96 across 36 / 60 / 84 months; the worst five are stable at 60 and 84 |
| **V6** | That the curve itself is a bug | ✅ 140 cells recomputed by direct counting instead of a windowed cumulative sum: 0 discrepancies, maximum difference 0.0 pp |

### The three hypotheses, adjudicated

Written 2026-08-31, before any analysis.

1. **"Vintages originated just before a shock lose more than those during or just after."**
   **Supported for the financial crisis** — FY2006 32.1% and FY2007 36.8%, against FY2009 14.7% and
   FY2010 9.2%. **Cannot be tested for covid**: FY2020–21 are policy-suppressed (V3), so their
   flatness is not evidence of anything about credit.
2. **"The raw ranking gives a different ordering than the equal-age ranking."** **Contradicted.**
   The ordering barely moves (Spearman 0.92–0.96, same worst five). What the correction changes is
   the level of the young vintages, not their rank.
3. **"Most charge-offs land in the first three to four years."** **Contradicted.** In uncensored
   vintages the median charge-off arrives at **58 months** and only 23.5% of eventual losses have
   occurred by 36 months; half the loss is still ahead at five years. This is why the horizon had
   to be set at 138 months rather than the 84 or 120 the plan expected.

### Limitations this analysis cannot argue away

- ~~**No external reconciliation.**~~ **Closed in phase 6.** The archive was not missing: the
  document page links it with a *relative* URL that only resolves against `legacy.sba.gov`, and the
  first attempt resolved it against `www.sba.gov` and took the 404 at face value. The reconciliation
  now passes with a maximum deviation of 4 loans across nine fiscal years. See §6.
- **Nothing here is causal.** The case describes how vintages behave. FY2007 is not bad "because of
  the crisis": that is context, not a finding, and the data cannot separate it from anything else
  that changed in 2007.
- **Gross, not net** — but no longer unbounded. No recoveries are in the FOIA extract, so every rate here is gross. SBA's published recovery tables put mature cohorts at 34–39% recovered, which bounds the overstatement at roughly a third. That is an order of magnitude, not a conversion: recovery is a share of the *purchased* amount by *purchase* year, and these rates are a share of the *approved* amount by *approval* year.
- **Partial government guarantee.** The shape of the maturation curve transfers to private credit;
  the level does not.
- **The projection assumes the past shape holds.** Development factors come from FY1991–FY2014. If
  the loss timing of recent vintages differs structurally from that history, the projection is
  wrong in a way this method cannot detect.

### Exit gate — phase 4

- [x] **Descriptive statistics complete and reviewed** — 35 vintages, 1,674,296 loans in the
      comparable population, 220,688 charge-offs, 13.18% overall; age at charge-off p25/median/p75
      = 39 / 58 / 81 months on uncensored vintages.
- [x] **Every phase 1 question answered by a concrete calculation** — the maturation curve answers
      how the rate evolves with age; the projection answers what terminal loss the immature
      vintages imply.
- [x] **All calculations documented and reproducible** — `consultas/03_curvas.sql` and
      `04_proyeccion.sql`, run end to end by `analizar.py` from the raw files.
- [x] **Every finding passed a sanity test and a recalculation by another route** — V1 and V6.
- [x] **Effects quantified, not just directional** — 3.46% → 12.23% with a 10.28–13.35 band; 23.5%
      of loss realised at 36 months.
- [x] **Alternative interpretations considered and ruled out with evidence** — V4 (mix, Spearman
      0.972), V2 (loan size, 0.939), V5 (choice of cut, 0.92–0.96). One was **not** ruled out: V3
      confirmed that FY2020–21 are policy-flattered, and they are labelled instead of used.
- [x] **What the data cannot answer is written as a limitation** — five, above, including the
      external reconciliation that could not be completed.
- [x] **No causal claim resting on correlation alone** — the case describes vintage behaviour and
      explicitly declines to explain it.
- [x] **Each finding written as a sentence with a number that works as a headline** — the block
      quote above, and the secondary finding on level-versus-order.

<!-- `problemType` confirmed as `predict`: the projection is the deliverable, not a description.
     The phase 1 note said to relabel as `find patterns` if the analysis turned out descriptive —
     it did not. -->

<!-- For phase 5, decided here so it is not rediscovered: the sector cut exports only at 36/60/84
     months and goes to a static figure. 21 sectors in an interactive explorer would be 21 curves
     nobody compares. The explorer carries global + term + size only. -->

<!-- Carried to phase 6: the underwriting number the committee needs is dollar-weighted, and this
     phase deliberately led with counts. `curvas.tasa_acum_usd_pct` already holds it. -->


## 5. Share

**Status:** closed — 2026-09-02

Four figures in `salidas/graficos/`, built by `notebooks/graficos.py` on top of `estilo.py` so the
three cases read as one body of work. Presentation script and Q&A in
`entregables/guion-presentacion.md`. The explorer's data file —
`salidas/tablas/explorador-anadas.json`, 78 KB — is built here and consumed in phase 7.

### The case's own palette

Crimson `#a8203a` and cyan `#0e8ea8`, against case 1's blue-and-orange and case 2's
green-and-violet. Not picked by eye: the hues the earlier cases already occupy were measured in
OKLCh (38°, 152°, 255°, 303°) and this case takes two genuinely free ones, 17° and 213°. The pair
passes the `dataviz` validator on all five checks — **ΔE 16.5 deutan and 32.5 tritan against a
target of 8** — and the sequential ramp passes lightness monotonicity. Composition is untouched:
colour is what a case may change, layout is what makes the author recognisable.

An earlier teal candidate was discarded because it failed the chroma floor (0.09 against 0.10) at
every lightness inside the band — teal simply cannot carry enough chroma there. That is the kind of
thing eyeballing does not catch.

### The four figures

No shape is reused, within the case or against the other two — case 1 spent dumbbell, matrix table,
lollipop and grouped bars; case 2 spent concentration curve, lines, diverging bars, slope and 100%
stacked bars.

| # | File | Headline | Form |
|---|---|---|---|
| 1 | `01_lo_que_falta_por_llegar.png` | Corrected for age, the 2023 vintage is on track for 12.2% losses — the worst since 2009 | Absolute stacked columns + IQR whisker |
| 2 | `02_a_los_tres_anos.png` | At three years a vintage has shown only a quarter of the losses it will suffer | Step curve with area |
| 3 | `03_nivel_no_orden.png` | Correcting for age changes the level, not the league table | Bump chart |
| 4 | `04_artefacto_de_politica.png` | FY2020 and FY2021 default at half the rate of their neighbours — because the government was paying | Small multiples, identical axes |

### Alt text — written here, with the figure in front of me

Copy these verbatim into the site's front-matter and body in phase 7.

**Figure 1.** *Stacked column chart of cumulative charge-off rates for the FY2015 to FY2025
vintages. Each column splits into the loss already recorded and the loss the projection says is
still to come. FY2023 reaches 12.2%, far above the 6.0–9.2% band where FY2010 to FY2014 landed,
even though only 3.5% has been recorded so far. FY2024 and FY2025 carry no projection and are
labelled "not projectable"; their raw rates are 1.05% and 0.14%.*

**Figure 2.** *Step curve showing the share of a vintage's eventual charge-offs that has already
occurred, by months since approval, measured on the 24 completed vintages. It reaches 23.5% at 36
months, 56.6% at 60 months and 97.0% at 120 months, so three years after approval three quarters of
the loss is still ahead.*

**Figure 3.** *Bump chart of the rank of 28 vintages by charge-off rate under four readings: the raw
rate and the rate at 36, 60 and 84 months. Most lines stay flat. The five worst — 2007, 2006, 2008,
2005 and 2004 — hold the top five places under every reading, with only minor swaps between them.*

**Figure 4.** *Five small panels with identical axes, one per vintage from FY2018 to FY2022, showing
the cumulative charge-off rate over the first 45 months. FY2018, FY2019 and FY2022 reach 2.8%, 2.5%
and 3.2%. FY2020 and FY2021, labelled "CARES Act relief", reach only 1.5% and 1.4% — roughly half,
at exactly the same age.*

### Exit gates — phase 5 and the visualisation annex

Both validated point by point. The ones that took real work:

- **The three-part filter on every figure** — practical question, what the data say, what the visual
  says. Figure 1 failed it on the first pass: its lower block plotted the rate at the reading age
  while the subtitle promised "loss already recorded". Those are different numbers — FY2024 showed
  0.50% instead of its true 1.05% — so the figure was rebuilt on the raw rate rather than the
  caption being softened.
- **Zero baseline on every bar.** Figure 1 is columns; truncating would exaggerate the very
  comparison the headline rests on.
- **Never colour alone.** Figure 4's two highlighted panels are also titled "CARES Act relief";
  figure 3's five highlighted lines are labelled at both ends.
- **Open them and look.** That is how the `2007.0` float labels in figure 3, the two misaligned
  "not projectable" labels in figure 1 and the panel titles colliding with the period line in
  figure 4 were caught. The validator checks colour, not layout.
- **Only the figures that carry the argument.** A fifth on the term or sector cut was planned and
  dropped: it did not earn its place next to these four.

## 6. Act

**Status:** closed — 2026-09-02

Deliverables: `entregables/recomendaciones.md`, `resumen_ejecutivo.md` and its `.docx` (generated by
`notebooks/build_docx.py`), `portafolio-indice.md`, and the public `README.md`. The technical report
follows publication, as it did in the football case.

### The number that goes into the model, and why it needed its own projection

Phase 4 decided counts would carry the mechanism and **dollars would supply the figure**. Producing
that figure turned out to need work rather than a division.

The dollar rate is not a fixed fraction of the count rate — **the ratio falls with age**: 0.456 for
FY2012 read at 138 months, 0.343 for FY2018 at 93, 0.226 for FY2023 at 33. The two curves mature at
different speeds, because loans that fail early have amortised little and large loans — which
dominate dollars and not counts — fail less and later. Applying the count-based development factors
to a dollar rate would have invented a number. `consultas/05_proyeccion_usd.sql` derives its own
factors from the same 24 completed vintages, under the same projectability threshold.

**FY2023 projects to 4.24 cents lost per dollar approved** (band 3.28–6.18) against 0.75 recorded.
Seventeen completed vintages are worse, the most recent being FY2010 (4.47) — so on the dollar
measure it is the worst since FY2010, where the count measure says the worst since FY2009. Both are
stated rather than the more dramatic one being chosen.

**The metric carries its label everywhere it is quoted.** `tasa_acum_usd_pct` is charge-off balance
÷ **original approved amount**: cents lost per dollar approved, with amortisation already inside it.
It is not loss on outstanding balance, not severity or LGD, and not net of recoveries. A reader who
files "4.24%" next to an LGD draws the wrong conclusion, so the definition sits in the recommendation
card itself, not in a footnote.

**Acceptance check, in code:** for every *completed* vintage the projection must return that
vintage's own observed rate at H. `analizar.py` raises if it does not, for both the count and the
dollar tables. If the factors were built wrongly, everything downstream would be noise shaped like a
figure.

### The three recommendations

Priority is impact against effort.

| # | Recommendation | Effort |
|---|---|---|
| **R1** | Price the book off a maturation curve, not off its observed rate | Low |
| **R2** | Keep FY2020–21 out of any calibration sample; use FY2016–19 | Low |
| **R3** | Underwrite the short-term, small-ticket segment on its own terms | Medium |

R3 answers the half of the phase 1 decision that asked *which origination mix to avoid*: at 60
months, loans of ≤7 years charge off at 5.67% against 0.39% for loans over 20 years — fourteen
times — and the smallest size quartile at 6.01% against 1.34% for the largest.

**Its confound is written into the card, not hidden.** Term proxies product and collateral: 20-year
7(a) loans are real-estate secured, short ones are working capital. The finding says *where the loss
sits*, not that shortening a term causes default. Rewriting short loans as long ones would import a
different product, not a lower rate. Without that paragraph R3 is a recommendation a risk analyst
dismantles with the first question.

**Sector produced no fourth recommendation.** Among sectors with enough volume the 60-month rate runs
4.28% to 4.57% — it does not separate, and it went to "deliberately not recommendations" rather than
padding the list.

### Findings raised to insight

The gate asks for this explicitly and it is where portfolio cases stall. The one that mattered most
is the secondary finding: the correction changes the level and not the order, so the insight is not
"rank vintages differently" — it is **the error a fund makes is not ranking the wrong vintage worst,
it is believing a young vintage's number.** That is what changes a behaviour.

### The external reconciliation, closed

It had been carried since phase 2 as the case's weakest point: the framework asks for a total checked
against an independent source, and SBA's published performance tables — the obvious check — sat
behind a link that returned 404.

**The archive was never missing.** The document page publishes it with a *relative* URL,
`/sites/default/files/2025-09/WebsiteReports_FY25Q3.zip`. Resolved against `www.sba.gov` it 404s;
it resolves only against `legacy.sba.gov`, where the page itself lives after a redirect. The first
attempt used the obvious host, got a 404, and recorded the check as impossible. It was not
impossible — it was one hostname away.

The reconciliation now **passes**, and against a genuinely independent pipeline: the performance
report is the programme's own reporting, not the FOIA disclosure extract.

| | Result |
|---|---|
| Approved loan count, FY2016–FY2024 | Maximum deviation **4 loans** against cohorts of 42,000–70,000. Exact in three of nine years |
| Gross approval amount | Systematically **0.7–1.7% low, always in the same direction** — the report counts subsequent loan increases, which the FOIA extract does not carry. A constant, explained sign is stronger evidence than a smaller deviation that wanders |
| FY2025 | Excluded: the report is cut at 2025-06-30 and our extract runs to 2026-06-30 |

It also bounds a second limitation. Table 10 of the same report puts mature recovery cohorts at
**34–39% recovered**, so the case's gross figures overstate a fund's eventual loss by roughly a
third. **No net figure is computed**, and that restraint is deliberate: recovery is a share of the
*purchased* amount indexed by *purchase* year, while these rates are a share of the *approved*
amount indexed by *approval* year. Different numerators on different axes. The bound is honest; a
division would not be.

`verificar.py` now runs this as V1 and V1b. The transcribed figures live in
`datos/crudos/sba_desempeno_2016-2025_2025-06-30.csv` — un-ignored on purpose, thirty numbers taken
from eleven PDFs that are linked rather than redistributed.

### Exit gate — phase 6

- [x] **Every finding raised to insight and to recommendation** — three cards, plus the level-vs-order
      insight above.
- [x] **Each recommendation has action, evidence, impact, metric, risk and effort** — no exceptions;
      R3's risk section is the longest of the three on purpose.
- [x] **Prioritised by impact against effort** — R1, R2, R3, with effort stated per card.
- [x] **Limitations and additional data documented** — "deliberately not recommendations" and "what
      would strengthen this materially" in `recomendaciones.md`.
- [x] **Public `README.md` complete, with the figures visible** — all four, with the alt text written
      in phase 5.
- [x] **No sensitive data or licence breach** — public domain; no borrower-identifying column is ever
      loaded, let alone published; the 901 MB of raw files stay out of the repository.
- [x] **Reproducible from raw by a third party** — `descargar.py` rebuilds the raw files and the
      README warns that SBA overwrites the same URLs quarterly, so the sha256 are what tell you
      whether you rebuilt the same thing.
- [x] **Written what this case demonstrates against the others** — `entregables/portafolio-indice.md`.
- [ ] **Presentation rehearsed at 30 and 3 minutes** — ⚠️ **not done.** The 3-minute script exists
      with its Q&A; the 30-minute version has not been written, and rehearsing is Juanes's to do, not
      the analysis's. Recorded as open rather than ticked, as the football case did.

## 7. Portfolio

**Status:** open

- Hand over to the site: front-matter Markdown (template 7 of `plantillas.md`) plus figures and
  aggregate tables. Only that crosses; this file stays here and is linked.
- If an aggregate the site needs weighs megabytes, the aggregation is incomplete — go back to
  phase 4 and summarise further.

## Decision log

| Date | Decision | Reason | Alternative discarded |
|---|---|---|---|
| 2026-08-31 | A financial domain for case 3 | The first two cases are games and football; a recruiter in credit or fintech has to do the translation unaided. This also draws on domain knowledge I actually have. | Retail / consumer, which was the first choice before the profile was on the table |
| 2026-08-31 | SBA 7(a) FOIA as the source | Public domain, no registration, loan-level since 1991, published by the guarantor itself — ROCCC passes on all five | **Freddie Mac**: requires registration and its licence restricts use to internal purposes, which collides with publishing in a public repository. **Lending Club**: no longer distributed from origin, only Kaggle copies, which fail the O of ROCCC |
| 2026-08-31 | 7(a) only, not 504 | 504 is a different product (real estate and equipment, CDC structure); mixing them would make one cohort curve mean two things at once | Combining both for volume |
| 2026-08-31 | `predict` as the problem type | Extrapolating an immature cohort's terminal loss from the completed ones is a projection, and it fills an empty cell honestly | `find patterns`, which would have been a third repeat |
| 2026-08-31 | Hypothesis recorded before analysis | The same discipline as the football case: without a dated line, "the data contradicted me" cannot be told apart from a story rewritten afterwards | Writing it up after seeing the result |
| 2026-09-01 | Charge-offs dated after the cut-off keep their loan but lose their date | Clamping them to the cut-off would invent an unobserved age and pile 32 loans into one month at the far right of the curve, where the case makes its claim | Clamping the date; dropping the 32 loans, which would have discarded real defaults |
| 2026-09-01 | Duplicates not removed | The file has no loan number, and the evidence says the repeats are distinct loans: 2,147 keys differ in term, 235 in outcome. Only 519 rows are fully identical, 0.03%, and their worst-case effect on the rate is bounded and printed on every run | Deduplicating on a composite key, which would have deleted real loans to tidy an artefact |
| 2026-09-01 | Implausible terms labelled `unknown`, loans kept | They are real disbursed loans and belong in the overall curve; term is needed for one cut only | Dropping 1,442 loans, removing real defaults to tidy a cut they do not take part in |
| 2026-09-01 | Terminal horizon H = 138 months, derived by rule | The rule (the age at which completed vintages have realised 95% of their charge-offs) was written before the number was computed. It came out far longer than the 84 or 120 the plan expected, which is itself a finding | Picking a round 120 because it looks tidy, which would have cut the horizon 6 pp of realisation short |
| 2026-09-01 | FY2024 and FY2025 published as a gap, not a projection | Their development factors are 17x and 606x: multiplying a near-zero observed rate produces a precise-looking number built on nothing. The threshold (10% of loss realised) was set after seeing the factors, and that is stated | Publishing the numbers with a wide band, which would have repeated the case's own headline error in its last figure |
| 2026-09-01 | FY2020-21 flagged as policy-flattered, not good vintages | V3: at 36 months they sit at half of every neighbour. CARES Act 1112 paid instalments; reading them as good underwriting would be wrong | Treating them as evidence for the pre-shock hypothesis, which is what they superficially look like |
| 2026-09-01 | Count-weighted rate leads, dollar-weighted verifies | The count metric is unmoved by the 180 zero-amount charge-offs and by the absence of recoveries; the dollar figure supplies the underwriting number in phase 6 | Leading with dollars, which would have put the case's weakest data in its strongest sentence |
| 2026-09-02 | Crimson + cyan as the case palette | The hues the other two cases occupy were measured in OKLCh (38, 152, 255, 303) and these take two free ones. Validated: 5/5 checks, deutan dE 16.5 against a target of 8 | A teal accent, dropped because it fails the chroma floor at every lightness in the band |
| 2026-09-02 | Figure 1 rebuilt on the raw rate, not the rate at reading age | The subtitle promises "loss already recorded" and the reading-age rate is a different number - FY2024 showed 0.50% instead of 1.05%. The three-part filter caught it | Softening the caption to match the chart, which would have made the figure technically true and practically misleading |
| 2026-09-02 | The panel grid lives in graficos.py, not estilo.py | estilo.py is shared by the three cases and is not forked for one case's need. If a second case wants small multiples, it gets promoted - to the template, not to a copy | Adding it to this case's estilo.py, which is how two copies start diverging |
| 2026-09-02 | The dollar projection gets its own development factors | The dollar/count ratio falls with age (0.456 at 138 months, 0.226 at 33), so the two curves mature at different speeds. Reusing the count factors would have produced an invented number | Multiplying the dollar rate by the count factors, which is the obvious shortcut and is wrong |
| 2026-09-02 | The dollar metric is labelled wherever it is quoted | It is charge-off balance over ORIGINAL approved amount, so amortisation is inside it. It is not LGD, not loss on outstanding balance, not net. A committee that files 4.24% next to an LGD draws the wrong conclusion | Quoting the number bare and putting the definition in a footnote |
| 2026-09-02 | R3 ships with its confound in the card | Term proxies product and collateral: 20-year loans are real-estate secured, short ones are working capital. The finding says where the loss sits, not that tenor causes it | Presenting the 14x spread as a lever, which a risk analyst dismantles with the first question |
| 2026-09-02 | Sector produces no recommendation | 4.28% to 4.57% at 60 months among sectors with volume: it does not separate | A fourth card, which would have padded the list with noise |
| 2026-09-02 | Deterministic tie-break added to the size-quartile window | Rebuilding the database changed half the rows of curva_por_importe.csv: approved amounts cluster on round numbers and ntile split the ties by arrival order. Caught by rebuilding twice and diffing the sha256 of every export, not by reading the code | Leaving it, which would have shipped a README promising reproducibility next to a pipeline that did not deliver it |
| 2026-09-02 | The external reconciliation was closed, not written off | The archive was never missing: the page links it with a relative URL that only resolves against legacy.sba.gov, and the first attempt used www.sba.gov and took the 404 at face value. It reconciles to within 4 loans across nine fiscal years | Leaving it as a declared limitation, which is honest but was hiding a one-hostname mistake |
| 2026-09-02 | The gross-to-net gap is bounded, not converted | SBA's Table 10 puts mature recovery cohorts at 34-39%. But recovery is a share of the PURCHASED amount by PURCHASE year, and the case's rates are on the APPROVED amount by APPROVAL year — different numerators on different axes | Dividing one by the other to publish a net figure, which would have looked more useful and meant nothing |
