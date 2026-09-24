# Costa Rica and its trade partners do not report the same trade

*[Versión en español](README.md)*

**In 2024, Costa Rica reported $19.9 bn in exports to the world. Its partners
reported importing $34.0 bn from Costa Rica. The difference is $14,140 million
—71%— and it keeps growing.**

![Two official sources](figuras/01_dos_lados.png)

Every international transaction is recorded twice: once by the exporter and once
by the importer. In theory both figures should match. They never do, and that
difference —the *mirror statistic*— is what customs agencies and central banks
use to detect under-invoicing, re-exports and classification errors.

![The gap by year](figuras/02_brecha_pc.png)

The gap is present in all ten years, never falls below 25%, and went from 44% in
2015 to 71% in 2024.

## Three partners explain half of it

![Who explains the gap](figuras/03_quien_explica.png)

| Partner | CR reports (average) | Mean gap | Std. dev. | Cumulative |
|---|---:|---:|---:|---:|
| **United States** | $5,795 M | **+17.3%** | 10.2 | $11.15 bn |
| **China** | $220 M | **+627%** | 396 | $12.40 bn |
| **Belgium** | $705 M | **−37.7%** | **7.0** | −$2.61 bn |

They are three different phenomena, and that is the conclusion of this work:

**United States, +17% with low dispersion.** That is the order of magnitude
explained by FOB versus CIF valuation —imports include freight and insurance—
plus recording lags. It is the "normal" gap.

**China, +627%.** That is not freight. Costa Rica reports exporting $220 million
a year to China, and China reports importing six times as much. The hypothesis to
test is origin attribution: free-zone goods sold to an intermediary and recorded
by the destination country as originating in Costa Rica.

**Belgium, −37.7% with a standard deviation of 7.** The reverse case, and the most
consistent of all: Costa Rica systematically reports **more** than Belgium reports
receiving. A one-year gap is an error; one that repeats for ten years with a
7-point standard deviation is structural.

## Run it

```bash
pip install duckdb pandas requests matplotlib
python 01_bajar.py      # UN COMTRADE, cached
python 03_reporte.py    # runs 02_analisis.sql and prints the report
python 04_figuras.py
```

| File | What it does |
|---|---|
| `01_bajar.py` | both sides of the mirror, with caching and retry on HTTP 429 |
| `02_analisis.sql` | **the whole analysis**: the pairing, the gap, the contribution, persistence and the checks |
| `03_reporte.py` | runs the SQL and prints. Python only orchestrates |
| `04_figuras.py` | the three figures |
| `EJERCICIOS.md` | ten exercises to rewrite the queries without looking (in Spanish) |

## Why the analysis is in SQL

Because it is a reconciliation problem between two sources, and that is what SQL
does better than any other tool. The queries use `FULL OUTER JOIN`, chained CTEs,
`SUM() OVER` for the running total, `ROW_NUMBER() OVER (PARTITION BY)` for the
yearly ranking, and `GROUP BY` with `HAVING`.

**The `FULL OUTER JOIN` is not decoration.** An `INNER` join drops the partners
that appear on only one side, and those are a finding in themselves: in 2024 there
were 17 partners reported only by the other country and 41 reported only by Costa
Rica.

## The mistake this project almost made

The first version of the persistence view sorted by mean percentage gap. The top
result was **Serbia, with a gap of 20 million percent**.

It was true and it was useless: Costa Rica reported a few hundred dollars and
Serbia a few thousand. **A percentage means nothing when the denominator is
tiny.** The view now requires average trade of at least $20 million and sorts by
amount, not by percentage.

It is documented in the SQL itself because it is the kind of error that slips into
an analysis and nobody reviews.

## Data quality checks

Each check returns **the rows that fail**, not a boolean:

| Check | Result |
|---|---:|
| Partners without a counterpart | 530 |
| Extreme gaps above 200% | 451 |
| Costa Rica reports more than the partner | 155 |
| Duplicates by year and partner | 0 |

The first two are concentrated in marginal trade partners. The third is the
interesting one: these are the cases that go against the theory and deserve an
explanation.

## Limitations

- **The gap is not decomposed.** Knowing how much is FOB/CIF, how much is
  re-exports and how much remains unexplained requires freight and origin data
  that COMTRADE does not publish. What can be said is that 17% is consistent with
  FOB/CIF and 627% is not.
- **The analysis is at the total level.** Breaking it down by chapter would show
  whether the gap is concentrated in free-zone products, which is the hypothesis.
- **COMTRADE figures get revised.** Recent years may change.

## Data

UN COMTRADE, public and keyless. Costa Rica is reporter 188. 2015-2024.

A detail that came from testing the API, not from the manual: when requesting
several reporters, the response is broken down by customs regime, transport mode
and second partner, and it cuts off at 500 records. You have to set
`customsCode=C00`, `motCode=0` and `partner2Code=0` to get the aggregate. Without
that the numbers come out wrong and you don't notice.
