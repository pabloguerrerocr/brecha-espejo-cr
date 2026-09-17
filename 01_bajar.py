"""Baja los dos lados del espejo del comercio exterior de Costa Rica.

    python 01_bajar.py

Estadistica espejo: cada transaccion internacional se registra dos veces, una
por el exportador y otra por el importador. En teoria las dos cifras deberian
coincidir. En la practica nunca lo hacen, y la diferencia se usa para detectar
subfacturacion, reexportacion y errores de clasificacion.

  LADO A  Costa Rica declara cuanto exporta a cada socio.
  LADO B  Cada socio declara cuanto importa de Costa Rica.

Cosa importante del endpoint, averiguada probandolo: cuando se piden varios
reporters, la API desglosa por regimen aduanero, modo de transporte y segundo
socio, y la respuesta topa en 500 registros. Hay que fijar customsCode=C00,
motCode=0 y partner2Code=0 para traer solo el agregado.
"""
import json
import os
import sys
import time

import pandas as pd
import requests

sys.stdout.reconfigure(encoding="utf-8")

AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "datos", "cache")
SALIDA = os.path.join(AQUI, "datos")
os.makedirs(CACHE, exist_ok=True)

API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
CR = 188
ANIOS = list(range(2015, 2025))
H = {"User-Agent": "Mozilla/5.0"}
ESPERA = 5.0


def cacheado(nombre, url, params=None):
    destino = os.path.join(CACHE, nombre + ".json")
    if os.path.exists(destino):
        return json.load(open(destino, encoding="utf-8"))
    for intento in range(4):
        r = requests.get(url, params=params, headers=H, timeout=90)
        if r.status_code == 200:
            d = r.json()
            json.dump(d, open(destino, "w", encoding="utf-8"))
            time.sleep(ESPERA)
            return d
        if r.status_code == 429:
            espera = 25 * (intento + 1)
            print(f"    429, esperando {espera}s", flush=True)
            time.sleep(espera)
            continue
        r.raise_for_status()
    raise RuntimeError("no pude bajar " + nombre)


print("Catalogo de paises")
paises = {int(x["PartnerCode"]): (x["PartnerDesc"], bool(x.get("isGroup", False)))
          for x in cacheado("ref_paises", REF)["results"]
          if str(x.get("PartnerCode", "")).isdigit()}
print(f"  {len(paises)} entradas\n")

filas = []
for anio in ANIOS:
    # LADO A: Costa Rica como reporter. No necesita filtros: CR no desglosa.
    for f in cacheado(f"cr_exporta_{anio}", API, {
            "reporterCode": CR, "period": anio,
            "cmdCode": "TOTAL", "flowCode": "X"}).get("data", []):
        cod = f.get("partnerCode")
        nom, grupo = paises.get(cod, (f"cod {cod}", False))
        filas.append({"anio": anio, "lado": "declara_CR", "socio_cod": cod,
                      "socio": nom, "es_agregado": grupo,
                      "valor_usd": f.get("primaryValue")})

    # LADO B: el resto del mundo como reporter, importando de Costa Rica.
    for f in cacheado(f"mundo_importa_{anio}", API, {
            "partnerCode": CR, "period": anio, "cmdCode": "TOTAL",
            "flowCode": "M", "customsCode": "C00", "motCode": 0,
            "partner2Code": 0}).get("data", []):
        cod = f.get("reporterCode")
        nom, grupo = paises.get(cod, (f"cod {cod}", False))
        filas.append({"anio": anio, "lado": "declara_socio", "socio_cod": cod,
                      "socio": nom, "es_agregado": grupo,
                      "valor_usd": f.get("primaryValue")})
    print(f"  {anio} ok", flush=True)

df = pd.DataFrame(filas)
df.to_csv(os.path.join(SALIDA, "espejo.csv"), index=False, encoding="utf-8")

print(f"\n{len(df):,} filas en datos/espejo.csv")
print(df.groupby("lado").agg(filas=("valor_usd", "size"),
                             socios=("socio_cod", "nunique")).to_string())
