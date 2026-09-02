<!-- Phase 6 deliverable. Business register, for the committee. The technical register is
     CASO.md; the .docx is generated from this content by notebooks/build_docx.py. -->

# Small-business credit: the vintage you are buying is younger than its number

**Executive summary for the investment committee · 2 September 2026**

## What we set out to test

The fund has to commit an expected-loss assumption for a book of US small-business loans **now**.
The only evidence available for that decision is the charge-off rate of recent origination years —
and we suspected that evidence is systematically flattering, because a loan approved eighteen months
ago has not had time to default.

We wrote three expectations down before opening the data. Two of them turned out to be wrong, and
the way they were wrong is the useful part.

## What we found

**A three-year-old vintage has shown you less than a quarter of what it will cost.** Across the
twenty-four vintages old enough to have finished, only **23.5%** of eventual charge-offs have
occurred by month 36. The median default lands at month 58 — year five, not year three. Half the
loss is still ahead at the five-year mark.

**The 2023 vintage is on track to be the worst since 2010.** It has recorded 0.75 cents of loss per
dollar approved, which reads as excellent. Corrected for age it projects to **4.24 cents**, with an
interquartile band of 3.28 to 6.18. Thirteen consecutive vintages, 2011 through 2022, landed below
that. In loan-count terms the same vintage moves from 3.5% to 12.2%.

**Two vintages get no number at all, on purpose.** The 2024 and 2025 books have realised 5.9% and
0.2% of their eventual loss. Multiplying those up would produce a confident-looking figure resting
on almost nothing, so we publish a gap instead. If a counterparty shows you a loss estimate for a
2025 vintage, that is the number to interrogate.

**2020 and 2021 look like the best underwriting in a decade. They are not.** At the same age they
default at roughly half the rate of every neighbouring vintage — 0.85% and 0.77% against 1.58% to
1.98%. Under CARES Act section 1112 the government was paying instalments on many of these loans.
A model calibrated on those two years understates everything else by about 18%.

**What the correction does not do is reshuffle the league table.** The five worst vintages are the
same whether you read raw rates or rates at equal age. The mistake a fund makes is not picking the
wrong worst year — it is believing a young year's number.

**The loss concentrates in short-term, small-ticket lending.** At 60 months, loans of seven years or
less charge off at 5.67% against 0.39% for loans over twenty years. That is where the loss sits —
though term is a proxy for product and collateral, so it is a statement about which business you are
in, not a lever to pull.

## What we recommend

- **Price the book off a maturation curve, not off its observed rate.** For a 2023-like book the loss
  input moves from 0.75 to 4.24 cents per dollar approved. Low effort: a change of input plus a
  quarterly re-run.
- **Keep 2020 and 2021 out of any calibration sample**, and use 2016–2019 as the modern reference
  window. Low effort.
- **Underwrite the short-term, small-ticket segment on its own terms** instead of at a portfolio
  average. Medium effort: it touches origination policy, not a single number.

## What this analysis cannot tell you

These are SBA-guaranteed loans. The **shape** of the maturation curve transfers to unguaranteed
private credit; the **level** does not, and nothing here can calibrate that gap. Every figure is
gross loss. SBA's own recovery tables put mature cohorts at 34–39% recovered, so a fund's eventual
loss is roughly a third lower than these numbers — a bound, not a conversion, since recovery is
measured against a different amount and on a different year axis. Nothing here is causal: the case
describes how vintages behave, not what moves them, and 2007 is not bad "because of the crisis". And
the projection assumes the loss timing of 1991–2014 still holds; if today's borrowers fail on a
different schedule, the method is wrong in a way it cannot detect on its own.

The population itself is not in doubt. It reconciles against SBA's published performance tables — a
different reporting pipeline from the disclosure extract this case is built on — with a maximum
deviation of **four loans** across nine fiscal years of 42,000 to 70,000 each, and exactly in three
of them. Amounts sit 0.7–1.7% below the published figures in every single year, which the report's
own definition explains: it counts loan increases made after approval, and the extract does not
carry them. A deviation with a constant sign and a documented cause is better evidence than a
smaller one that wanders.

*Full method, checks and decision log: `CASO.md` in the case repository.*
