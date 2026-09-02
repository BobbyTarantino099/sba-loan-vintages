<!-- Phase 2 deliverable: one record per source. A source that fails ROCCC is not
     automatically discarded, but the failure must be declared and its effect on the
     conclusion assessed. -->

# Data source records — SBA 7(a) loan vintages

## Source 1: SBA 7(a) FOIA loan-level extract

- **Link:** https://data.sba.gov/dataset/7a-504-foia
- **Publisher:** U.S. Small Business Administration (SBA), the agency that guarantees these loans.
- **Licence:** U.S. Government Works — public domain. Republication of the data and of any derived
  analysis is permitted.
- **Period covered:** FY1991 – FY2026, i.e. approvals from 1990-10-01 to 2026-06-30.
- **Volume:** 1,961,455 rows × 42 columns, across four CSV files (901 MB).
- **Downloaded on:** 2026-08-31. Publisher's cut-off (`AsOfDate`): 2026-06-30, identical in all
  four files.
- **Saved as:** `datos/crudos/sba_7a_1991-1999_2026-06-30.csv` and its three siblings
  (`2000-2009`, `2010-2019`, `2020-2026`).

### ROCCC

| Letter | Assessment | Detail |
|---|---|---|
| **R**eliable | High | The guarantor's own loan book, not a survey or an estimate. Status, charge-off date and charge-off amount come from SBA's servicing records. |
| **O**riginal | High | First-party, downloaded from the agency's own open-data portal. No aggregator in between. The widely used Kaggle derivative of this data is a copy of this file, not the other way round. |
| **C**omprehensive | High for the question asked | Carries approval date, charge-off date, charge-off amount, term, size, sector, state and originating bank — everything the maturation curve needs. Two structural gaps, both stated below. |
| **C**urrent | High | Refreshed quarterly; this extract is two months old at time of use, and the question is about 35-year-old behaviour, so the lag is immaterial. |
| **C**ited | High | Published with an official data dictionary (`sba_diccionario_oficial.xlsx`, kept in this folder), a declared cut-off date and an explicit licence. |

### What it can and cannot answer

- **Can:** how a cohort of loans defaults as it ages, because every disbursed loan carries either a
  terminal outcome (paid in full, charged off) or an explicit still-alive marker, plus the dates
  needed to place the event on a timeline.
- **Cannot:**
  - **Net loss.** No recoveries are recorded after charge-off. Every rate here is gross.
  - **Unguaranteed private credit levels.** These loans carry a partial SBA guarantee, which changes
    both lender incentives and borrower access. The *shape* of the maturation curve transfers to
    private credit; the *level* does not, and the case must say so.
  - **Sector before FY2001.** `NaicsCode` is null for 55–57% of disbursed loans approved in FY1991–
    FY2000 and for ~0% from FY2001 onward — SBA adopted NAICS at that boundary. Any cut by sector is
    therefore restricted to FY2001+; the whole-portfolio curve still uses all 35 years.
  - **Why.** No borrower financials, no credit score, no interest-rate history beyond the initial
    rate. The case describes behaviour; it does not attribute cause.
  - **Drawn amounts over time.** The file holds approvals, not outstanding balances, so exposure is
    measured at origination and never amortised.

### The `EXEMPT` status — read this before touching the denominator

The single most consequential field in this dataset, and the easiest to get wrong. The official
dictionary defines it as:

> `EXEMPT` = the status of loans that have been **disbursed** but have **not been cancelled, paid in
> full, or charged off** — exempt from disclosure under FOIA Exemption 4.

So `EXEMPT` does not mean "unknown" or "missing". It means **still outstanding as of the cut-off**:
the loan is alive and has not yet experienced the event. It is the censoring indicator, handed over
explicitly by the publisher.

Its share rises steeply with cohort age, exactly as that definition predicts — 0.7% of FY1991,
0.2% of FY2000, 27.1% of FY2019, 76.8% of FY2024:

| Approval FY | EXEMPT % | CHGOFF % | P I F % |
|---|---|---|---|
| 1991 | 0.7 | 11.2 | 76.6 |
| 2000 | 0.2 | 12.7 | 73.1 |
| 2007 | 0.6 | 32.6 | 55.5 |
| 2019 | 27.1 | 5.9 | 55.0 |
| 2024 | 76.8 | 0.9 | 7.8 |

An analyst who drops `EXEMPT` rows as unusable deletes almost the entire recent population and
concludes that recent cohorts barely default. An analyst who keeps them in the denominator without
adjusting for age concludes the same thing for the opposite reason. Both are the error this case
exists to demonstrate.

**Denominator decided in phase 2, before any analysis:** the population at risk is the **disbursed**
loans — `P I F` + `CHGOFF` + `EXEMPT` = 1,697,542. Excluded: `CANCLD` (242,790, approved but
cancelled) and `COMMIT` (21,123, "Undisbursed" per the official dictionary). Neither ever put money
at risk, so neither belongs in numerator or denominator.

### Initial integrity test — 2026-08-31, on the complete files

| Check | Result |
|---|---|
| Schema consistency across the four files | ✅ Identical 42-column header; no reconciliation needed |
| Partition overlap | ✅ Fiscal years are disjoint between files; no double counting |
| `AsOfDate` | ✅ Single value, 2026-06-30, in all four files |
| `ApprovalDate` / `ApprovalFY` nulls | ✅ Zero |
| Date format | ✅ ISO `YYYY-MM-DD` throughout; no mixed formats |
| `ChargeOffDate` coverage on `CHGOFF` | ✅ 220,630 of 220,688 — 99.97% |
| `ChargeOffDate` on non-`CHGOFF` rows | ✅ Zero; status and date never contradict each other |
| Negative age at charge-off | ✅ Zero rows charged off before approval |
| Charge-off date after the cut-off | ⚠️ **32 rows** — 31 on 2026-07-01, one on 2026-10-22, against an `AsOfDate` of 2026-06-30. Missed by this test and caught in phase 3 by an assertion in `procesar.py`; the file contradicts its own cut-off |
| Charge-off amount of zero on a charge-off | ⚠️ 180 rows — carried to phase 4, where the dollar-weighted cross-check has to decide what they are |
| `GrossApproval` ≤ 0 | ⚠️ 3 rows (one negative, at −$120,000) |
| `TermInMonths` = 0 | ⚠️ 1,359 rows |
| `TermInMonths` > 360 | ⚠️ 85 rows, up to 569 months |
| `NaicsCode` null | ⚠️ 176,915 disbursed rows, all but ~0.2% of them approved before FY2001 |
| Duplicate composite key (borrower + date + amount + bank) | ⚠️ 3,581 keys covering 7,393 rows (0.4%) in the population at risk; 9,524 keys / 20,155 rows if cancelled loans are counted too. Only 403 groups are identical across all 42 columns |

Every ⚠️ row is phase 3 work, not a blocker: the amount and term anomalies together are 0.09% of the
population at risk, and the NAICS gap, the duplicates and the two charge-off anomalies are all
bounded and understood. Each has a documented decision in `bitacora-limpieza.md`.

> Counts in this table are measured over the **population at risk** (1,697,542), which is why the
> duplicate figures are smaller than a count over all 1,961,455 approvals would give: cancelled
> loans repeat more than disbursed ones.


### File fingerprints — verify before trusting a re-download

The SBA overwrites the same URLs every quarter, so a file downloaded later will **not** be the one
this case analysed. `python notebooks/descargar.py --solo-hashes` re-computes these without
downloading anything.

| File | Bytes | sha256 |
|---|---|---|
| `sba_7a_1991-1999_2026-06-30.csv` | 146,416,885 | `05040efc4a43224a02460d606ea744579a54b650bdb99663a833ed0b31936213` |
| `sba_7a_2000-2009_2026-06-30.csv` | 318,425,094 | `66674e18a700fbba0378c25118c291ac2759784a550c643cab5747eced763d6a` |
| `sba_7a_2010-2019_2026-06-30.csv` | 255,101,999 | `01a3e2c7988a6f4052e53f218a309feb2ec2fe42887bebdc0fa94ac8b1024ade` |
| `sba_7a_2020-2026_2026-06-30.csv` | 181,130,871 | `6c1e9132b5141a19f82bdc8ccafb86c9a01662461cad41ddb36a3cf409d8a4fe` |
| `sba_diccionario_oficial.xlsx` | 24,529 | `777ba97a6f92e325f79905610816cb59d41f1971cd964c54dc30ef02730a3941` |

### Potential biases, written down before the analysis

Six, in rough order of how much they could bend the conclusion.

1. **Right-censoring.** The one the case is about. Every cohort is observed only up to 2026-06-30,
   so recent cohorts have had less time to default. Addressed head-on by comparing cohorts at equal
   age rather than at a common observation date.
2. **Adverse selection into the programme.** A 7(a) loan exists because the borrower could not get
   conventional credit on reasonable terms — that is the programme's stated purpose. This book is
   therefore selected *towards* weaker credit relative to ordinary bank lending. It shifts the level
   of the curve, not its shape.
3. **CARES Act debt relief, FY2020–FY2021.** Under section 1112, SBA paid principal and interest on
   many 7(a) loans for a period during the pandemic. Defaults that would otherwise have occurred in
   those cohorts were suppressed or deferred by policy, not by credit quality. The FY2020–FY2021
   cohorts must be read with this in mind, and the case should check whether their early curve is
   visibly flatter than their neighbours'.
4. **Guarantee moral hazard.** The lender bears only the unguaranteed slice, which plausibly makes
   it both more willing to originate and slower to work a loan out. Charge-off *timing* in this book
   may therefore be later than an unguaranteed lender's would be.
5. **`BankName` is the current holder, not the originator.** The publisher's own definition says
   "currently assigned to". Any cut by lender measures who holds the loan today, which is not the
   same as who underwrote it — so a lender-level claim is not safely available from this file.
6. **Cancellations may not be random.** 12.4% of approvals were cancelled and are excluded from the
   population at risk. If cancellation correlates with borrower quality, the surviving book is
   selected on something invisible here.

### Privacy check

- [x] No personally identifiable data **is used**. The file does carry `BorrName`, `BorrStreet`,
      `BorrCity` and `BorrZip` for what are largely small businesses; none of these columns enters
      the analysis, the aggregates or the site, and the raw files are gitignored.
- [x] The licence permits publishing the derived analysis (U.S. Government Works, public domain).
