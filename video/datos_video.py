"""
The numbers the video shows, taken from the case's own files instead of typed by hand.

    python video/datos_video.py

Writes video/composicion/assets/datos.js (`window.DATOS = {...}`), loaded by index.html. A .js
and not a .json because a composition must not fetch anything while it renders: every frame has
to come out the same.

Every number comes from salidas/tablas/, or from datos/limpios/ when no aggregated table has
it, and each one is asserted against what the case publishes (checked again on 2026-10-18, right
after the case was corrected). If the analysis ever changes, this stops instead of the video
quietly showing an old number. The reasoning behind each claim is in guion.md, "Notes on the
claims".
"""

from pathlib import Path
import json

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "salidas" / "tablas"
BD = RAIZ / "datos" / "limpios" / "sba-loan-vintages.duckdb"
DESTINO = Path(__file__).resolve().parent / "composicion" / "assets" / "datos.js"

proyeccion = pd.read_csv(TABLAS / "proyeccion_terminal.csv").set_index("cohorte")


def escena_1() -> dict:
    """Raw charge-off rate of every vintage, FY1991-FY2025: what a fund sees today."""
    cruda = proyeccion.tasa_cruda_pct
    assert len(cruda) == 35 and cruda.index.min() == 1991 and cruda.index.max() == 2025
    assert round(cruda[2023], 2) == 3.46
    # "One of the best in thirty-five years": only three are lower, all younger or policy-flattered.
    assert sorted(cruda[cruda < cruda[2023]].index) == [2021, 2024, 2025]
    return {
        "vintages": [{"year": int(a), "raw": round(float(v), 2)} for a, v in cruda.items()],
        "highlight": 2023,
    }


def escena_2() -> dict:
    """The population, and the share of each vintage still alive (EXEMPT) at the cut-off."""
    con = duckdb.connect(str(BD), read_only=True)
    total = con.sql("SELECT count(*) FROM prestamos").fetchone()[0]
    vivos = con.sql("""
        SELECT anio_fiscal AS year, 100.0 * avg((estado = 'EXEMPT')::int) AS pct
        FROM raw_7a WHERE anio_fiscal BETWEEN 1991 AND 2024
        GROUP BY 1 ORDER BY 1
    """).df()
    con.close()
    assert total == 1_697_539
    pct = vivos.set_index("year").pct
    assert round(pct[1991], 2) == 0.73 and round(pct[2024], 2) == 76.75
    assert pct.idxmax() == 2024
    return {
        "loans": int(total),
        "alive": [{"year": int(a), "pct": round(float(v), 2)} for a, v in pct.items()],
    }


def escena_3() -> dict:
    """The maturation curve, and FY2023 read at the same age."""
    f = pd.read_csv(TABLAS / "factores_desarrollo.csv")
    f["realised"] = 100 / f.factor_mediano
    curva = f[f.edad >= 12][["edad", "realised"]]   # below 12 months the factors are on 2-22 vintages
    r36 = float(f.loc[f.edad == 36, "realised"].iloc[0])
    assert round(r36, 1) == 23.5 and (f.cohortes_completas[f.edad >= 12] == 24).all()

    con = duckdb.connect(str(BD), read_only=True)
    mediana = con.sql("""
        SELECT median(edad_al_fallido) FROM prestamos
        WHERE fallido AND NOT fallido_sin_fecha_util
          AND cohorte IN (SELECT cohorte FROM cohortes WHERE edad_min_observable >= 240)
    """).fetchone()[0]
    con.close()
    assert mediana == 58

    p = proyeccion.loc[2023]
    assert round(p.terminal_proyectado_pct, 1) == 12.2
    assert round(p.terminal_q1_pct, 1) == 10.3 and round(p.terminal_q3_pct, 1) == 13.4
    # Completed vintages at their raw (lifetime) rate, as figure 1 draws them: 2010-2014 between
    # 6.0 and 9.2, and 2009 above the projection. "Worst since 2009" holds on the terminal rate too.
    cruda = proyeccion.tasa_cruda_pct
    rango = cruda.loc[2010:2014]
    assert round(rango.min(), 1) == 6.0 and round(rango.max(), 1) == 9.2
    assert cruda[2009] > p.terminal_proyectado_pct > proyeccion.terminal_proyectado_pct.loc[2010:2022].max()
    # The columns of the second beat, 2009-2023, built as figure 1 builds them: a completed
    # vintage is its raw rate; a young one is its raw rate plus what the projection adds.
    columnas = []
    for a in range(2009, 2024):
        fila = proyeccion.loc[a]
        total = fila.tasa_cruda_pct if fila.completa else max(fila.terminal_proyectado_pct, fila.tasa_cruda_pct)
        columnas.append({"year": a, "recorded": round(float(fila.tasa_cruda_pct), 2),
                         "total": round(float(total), 2), "complete": bool(fila.completa)})
    assert max(c["total"] for c in columnas if 2010 <= c["year"] <= 2022) < 12.2
    return {
        "columns": columnas,
        "curve": [{"age": int(e), "pct": round(float(v), 2)} for e, v in curva.values],
        "at36": round(r36, 1),
        "median_age": int(mediana),
        "y2023": {"raw": round(float(p.tasa_cruda_pct), 1),
                  "projected": round(float(p.terminal_proyectado_pct), 1),
                  "q1": round(float(p.terminal_q1_pct), 1),
                  "q3": round(float(p.terminal_q3_pct), 1)},
        "band_2010_2014": [round(float(rango.min()), 1), round(float(rango.max()), 1)],
        "y2009": round(float(cruda[2009]), 1),
    }


def escena_4() -> dict:
    """The two vintages with no number, and FY2018-2022 over their first 36 months."""
    gap = {}
    for a in (2024, 2025):
        fila = proyeccion.loc[a]
        assert not fila.proyectable
        gap[str(a)] = {"realised": round(float(fila.pct_perdida_ya_realizada), 1),
                       "raw": round(float(fila.tasa_cruda_pct), 2),
                       "factor": round(float(fila.factor_mediano))}
    assert gap["2024"]["realised"] == 5.9 and gap["2025"]["realised"] == 0.2
    assert gap["2024"]["factor"] == 17 and gap["2025"]["factor"] == 606

    c = pd.read_csv(TABLAS / "curva_global.csv")
    c = c[c.cohorte.between(2018, 2022) & (c.edad <= 36)]
    a36 = c[c.edad == 36].set_index("cohorte").tasa_acum_pct.round(2)
    assert a36.to_dict() == {2018: 1.72, 2019: 1.58, 2020: 0.85, 2021: 0.77, 2022: 1.98}
    return {
        "gap": gap,
        "policy": [{"year": int(a), "points": [[int(e), round(float(v), 3)] for e, v in g[["edad", "tasa_acum_pct"]].values],
                    "at36": float(a36[a])} for a, g in c.groupby("cohorte")],
    }


def main() -> None:
    datos = {"hook": escena_1(), "trap": escena_2(), "finding": escena_3(), "nonumber": escena_4()}
    texto = json.dumps(datos, indent=2, ensure_ascii=False)
    DESTINO.write_text(
        "// Generated by video/datos_video.py. Do not edit by hand.\n"
        f"window.DATOS = {texto};\n",
        encoding="utf-8",
    )
    print(f"-> {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
