-- Analisis de la brecha espejo. Todo en SQL, a proposito: esto es un problema
-- de reconciliacion entre dos fuentes, y reconciliar es lo que SQL hace mejor.

DROP TABLE IF EXISTS espejo;

CREATE TABLE espejo AS
SELECT * FROM read_csv_auto('datos/espejo.csv');

-- El codigo 0 es "el mundo": es el total, no un socio. Los agregados regionales
-- tampoco. Sumarlos junto a los paises contaria dos veces.
CREATE OR REPLACE VIEW v_paises AS
SELECT * FROM espejo
WHERE socio_cod <> 0 AND NOT es_agregado AND valor_usd > 0;


-- ---------------------------------------------------------------- el par espejo
-- Un FULL OUTER JOIN y no un INNER: si un socio aparece de un solo lado, eso
-- tambien es un hallazgo. Un INNER lo escondería.
CREATE OR REPLACE VIEW v_par AS
WITH cr AS (
    SELECT anio, socio_cod, socio, valor_usd AS declara_cr
    FROM v_paises WHERE lado = 'declara_CR'
), socio AS (
    SELECT anio, socio_cod, socio, valor_usd AS declara_socio
    FROM v_paises WHERE lado = 'declara_socio'
)
SELECT
    COALESCE(cr.anio, socio.anio)             AS anio,
    COALESCE(cr.socio_cod, socio.socio_cod)   AS socio_cod,
    COALESCE(cr.socio, socio.socio)           AS socio,
    cr.declara_cr,
    socio.declara_socio,
    socio.declara_socio - cr.declara_cr       AS brecha_usd,
    CASE WHEN cr.declara_cr > 0
         THEN ROUND((socio.declara_socio / cr.declara_cr - 1) * 100, 1) END AS brecha_pc,
    CASE WHEN cr.declara_cr IS NULL     THEN 'solo lo declara el socio'
         WHEN socio.declara_socio IS NULL THEN 'solo lo declara Costa Rica'
         ELSE 'ambos declaran' END            AS cobertura
FROM cr
FULL OUTER JOIN socio USING (anio, socio_cod);


-- ---------------------------------------------------------------- agregado anual
CREATE OR REPLACE VIEW v_anual AS
SELECT
    anio,
    COUNT(*)                                          AS socios,
    SUM(declara_cr)                                   AS cr_dice,
    SUM(declara_socio)                                AS mundo_dice,
    SUM(declara_socio) - SUM(declara_cr)              AS brecha_usd,
    ROUND((SUM(declara_socio) / SUM(declara_cr) - 1) * 100, 1) AS brecha_pc,
    COUNT(*) FILTER (WHERE cobertura = 'solo lo declara el socio')     AS solo_socio,
    COUNT(*) FILTER (WHERE cobertura = 'solo lo declara Costa Rica')   AS solo_cr
FROM v_par GROUP BY anio ORDER BY anio;


-- ---------------------------------------------------------------- quien la explica
-- Aporte de cada socio a la brecha total del anio, con acumulado: responde
-- "cuantos paises explican la mitad del problema".
CREATE OR REPLACE VIEW v_aporte AS
WITH b AS (
    SELECT anio, socio, brecha_usd,
           SUM(brecha_usd) OVER (PARTITION BY anio) AS brecha_anio
    FROM v_par WHERE brecha_usd IS NOT NULL
)
SELECT anio, socio,
       ROUND(brecha_usd / 1e9, 3) AS brecha_mmUSD,
       ROUND(brecha_usd / brecha_anio * 100, 1) AS aporte_pc,
       ROUND(SUM(brecha_usd) OVER (PARTITION BY anio ORDER BY brecha_usd DESC)
             / brecha_anio * 100, 1) AS acumulado_pc,
       ROW_NUMBER() OVER (PARTITION BY anio ORDER BY brecha_usd DESC) AS puesto
FROM b;


-- ---------------------------------------------------------------- persistencia
-- Una brecha de un anio puede ser un error puntual. Una que se repite diez
-- anios seguidos es estructural, y esa es la que vale la pena explicar.
-- OJO CON EL PORCENTAJE. Sin un piso de volumen esta vista se llena de ruido:
-- si Costa Rica declara 1.000 dolares a Serbia y Serbia declara 2 millones, la
-- brecha es de 200.000 %, cierto pero inutil. El porcentaje solo significa algo
-- cuando el denominador tiene tamano. Por eso se exige comercio relevante.
CREATE OR REPLACE VIEW v_persistencia AS
SELECT socio,
       COUNT(*)                                    AS anios,
       ROUND(AVG(declara_cr) / 1e6, 1)             AS cr_declara_medio_mUSD,
       ROUND(AVG(brecha_pc), 1)                    AS brecha_media_pc,
       ROUND(MIN(brecha_pc), 1)                    AS minima,
       ROUND(MAX(brecha_pc), 1)                    AS maxima,
       ROUND(STDDEV_SAMP(brecha_pc), 1)            AS desviacion,
       COUNT(*) FILTER (WHERE brecha_pc > 0)       AS anios_con_brecha_positiva,
       ROUND(SUM(brecha_usd) / 1e9, 2)             AS brecha_acumulada_mmUSD
FROM v_par
WHERE brecha_pc IS NOT NULL
GROUP BY socio
HAVING COUNT(*) >= 8                       -- historia suficiente
   AND AVG(declara_cr) >= 20e6             -- y al menos 20 millones de comercio medio
ORDER BY ABS(SUM(brecha_usd)) DESC;        -- ordenado por plata, no por porcentaje


-- ---------------------------------------------------------------- calidad
-- Los mismos chequeos que se le harian a cualquier carga: lo que no cuadra
-- devuelve filas, no un booleano.
CREATE OR REPLACE TABLE reporte_calidad AS
SELECT 'socio sin contraparte' AS chequeo, 'aviso' AS severidad,
       anio, socio, cobertura AS detalle
FROM v_par WHERE cobertura <> 'ambos declaran'
UNION ALL
SELECT 'brecha extrema (>200%)', 'aviso', anio, socio,
       'brecha de ' || brecha_pc || ' %'
FROM v_par WHERE brecha_pc > 200
UNION ALL
SELECT 'Costa Rica declara mas que el socio', 'revisar', anio, socio,
       'brecha de ' || brecha_pc || ' % — lo habitual es lo contrario'
FROM v_par WHERE brecha_pc < -20
UNION ALL
SELECT 'duplicado por anio y socio', 'error', anio, socio,
       'aparece ' || n || ' veces'
FROM (SELECT anio, socio, COUNT(*) AS n FROM v_par GROUP BY 1, 2 HAVING COUNT(*) > 1);
