<!-- Phase 2 deliverable. Mark with ★ the columns the analysis actually uses: it is what
     lets a reader tell the working set apart from the noise in a 40-column table. -->

# Data dictionary — SBA 7(a) FOIA loan-level extract

**Files:** `datos/crudos/sba_7a_{1991-1999,2000-2009,2010-2019,2020-2026}_2026-06-30.csv`
— 1,961,455 rows × 42 columns in total.
**Unit of observation:** 1 row = one SBA 7(a) loan **approval**, not a disbursement and not a
borrower. The same business can appear many times.

Definitions are the publisher's own, from `sba_diccionario_oficial.xlsx` (kept in this folder),
abbreviated where they ran long. Null percentages are measured over the **1,697,542 disbursed
loans** (`P I F` + `CHGOFF` + `EXEMPT`) — the population at risk defined in
`fichas-de-fuente.md` — not over all 1,961,455 rows, because that is the population the analysis
actually runs on.

★ = column used by the analysis.

| Column | Type | Unit | Allowed values | Meaning | Nulls |
|---|---|---|---|---|---|
| `AsOfDate` ★ | date | — | 2026-06-30 | Date the data was recorded. Single-valued: the observation cut-off, and therefore the point at which every live loan is censored | 0.0% |
| `Program` | categorical | — | `7A` | 7(a) or 504. Constant here — the 504 files were deliberately not downloaded | 0.0% |
| `LocationID` | text | — | — | SBA's unique lender ID code | 0.1% |
| `BorrName` | text | — | — | Borrower name. **Not used, not published** | 0.0% |
| `BorrStreet` | text | — | — | Borrower street address. **Not used, not published** | 0.0% |
| `BorrCity` | text | — | — | Borrower city. **Not used, not published** | 0.0% |
| `BorrState` | text | — | 2-letter code | Borrower state | 0.0% |
| `BorrZip` | text | — | — | Borrower ZIP code. **Not used, not published** | 0.0% |
| `BankName` ★ | text | — | — | Bank the loan is *currently* assigned to — note "currently": a sold or transferred loan carries the new holder, not the originator | 0.1% |
| `BankFDICNumber` | text | — | — | FDIC certificate ID of the lender | 9.5% |
| `BankNCUANumber` | text | — | — | NCUA charter number of the lender | 97.9% |
| `BankStreet` / `BankCity` / `BankState` / `BankZip` | text | — | — | Bank address | 0.1% |
| `GrossApproval` ★ | decimal | USD | 3 rows ≤ 0; max 5,000,000 | Total loan amount. Nominal dollars at approval — never inflation-adjusted in the raw file | 0.0% |
| `SBAGuaranteedApproval` ★ | decimal | USD | — | Amount of SBA's guaranty. Its ratio to `GrossApproval` is what makes this book unlike unguaranteed private credit | 0.0% |
| `ApprovalDate` ★ | date | — | 1990-10-01 → 2026-06-30 | Date the loan was approved. **The origin of the cohort clock** | 0.0% |
| `ApprovalFY` ★ | integer | fiscal year | 1991 → 2026 | Fiscal year of approval; US federal FY starts 1 October. **The cohort key** | 0.0% |
| `FirstDisbursementDate` | date | — | — | Date of first disbursement, where available | 0.1% |
| `ProcessingMethod` | categorical | — | see SOP 50 10 5 | Processing method the loan was approved under | 0.0% |
| `InitialInterestRate` | decimal | % | — | Base rate plus spread at approval. Half the book is missing it, so it cannot carry a pricing cut | 51.2% |
| `FixedorVariableInterestInd` | categorical | — | F / V | Fixed or variable rate indicator | 51.2% |
| `TermInMonths` ★ | integer | months | 1,359 rows = 0; 85 rows > 360; max 847 | Contracted loan term. One of the three cuts of the analysis | 0.0% |
| `NaicsCode` ★ | text | — | 6-digit NAICS | Sector code. **Absent for 55–57% of pre-FY2001 approvals and ~0% after** — the sector cut is restricted to FY2001+ | 10.4% |
| `NaicsDescription` ★ | text | — | — | Label for the code above | 10.4% |
| `FranchiseCode` / `FranchiseName` | text | — | — | Franchise identity, where applicable | 92.1% |
| `ProjectCounty` | text | — | — | County where the project occurs | 0.0% |
| `ProjectState` ★ | text | — | 2-letter code | State where the project occurs. Preferred over `BorrState` for geography: it is where the money went | 0.0% |
| `SBADistrictOffice` | text | — | — | SBA district office | 0.0% |
| `CongressionalDistrict` | text | — | — | Congressional district of the project | 0.2% |
| `BusinessType` | categorical | — | Individual / Partnership / Corporation | Borrower legal form | 0.2% |
| `BusinessAge` | categorical | — | — | Categorical age of the business at approval. Low null rate, but the categories are lender-reported and unaudited — verify before leaning on it | 0.1% |
| `LoanStatus` ★ | categorical | — | `P I F`, `EXEMPT`, `CANCLD`, `CHGOFF`, `COMMIT` | Current status. **The field the whole case turns on** — see the note below | 0.0% |
| `PaidInFullDate` | date | — | — | Date paid in full, where applicable | 30.5% |
| `ChargeOffDate` ★ | date | — | 1991-12 → 2026-06 | Date SBA charged the loan off. Present on 99.97% of `CHGOFF` rows and on no other row. **Minus `ApprovalDate`, this is age at default** | 87.0% |
| `GrossChargeOffAmount` ★ | decimal | USD | 0 where no charge-off | Total balance charged off, guaranteed and unguaranteed portions together. Gross: recoveries are not recorded | 0.0% |
| `RevolverStatus` | categorical | — | 0 = term, 1 = revolver | Term loan or revolving line. A revolver's "term" means something different, so it is a control worth checking | 0.0% |
| `JobsSupported` | integer | jobs | — | Jobs created plus retained, **as reported by the lender**; the publisher states it does not review or audit the figure | 0.0% |
| `CollateralInd` | categorical | — | Y / N | Whether the lender reported the loan as collateral-backed | 1.0% |
| `SoldSecMrktInd` | categorical | — | Y / N | Whether the loan was sold on the secondary market | 71.2% |

## `LoanStatus`, in full

The publisher's definitions, because the analysis stands or falls on reading them correctly:

| Value | Publisher's definition | Rows | In the population at risk? |
|---|---|---|---|
| `P I F` | Paid in full | 1,179,360 | Yes — survived to a terminal outcome |
| `CHGOFF` | Charged off | 220,688 | Yes — the event |
| `EXEMPT` | Disbursed, but not cancelled, paid in full or charged off; withheld under FOIA Exemption 4 | 297,494 | Yes — **still alive at the cut-off; this is the censored population** |
| `CANCLD` | Cancelled | 242,790 | No — never funded |
| `COMMIT` | Undisbursed | 21,123 | No — never funded |

## Derived columns

| Column | Formula | Unit | Created in |
|---|---|---|---|
| `age_at_chargeoff` | `date_diff('month', ApprovalDate, ChargeOffDate)` | months | `notebooks/procesar.py` |
| `observable_age` | `date_diff('month', ApprovalDate, AsOfDate)` | months | `notebooks/procesar.py` |
| `cohort` | `ApprovalFY` | fiscal year | `notebooks/procesar.py` |
| `at_risk` | `LoanStatus IN ('P I F','CHGOFF','EXEMPT')` | boolean | `notebooks/procesar.py` |
| `size_band` | quantile bands of `GrossApproval` within cohort | categorical | `notebooks/procesar.py` |
| `term_band` | banded `TermInMonths` (≤ 84, 85–120, 121–240, > 240) | categorical | `notebooks/procesar.py` |
| `cum_chargeoff_rate(n)` | loans in cohort with `age_at_chargeoff` ≤ *n* ÷ loans in cohort with `at_risk` | % | `notebooks/analizar.py` |
