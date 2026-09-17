"""Corre el analisis en SQL y saca el reporte.

    python 03_reporte.py

Python solo orquesta e imprime. Todo el analisis vive en 02_analisis.sql: eso
es deliberado, porque la pregunta -reconciliar dos fuentes que no cuadran- es
exactamente para lo que sirve SQL.
"""
import os
import sys

import duckdb
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 200)

AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
BD = os.path.join(AQUI, "espejo.duckdb")

if not os.path.exists(os.path.join(AQUI, "datos", "espejo.csv")):
    sys.exit("Falta datos/espejo.csv. Corre primero: python 01_bajar.py")

con = duckdb.connect(BD)
con.execute(open("02_analisis.sql", encoding="utf-8").read())


def seccion(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


def mm(df, cols):
    df = df.copy()
    for c in cols:
        df[c] = (df[c] / 1e9).round(2)
    return df


seccion("LA BRECHA, AÑO POR AÑO  (miles de millones de USD)")
anual = con.execute("SELECT * FROM v_anual").df()
print(mm(anual, ["cr_dice", "mundo_dice", "brecha_usd"])
      .rename(columns={"cr_dice": "CR dice", "mundo_dice": "el mundo dice",
                       "brecha_usd": "brecha", "brecha_pc": "brecha %"})
      .to_string(index=False))

ult = anual.iloc[-1]
print(f"\n  En {int(ult.anio)}, Costa Rica declaró exportar ${ult.cr_dice/1e9:.2f} mm")
print(f"  y sus socios declararon importar ${ult.mundo_dice/1e9:.2f} mm de Costa Rica.")
print(f"  La diferencia es de ${ult.brecha_usd/1e9:.2f} mm ({ult.brecha_pc:+.1f} %).")

seccion("QUIÉN EXPLICA LA BRECHA  (último año)")
a = int(anual.iloc[-1].anio)
print(con.execute(f"""
    SELECT puesto, socio, brecha_mmUSD, aporte_pc AS "aporte %",
           acumulado_pc AS "acumulado %"
    FROM v_aporte WHERE anio = {a} AND puesto <= 10 ORDER BY puesto
""").df().to_string(index=False))

mitad = con.execute(f"""
    SELECT MIN(puesto) FROM v_aporte WHERE anio = {a} AND acumulado_pc >= 50
""").fetchone()[0]
print(f"\n  {mitad} socios explican la mitad de la brecha de {a}.")

seccion("BRECHAS PERSISTENTES  (8+ años y comercio medio sobre $20 M)")
print(con.execute("""
    SELECT socio, anios, cr_declara_medio_mUSD AS "CR declara (mUSD)",
           brecha_media_pc AS "media %", desviacion,
           anios_con_brecha_positiva AS "años +",
           brecha_acumulada_mmUSD AS "acumulada mm"
    FROM v_persistencia LIMIT 12
""").df().to_string(index=False))

print("\n  Una brecha de un año puede ser un error. Una que se repite todos los")
print("  años, con poca desviación, es estructural — y esa sí hay que explicarla.")

seccion("CHEQUEOS DE CALIDAD")
res = con.execute("""
    SELECT severidad, chequeo, COUNT(*) AS n
    FROM reporte_calidad GROUP BY 1, 2 ORDER BY 1, 3 DESC
""").df()
print(res.to_string(index=False) if len(res) else "  sin hallazgos")

print("\n  Casos donde Costa Rica declara MÁS que su socio (lo inusual):")
inv = con.execute("""
    SELECT anio, socio, brecha_pc AS "brecha %"
    FROM v_par WHERE brecha_pc < -20 ORDER BY brecha_pc LIMIT 8
""").df()
print(inv.to_string(index=False) if len(inv) else "  ninguno")

con.close()
print("\nBase en espejo.duckdb — se puede consultar directo con DuckDB.")
