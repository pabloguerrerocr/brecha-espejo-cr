"""Las figuras del README.

    python 04_figuras.py
"""
import os
import sys

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)
FIG = os.path.join(AQUI, "figuras")
os.makedirs(FIG, exist_ok=True)

AZUL, NARANJA, GRIS = "#1c7ed6", "#e8590c", "#adb5bd"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white",
                     "axes.grid": True, "grid.alpha": .25})

con = duckdb.connect("espejo.duckdb", read_only=True)


def cerrar(fig, nombre, titulo, sub):
    fig.suptitle(titulo, fontsize=15, fontweight="bold", x=.02, ha="left", y=.98)
    fig.text(.02, .915, sub, fontsize=10.5, color="#555")
    fig.tight_layout(rect=[0, 0, 1, .89])
    fig.savefig(os.path.join(FIG, nombre), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  ", nombre)


# 1 — los dos lados
a = con.execute("SELECT * FROM v_anual ORDER BY anio").df()
fig, ax = plt.subplots(figsize=(11, 5.4))
ax.fill_between(a.anio, a.cr_dice / 1e9, a.mundo_dice / 1e9, color=NARANJA, alpha=.15)
ax.plot(a.anio, a.cr_dice / 1e9, "o-", color=AZUL, lw=2.6,
        label="lo que Costa Rica declara exportar")
ax.plot(a.anio, a.mundo_dice / 1e9, "s-", color=NARANJA, lw=2.6,
        label="lo que sus socios declaran importar")
u = a.iloc[-1]
ax.annotate(f"brecha\n${u.brecha_usd/1e9:.1f} mm",
            (u.anio, (u.cr_dice + u.mundo_dice) / 2e9),
            textcoords="offset points", xytext=(-58, 0), ha="center",
            fontsize=10.5, fontweight="bold", color=NARANJA)
ax.set_ylabel("miles de millones de USD")
ax.legend(frameon=False, loc="upper left")
cerrar(fig, "01_dos_lados.png", "Dos fuentes oficiales, el mismo comercio",
       "Exportaciones de Costa Rica según quién las reporta. Fuente: UN COMTRADE.")

# 2 — la brecha en porcentaje
fig, ax = plt.subplots(figsize=(11, 4.6))
col = [NARANJA if v > 0 else AZUL for v in a.brecha_pc]
ax.bar(a.anio, a.brecha_pc, color=col, width=.65)
for x, y in zip(a.anio, a.brecha_pc):
    ax.text(x, y + (1.6 if y > 0 else -3.4), f"{y:.0f}%", ha="center",
            fontsize=9.5, fontweight="bold", color="#444")
ax.axhline(0, color="#333", lw=1)
ax.set_ylabel("% por encima de lo que declara Costa Rica")
ax.set_ylim(min(0, a.brecha_pc.min() * 1.3), a.brecha_pc.max() * 1.22)
cerrar(fig, "02_brecha_pc.png", "La brecha no es un año raro: está todos los años",
       "Cuánto más declara el mundo importar de Costa Rica que lo que Costa Rica declara exportar.")

# 3 — quien la explica
ult = int(a.iloc[-1].anio)
t = con.execute(f"""
    SELECT socio, brecha_mmUSD, acumulado_pc FROM v_aporte
    WHERE anio = {ult} AND puesto <= 10 ORDER BY brecha_mmUSD
""").df()
fig, ax = plt.subplots(figsize=(11, 5.6))
ax.barh([s[:34] for s in t.socio], t.brecha_mmUSD, color=NARANJA)
for i, (v, ac) in enumerate(zip(t.brecha_mmUSD, t.acumulado_pc)):
    ax.text(v + t.brecha_mmUSD.max() * .015, i, f"acumula {ac:.0f}%",
            va="center", fontsize=9.5, color="#444")
ax.set_xlabel("brecha, miles de millones de USD")
ax.set_xlim(0, t.brecha_mmUSD.max() * 1.32)
cerrar(fig, "03_quien_explica.png",
       f"Unos pocos socios explican casi toda la brecha ({ult})",
       "Diferencia entre lo que cada socio declara importar y lo que Costa Rica declara exportarle.")

con.close()
print("\nFiguras en figuras/")
