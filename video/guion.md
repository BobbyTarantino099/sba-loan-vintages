# Video script: US small-business loan vintages

**Status:** recorded in five parts on 2026-10-18; the cut runs 106 s
**Format:** trailer, ~85 s, narrated in my own voice
**Length:** 213 words (~89 s at the pace of the first two cases, 2.4 words per second)
**Last updated:** 2026-10-18

Numbers carry their literal pronunciation in parentheses *(like this)*. The parentheses are a
reading aid for recording, not part of the narration.

The video invites the viewer to read the case; it does not replace it. The narration leaves out
the recommendations, the dollar figures, the ranking that barely moves and the external
reconciliation: those stay on the page, so that scene 5's question has an answer to go and find.

## Scene 1 · The hook (0-17 s)

> A private credit fund has to put a loss number into its model today. Its only evidence is how
> recent loans have done. And the 2023 *(twenty twenty-three)* vintage of US small-business loans
> shows 3.5% *(three point five per cent)* charged off: one of the best in thirty-five years.

**Visual:** the fund and an empty model input, "expected loss = ?". Then the raw charge-off rate
of every vintage, 1991 to 2025, as a row of columns; 2023 lights up low among them, at 3.5%.

## Scene 2 · The trap (17-42 s)

> The data is every SBA *(S-B-A)* loan since 1991: 1.7 million. But a loan approved two years ago
> hasn't had time to fail. The file even says so: a status most analysts drop as unknown means
> "still alive", and it climbs from under 1% of the 1991 loans to 77% of 2024's. So I read every
> vintage at the same age.

**Visual:** a counter to 1,697,539. One loan's timeline: approved, two years in, the cut-off
date, and the long stretch where it could still fail, greyed out. Then the share of loans still
alive by vintage, a line from 0.7% to 76.8%, labelled with the field's real name, `EXEMPT`.

## Scene 3 · The finding (42-60 s)

> At three years, a vintage has shown less than a quarter of its losses: 23.5% *(twenty-three
> point five)*. The typical failure arrives in year five. Read at the same age, 2023 isn't at
> 3.5%. It's heading for 12.2% *(twelve point two)*: the worst since 2009.

**Visual:** the maturation curve, share of eventual losses already recorded by months since
approval; a marker at 36 months, 23.5%, and the median at month 58. Then 2023's column from
scene 1 grows from 3.5% to 12.2%, with its band, next to the 2010-2014 range (6.0-9.2%) and
2009 (14.7%), all as figure 1 draws them.

## Scene 4 · What gets no number (60-80 s)

> Two vintages get no number at all. 2024 and 2025 have shown under 6% of their losses, and
> multiplying that up is the very mistake the case exists to expose. And 2020 and 2021 look
> excellent at the same age, while the government was paying many of their instalments.

**Visual:** 2024 and 2025 as dashed, empty columns marked "not projectable", each with its
realised share (5.9%, 0.2%). Then the first 36 months of 2018-2022 on one axis: 2020 and 2021
run at half their neighbours, labelled "CARES Act relief".

## Scene 5 · The invitation (80-89 s)

> So what loss number goes into the model, and what can't this data tell us? You can read the
> case below.

**Visual:** the two questions, then a closing card with the case's name and
`juanesportfolio.com/cases/sba-loan-vintages/`.

## Notes on the claims

Checked on 2026-10-18 against `datos/limpios/sba-loan-vintages.duckdb` and `salidas/tablas/`,
before recording, right after the published case was corrected (see the decision log in
`CASO.md`).

- **"3.5% charged off: one of the best in thirty-five years"**: `proyeccion_terminal.csv`,
  `tasa_cruda_pct` = 3.4564 for FY2023. Of the 35 vintages FY1991-FY2025 only three are lower,
  FY2021 (2.83), FY2024 (1.05) and FY2025 (0.14), all younger or policy-flattered. "One of the
  best", not "the best".
- **"every SBA loan since 1991: 1.7 million"**: the population is the 1,697,539 *disbursed* 7(a)
  loans (paid in full, charged off or alive) of 1,961,455 approvals. "SBA loan" means 7(a); 504
  is out of scope. On screen the counter shows 1,697,539.
- **"climbs from under 1% of the 1991 loans to 77% of 2024's"**: `raw_7a`, share of `EXEMPT` by
  fiscal year over all approvals: 0.73% (FY1991), 76.75% (FY2024). Its definition (disbursed, not
  cancelled, paid or charged off) is the publisher's data dictionary. FY2024 is the peak: FY2023
  70.12%, FY2025 74.40% (17.9% of its approvals cancelled), FY2026 56.73% (a partial year with
  30.4% still undisbursed, `COMMIT`). The line on screen ends at 2024, the year the case quotes.
- **"less than a quarter … 23.5%"**: median development factor at 36 months over the 24
  completed vintages, 4.2568 → 1/4.2568 = 23.49%.
- **"The typical failure arrives in year five"**: median age at charge-off = 58 months on
  vintages with ≥ 240 months observable (`analizar.py`); month 58 falls in year five (49-60).
  "Typical" = median; the screen says "median".
- **"heading for 12.2%: the worst since 2009"**: FY2023 projected terminal 12.232% (IQR band
  10.28-13.35), from an observed 2.3886% at 33 months × 5.121. Every vintage FY2010-FY2022 is
  below it (highest FY2010, 8.94%); FY2009 is above (14.39%). So "since 2009" means 2009 itself
  was worse. The 3.5% in the same sentence is the raw rate, the number a fund sees. On screen
  the completed vintages carry their raw (lifetime) rate, as figure 1 draws them: 2010-2014 at
  6.0-9.2% and 2009 at 14.7%; on the terminal rate they are 5.8-8.9% and 14.4%, and the claim
  holds either way (asserted in `datos_video.py`).
- **"under 6% of their losses"**: realised share FY2024 5.93%, FY2025 0.17%; factors 16.9× and
  605.7×. Not projected by the case's rule (≥ 10% realised), set after seeing the factors, which
  the case states.
- **"2020 and 2021 look excellent at the same age, while the government was paying many of
  their instalments"**: at 36 months FY2020 0.85% and FY2021 0.77% against FY2018 1.72%,
  FY2019 1.58% and FY2022 1.98% (V3). The sentence says "while", not "because": the case makes
  no causal claim, and CARES Act §1112 is the documented context, not something the data proves.
  "Many", not "all": §1112 covered many 7(a) loans, not every one.

## Before recording

- Read it aloud against a stopwatch: ~85 s is the target. Recording one part per scene worked
  better in the second case (`Part 1.wav` … `Part 5.wav`, joined by `unir_partes.py`).
- Same microphone, room and distance throughout, a second of silence at both ends of each part,
  and a few seconds of the room alone.
