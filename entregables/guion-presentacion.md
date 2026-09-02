<!-- Phase 5 deliverable. Two audiences, two registers: the three-minute pitch is for the
     investment committee, the Q&A is for whoever knows credit and wants to break it. -->

# Presentation script — SBA 7(a) loan vintages

**Audience:** the investment committee of a private credit fund considering US small-business loans.
Non-technical, decision-making, and short of time.
**Length:** three minutes, four figures.

---

## The three-minute pitch

> **[Figure 1 on screen before saying anything.]**
>
> Your analyst hands you this book and says the 2023 vintage is running at three and a half per
> cent. Against a programme average of thirteen, that looks like one of the best vintages ever
> written.
>
> It isn't. It's just young.
>
> **[Figure 2.]** Here is why. Across the twenty-four vintages old enough to have finished, a
> portfolio of small-business loans has recorded only **twenty-three per cent** of its eventual
> charge-offs by month thirty-six. The median default lands at fifty-eight months — year five, not
> year three. So a three-year-old book has shown you less than a quarter of what it will cost.
>
> **[Back to Figure 1.]** Apply the maturation of the finished vintages to the unfinished ones and
> 2023 lands at **12.2 per cent**, with a range of 10.3 to 13.4. That is worse than every vintage
> since 2009. The grey block is what you can see today; the red block is what the history says is
> still coming.
>
> Two vintages get no number at all. 2024 and 2025 have realised six per cent and two tenths of one
> per cent of their eventual loss. Multiplying those up would produce a confident-looking figure
> built on almost nothing, so the honest output is a gap — and if anyone shows you a loss estimate
> for a 2025 vintage, that is the question to ask them.
>
> **[Figure 4.]** One trap worth naming. 2020 and 2021 look like the best underwriting in a decade.
> They aren't: the CARES Act had the government paying instalments on these loans. That is policy,
> not credit quality, and a model calibrated on those two years will underprice everything.
>
> **[Figure 3.]** And what the correction does *not* do: it doesn't reshuffle the league table. The
> five worst vintages are the same read raw or read at equal age. The error isn't ranking the wrong
> year worst — it's believing a young year's number.
>
> **The recommendation.** Underwrite the current book against a maturation curve, not against
> observed rates. On this evidence the 2023 vintage is the one to price hardest, and anything
> originated in the last two years cannot be priced from its own record at all.

---

## The five hardest questions

Prepared because they are the ones that would actually be asked, not the ones that are easy to
answer.

### 1. Why are loans whose outcome you don't know sitting in your denominator?

Because their outcome *is* known, and it is "not yet defaulted". The publisher's own dictionary
defines `EXEMPT` as a loan **disbursed but not cancelled, paid in full or charged off** — alive at
the cut-off. It is the censoring indicator, handed over explicitly.

Dropping those 297,494 loans would delete most of the recent population and make new vintages look
almost default-free, which is the exact error this analysis exists to correct. What I *do* exclude
is the 264,000 loans that were cancelled or never disbursed: those never put money at risk, so they
belong in neither numerator nor denominator.

### 2. Multiplying by a median factor assumes the past repeats. What if it doesn't?

It does assume that, and the projection is only as good as that assumption — which is why it ships
as a band, not a point.

Three things make it defensible rather than arbitrary. The factors come from twenty-four completed
vintages spanning two recessions, not from a fitted curve. The median is used rather than the mean
precisely so 2007 cannot drag it. And the cohorts that are furthest from complete are refused
outright rather than extrapolated.

What it cannot detect is a **structural** change in the *timing* of losses — if today's borrowers
fail faster or slower than history, the projection is wrong and this method will not notice. That
is written into the limitations, and it is the reason the recommendation is to re-run this on each
quarterly file rather than to trust one number.

### 3. These loans carry a government guarantee. What transfers to private credit and what doesn't?

**The shape transfers; the level does not.** How a book of small-business loans seasons — slow for
two years, steep through years three to six, tailing out past year ten — is a property of
small-business credit, not of the guarantee.

The level is a different matter, and in two directions at once. A 7(a) loan exists because the
borrower could not get conventional credit on reasonable terms, which selects towards weaker credit.
And the lender only carries the unguaranteed slice, which plausibly makes it slower to work a loan
out, so charge-offs may be recorded later here than a private lender would record them.

So: use the curve to correct your own vintages for age. Do not lift 12.2% into an unguaranteed
portfolio.

### 4. Why 2023 and not 2022, when 2022 has the higher raw rate?

Because they are different ages, which is the whole point. 2022 shows 4.1% and 2023 shows 3.5% — but
2022 has been observed for 45 months and 2023 for 33. At their respective ages, 2022 has realised
37% of its eventual loss and 2023 only 19.5%. Projected out, 2022 lands at 8.8% and 2023 at 12.2%.

The raw ordering between them is an artefact of the twelve months separating them.

### 5. You couldn't reconcile against an external source. How do I know the population is right?

You have my word on less than I would like, and I would rather say so than dress it up. SBA
publishes aggregate performance tables that would settle this in one line; the archive their own
page links to returns a 404, and I did not find a live replacement.

What is checked: the population was recounted straight off the raw CSVs, bypassing every
intermediate table — 1,961,455 approvals, 1,697,542 disbursed, 220,688 charged off, identical both
ways. The data also obeys the programme's published rules: no loan above the $5,000,000 statutory
cap, no guarantee larger than its own loan, a 74.2% average guarantee. And the cumulative curve was
recomputed by direct counting instead of a windowed sum, with zero discrepancies across 140 cells.

That is internal consistency plus a rule check. It is not an external reconciliation, and it stays
on the limitations list until it is done.

---

## What I would show if there were thirty minutes instead of three

- The term and size cuts, which exist in `salidas/tablas/` and did not earn a figure here.
- The direct standardisation behind V4 — the check that the reordering is the vintage and not a
  change of mix — which is the most technical thing in the case and the most convincing.
- The interactive explorer, where the committee picks the cut and the curve redraws.
