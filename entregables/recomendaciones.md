<!-- Phase 6 deliverable. A finding is not a recommendation. Each card carries action,
     evidence, expected impact with its assumption, how it is measured, its risk, and the
     effort it takes — no exceptions, or it is a slogan. -->

# Recommendations — SBA 7(a) loan vintages

**For:** the investment committee of a private credit fund underwriting US small-business loans.
**From:** the analysis in `CASO.md`, 1,697,539 disbursed SBA 7(a) loans approved FY1991–FY2025, as
of 2026-06-30.
**Prioritised** by impact against effort: R1 first, R3 last.

---

## The unit the committee has to hold in its head

Two rates run through this document and they are not interchangeable.

| Metric | What it is | FY2023 |
|---|---|---|
| **Count-weighted** | Share of *loans* charged off | 12.2% projected |
| **Dollar-weighted** | **Cents charged off per dollar approved at origination** | **4.24 c** projected |

The dollar figure is the one that enters the model, and it needs its label attached every time it
is quoted. It is charge-off balance divided by the **original approved amount**, so amortisation is
already inside it. It is **not** loss on outstanding balance, **not** severity or LGD, and **not**
net of recoveries — the source records none. A committee that hears "4.24%" and files it next to an
LGD will draw the wrong conclusion.

---

## R1 — Price the book off a maturation curve, not off its observed rate

**Action.** Replace "observed charge-off rate" with "age-adjusted projected terminal loss" as the
loss input to the underwriting model, effective at the next investment committee. Owner: the fund's
risk analyst. Cadence: re-run on each quarterly SBA file, which is published one month after each
quarter closes.

**Evidence.** The FY2023 vintage has recorded **0.75 cents of loss per dollar approved**. Read at
its own age and projected on the maturation of the 24 completed vintages, it lands at **4.24 cents**
(interquartile band 3.28–6.18). In count terms the same vintage moves from 3.5% to 12.2%. The
mechanism is one number: **at 36 months a vintage has realised only 23.5% of the charge-offs it
will eventually suffer**, and the median charge-off does not arrive until month 58.

**Expected impact.** For a book resembling FY2023, the loss assumption moves from 0.75 to 4.24 cents
per dollar — the uncorrected figure understates by a factor of **5.7**. *Assumption:* the loss
timing of FY1991–FY2014 continues to hold. FY2023's projection would place it worse than every
vintage since FY2010: thirteen consecutive vintages, FY2011 to FY2022, landed below it.

**How it is measured.** Each quarter, recompute the curve and record realised-against-projected for
every vintage at its current age. A drift above 1 percentage point at equal age is the trigger to
re-derive the development factors rather than to keep multiplying.

**Risk and what must be true.** The method assumes the *shape* of loss timing is stable. If today's
borrowers fail faster or slower than history, the projection is wrong and **this method cannot
detect it** — the error hides inside the factor. Mitigation is the quarterly re-run, not confidence.
A second limit: FY2024 and FY2025 have realised 5.9% and 0.2% of their eventual loss, so they are
published with no projection at all. If a counterparty shows you a loss estimate for a 2025 vintage,
that is the number to interrogate.

**Effort.** **Low.** It is a change of input and a recurring job, not a project.

---

## R2 — Keep FY2020 and FY2021 out of any calibration sample

**Action.** Exclude the FY2020 and FY2021 vintages from the sample used to calibrate expected loss,
and use **FY2016–FY2019** as the modern reference window instead. Owner: whoever maintains the loss
model. Immediate.

**Evidence.** At 36 months of age, FY2020 sits at 0.85% and FY2021 at 0.77%, against 1.72% for
FY2018, 1.58% for FY2019 and 1.98% for FY2022 — roughly half, at exactly the same age. Under CARES
Act section 1112 the federal government paid principal and interest on many 7(a) loans through the
pandemic. That is policy, not credit quality.

**Expected impact.** Including those two years pulls a FY2016–FY2021 average at 36 months from
**1.83% down to 1.49%**, an understatement of 18% before any other adjustment. *Assumption:* the
relief programme explains the gap. The timing and the size of the gap support it; the data cannot
prove it, because the file records no relief flag.

**How it is measured.** Recompute the calibration average with and without the two vintages and
record the delta in the model documentation, so the exclusion is visible to whoever inherits it
rather than buried in a filter.

**Risk and what must be true.** Two risks pull in opposite directions. Dropping two years costs
sample size at exactly the point where recent behaviour matters most. And if the relief **deferred**
defaults rather than preventing them, those vintages will catch up later and their curves will
steepen — which the quarterly re-run of R1 would reveal. Neither risk argues for including them
today.

**Effort.** **Low.** A filter and a paragraph of documentation.

---

## R3 — Underwrite the short-term, small-ticket segment on its own terms

**Action.** Stop pricing the book at a portfolio average. Either tilt the origination mix towards
longer-term, larger loans for a given loss target, or price the short-term small-ticket segment
against its own curve. Owner: credit policy, at the next policy review.

**Evidence.** At 60 months of age, averaged across FY2010–FY2019:

| Contracted term | Charge-off rate at 60 months |
|---|---|
| ≤ 7 years | **5.67%** |
| 7–10 years | 3.87% |
| 10–20 years | 0.67% |
| > 20 years | **0.39%** |

A fourteen-fold spread. Loan size runs the same way and less steeply: the smallest quartile within
its own vintage reaches 6.01% against 1.34% for the largest — 4.5×.

**Expected impact.** A single portfolio-average price systematically overcharges the long-term,
large-ticket segment and undercharges the short, small one. *Assumption:* the segments keep behaving
as they have across ten vintages.

**How it is measured.** Track realised loss by term band against these benchmarks at 36 and 60
months. A band drifting more than 1 pp from its benchmark at equal age is a pricing signal.

**Risk and what must be true — read this before acting on it.** **Term is a proxy for product and
collateral, not an independent lever.** SBA 7(a) loans of 20+ years are real-estate secured;
short-term loans are working capital. This finding says *where the loss sits*, not that shortening a
term causes default or that lengthening one prevents it. Rewriting short-term loans as long-term
ones would not import the low rate — it would import a different product. Acting on this means
choosing which business to be in, or pricing each properly; it does not mean changing a tenor field.

**Effort.** **Medium.** It touches origination policy and mix, not a single model input.

---

## Deliberately not recommendations

Four things the analysis looked at and will not turn into advice.

- **Sector.** Among sectors with enough volume to be readable, the 60-month rate runs from 4.28% to
  4.57%. It does not separate, and a recommendation built on that spread would be noise dressed as
  guidance.
- **Why any vintage performed as it did.** FY2007 is not bad "because of the crisis" — that is
  context. This file cannot separate the crisis from everything else that changed in 2007, and no
  causal claim is made anywhere in the case.
- **A net-loss figure.** Every rate here is gross. SBA's own recovery tables put mature cohorts at
  **34–39% recovered**, so a fund's eventual loss is roughly a third lower than these numbers —
  but that is a bound, not a conversion. Recovery is a share of the *purchased* amount indexed by
  *purchase* year; these rates are a share of the *approved* amount indexed by *approval* year.
  Dividing one by the other would produce a number with no defensible meaning, so none is given.
- **A number for FY2024 or FY2025.** They exist in the tables as a labelled gap, on purpose.

## What would strengthen this materially

- **Loan-level recovery data**, to move from a bound to an actual net figure. The published rates
  are aggregate and on a different axis; only loan-level recoveries would close this properly.
- **Quarterly rather than annual vintages**, which would sharpen the 2008 and 2020 boundaries where
  the interesting behaviour sits.
- **An unguaranteed comparison book.** The shape of these curves transfers to private credit; the
  level does not, and nothing here can calibrate that gap.

## Next steps

1. Re-run the pipeline on the FY2026 Q3 file when it publishes and record the drift. That is the
   first real test of R1.
2. Add the term-band benchmarks of R3 to the quarterly monitoring pack.
3. ~~Close the external reconciliation.~~ **Done.** It now passes against SBA's published
   performance tables with a maximum deviation of 4 loans across nine fiscal years.

*Full method, checks and decision log: `CASO.md` in the case repository. Cleaning decisions:
`bitacora-limpieza.md`.*
