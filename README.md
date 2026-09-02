# Corrected for age, the 2023 vintage of US small-business loans is the worst since 2009

> A loan book's charge-off rate lies when the vintages inside it are of different ages. The FY2023
> SBA 7(a) vintage shows **3.5%** — one of the best numbers in the programme's history. Read at the
> same age as every other vintage and projected on the maturation of the 24 completed ones, it
> lands at **12.2%** (band 10.3–13.4). The mechanism is one number: **at 36 months a vintage has
> realised only 23.5% of the charge-offs it will eventually suffer.**

`SQL` `DuckDB` `Python` `matplotlib` `1,697,539 loans` `35 vintages` `1991–2026`

**Full case, findings and recommendations →
[juanesportfolio.com/cases/sba-loan-vintages](https://juanesportfolio.com/cases/sba-loan-vintages/)**

This repository is the case's evidence layer: the full phase-by-phase log, the cleaning log, source
records and the reproducible pipeline. The narrative — context, data, process, findings,
recommendations — lives on the site linked above.

---

## The question

A private credit fund has to commit an expected-loss assumption for a book of US small-business
loans **now**. The only evidence it has is the charge-off rate of recent origination years, and that
evidence is flattering by construction: a loan approved eighteen months ago has not had time to
default.

The analytical question: across SBA 7(a) loans approved FY1991–FY2026, how does the cumulative
charge-off rate evolve with months since approval for each annual vintage — and once vintages are
read at equal **age** rather than at a common **date**, what terminal loss do the immature ones
imply?

**Client is fictional; the analysis is not.**

## What the data says

**A three-year-old vintage has shown less than a quarter of what it will cost.** Only 23.5% of
eventual charge-offs have occurred by month 36, and the median default arrives at month 58. Half the
loss is still ahead at five years.

![Step curve showing the share of a vintage's eventual charge-offs that has already occurred, by months since approval, measured on the 24 completed vintages. It reaches 23.5% at 36 months, 56.6% at 60 months and 97.0% at 120 months, so three years after approval three quarters of the loss is still ahead.](salidas/graficos/02_a_los_tres_anos.png)

**FY2023 projects to 12.2% against an observed 3.5%.** Every completed vintage from FY2010 to FY2014
landed between 6.0% and 9.2%; FY2023's projection exceeds all of them, and so does the bottom of its
band. In dollar terms — cents charged off per dollar approved — it moves from 0.75 to **4.24**,
which would make it the worst vintage since FY2010 on that measure.

![Stacked column chart of cumulative charge-off rates for the FY2015 to FY2025 vintages. Each column splits into the loss already recorded and the loss the projection says is still to come. FY2023 reaches 12.2%, far above the 6.0–9.2% band where FY2010 to FY2014 landed, even though only 3.5% has been recorded so far. FY2024 and FY2025 carry no projection and are labelled "not projectable"; their raw rates are 1.05% and 0.14%.](salidas/graficos/01_lo_que_falta_por_llegar.png)

**FY2024 and FY2025 are published as a gap, not a number.** They have realised 5.9% and 0.2% of
their eventual loss, which makes their development factors 17× and 606×. Multiplying a near-zero
rate by 606 produces a precise-looking figure built on nothing — the same error this case exists to
expose, committed in its own last figure. The honest output is the gap.

**FY2020 and FY2021 are policy, not performance.** At the same age they default at roughly half the
rate of every neighbour, because CARES Act section 1112 had the federal government paying
instalments on many 7(a) loans. A model calibrated on those two years understates everything else by
about 18%.

![Five small panels with identical axes, one per vintage from FY2018 to FY2022, showing the cumulative charge-off rate over the first 45 months. FY2018, FY2019 and FY2022 reach 2.8%, 2.5% and 3.2%. FY2020 and FY2021, labelled "CARES Act relief", reach only 1.5% and 1.4% — roughly half, at exactly the same age.](salidas/graficos/04_artefacto_de_politica.png)

**The correction changes the level, not the order.** This contradicts what was written down before
the analysis. Rank correlation between the raw ranking and the equal-age ranking is 0.92–0.96, and
the five worst vintages are the same either way. The error a fund makes is not ranking the wrong
vintage worst — it is believing a young vintage's number.

![Bump chart of the rank of 28 vintages by charge-off rate under four readings: the raw rate and the rate at 36, 60 and 84 months. Most lines stay flat. The five worst — 2007, 2006, 2008, 2005 and 2004 — hold the top five places under every reading, with only minor swaps between them.](salidas/graficos/03_nivel_no_orden.png)

## Recommendations

Full cards, each with evidence, expected impact, measurement, risk and effort, in
[`entregables/recomendaciones.md`](entregables/recomendaciones.md).

1. **Price the book off a maturation curve, not off its observed rate.** For a FY2023-like book the
   loss input moves from 0.75 to 4.24 cents per dollar approved — the uncorrected figure understates
   by 5.7×. Low effort.
2. **Keep FY2020 and FY2021 out of any calibration sample**; use FY2016–FY2019 as the modern
   reference window. Low effort.
3. **Underwrite the short-term, small-ticket segment on its own terms.** At 60 months, loans of ≤7
   years charge off at 5.67% against 0.39% for loans over 20 years. Medium effort — and term is a
   proxy for product and collateral, so this says where the loss sits, not that tenor causes it.

## Data

| Source | Period | Volume | Licence |
|---|---|---|---|
| [SBA 7(a) FOIA loan-level extract](https://data.sba.gov/dataset/7a-504-foia) | FY1991–FY2026, as of 2026-06-30 | 1,961,455 approvals · 42 columns · 901 MB | U.S. Government Works (public domain) |

**It can answer the question** because every disbursed loan carries either a terminal outcome or an
explicit still-alive marker, plus the dates needed to place the event on a timeline. The single most
consequential field is `EXEMPT`, which the publisher defines as *disbursed but not cancelled, paid in
full or charged off* — that is not missing data, it is the censoring indicator handed over
explicitly, and dropping it would delete almost the entire recent population.

**It cannot answer**: net loss (no recoveries are recorded, so every figure is gross); the level of
loss in unguaranteed private credit (these loans carry a partial government guarantee — the curve's
shape transfers, its level does not); sector before FY2001 (`NaicsCode` is absent for 55–57% of
earlier approvals); or *why* any vintage behaved as it did — no causal claim is made anywhere.

ROCCC assessment, potential biases and the full integrity test:
[`documentacion/fichas-de-fuente.md`](documentacion/fichas-de-fuente.md).

## Reproduce

The four raw CSVs are **not in this repository** — 901 MB, and the licence does not require
redistribution. `descargar.py` rebuilds them.

> **Important.** SBA refreshes these files quarterly and **overwrites the same URLs**. A file
> downloaded today will not be the one this case analysed. The sha256 of each file is recorded in
> `documentacion/fichas-de-fuente.md`; `python notebooks/descargar.py --solo-hashes` recomputes them
> without downloading. If they differ, you have newer data — the figures will change, and
> `procesar.py` will stop, because it asserts the counts that closed phase 2.

```bash
# 1. Clone
git clone https://github.com/BobbyTarantino099/sba-loan-vintages.git
cd sba-loan-vintages

# 2. Dependencies
pip install -r requirements.txt

# 3. Rebuild the raw files (~901 MB) and print their fingerprints
python notebooks/descargar.py

# 4. Run in order — each step consumes the previous one's output
python notebooks/procesar.py    # cleaning + reconciliation -> datos/limpios/
python notebooks/analizar.py    # curves and projection     -> salidas/tablas/
python notebooks/verificar.py   # the seven checks, V0 to V6
python notebooks/graficos.py    # the four figures          -> salidas/graficos/
python notebooks/build_docx.py  # the executive summary     -> entregables/
```

Before making this repository public:

```bash
bash scripts/verificar-rutas.sh
```

## What's here

```
├── CASO.md                       # living log of the 8 phases and every decision made
├── bitacora-limpieza.md          # every cleaning transformation, with its rationale
├── consultas/                    # all the analysis logic, in SQL with dated headers
│   ├── 01_construir_base.sql     # typed load of the four raw files
│   ├── 02_poblacion.sql          # population at risk and derived labels
│   ├── 03_curvas.sql             # the vintage × age matrix
│   ├── 04_proyeccion.sql         # development factors, count-weighted
│   └── 05_proyeccion_usd.sql     # development factors, dollar-weighted
├── datos/crudos/                 # raw. Not versioned — descargar.py rebuilds it
├── documentacion/
│   ├── diccionario-de-datos.md   # all 42 columns, publisher's definitions, null rates
│   ├── fichas-de-fuente.md       # ROCCC, six biases, integrity test, sha256
│   └── sba_diccionario_oficial.xlsx
├── notebooks/                    # descargar · procesar · analizar · verificar · graficos · build_docx
├── salidas/
│   ├── graficos/                 # the four figures
│   └── tablas/                   # aggregate tables + the explorer's JSON
└── entregables/
    ├── recomendaciones.md        # the three recommendation cards + limitations
    ├── resumen_ejecutivo.md/.docx# for the (fictional) investment committee
    ├── guion-presentacion.md     # 3-minute script + the five hardest questions
    └── portafolio-indice.md
```

---

*Fictional client, real analysis. Data from the U.S. Small Business Administration, public domain.*
