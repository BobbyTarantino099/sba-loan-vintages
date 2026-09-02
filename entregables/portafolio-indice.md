<!-- Phase 6 deliverable. The paragraph that introduces this case in the portfolio index.
     For many readers it is the only thing they will read, so it carries the finding, not
     the topic. -->

# Portfolio index entry

## Short version (index card, ~40 words)

A loan book's charge-off rate lies when the vintages in it are of different ages. Corrected against
the maturation of 24 completed vintages, the 2023 SBA vintage moves from 3.5% to a projected 12.2% —
the worst since 2009. SQL on DuckDB, 1.7 million loans.

## Long version (case intro, ~110 words)

A private credit fund has to price loss it has not yet seen, and the only evidence it has — the
charge-off rate of recent origination years — is flattering by construction. This case builds the
maturation curve of 1.7 million SBA 7(a) loans approved since 1991 and reads every vintage at the
same age instead of on the same date. A three-year-old vintage turns out to have shown only 23.5% of
the losses it will suffer; the 2023 book projects to 12.2% against an observed 3.5%. The two
youngest vintages are published as a labelled gap rather than a number, because a 606× multiplier on
a near-zero rate is not a forecast.

## What it demonstrates that the other cases don't

The reflex that separates a credit analyst from someone who can group rows in SQL: knowing that a
raw default rate is not comparable across cohorts of different ages, and correcting it. Underneath
that, the discipline of refusing to publish a number the method cannot support — and of finding, in
`EXEMPT`, that the field most analysts discard as "unknown outcome" is in fact the censoring
indicator the publisher hands over.
