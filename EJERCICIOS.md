# Ejercicios sobre la brecha espejo

Las consultas de `02_analisis.sql` ya están escritas. **Reescribilas vos sin
mirarlas** — esa es la práctica. Abrí la base y probá:

```bash
python -c "import duckdb; duckdb.connect('espejo.duckdb').sql('SELECT * FROM espejo LIMIT 5').show()"
```

O mejor, la consola interactiva:

```bash
python -c "import duckdb; duckdb.connect('espejo.duckdb').sql('SELECT 1').show(); import code; code.interact(local={'c': duckdb.connect('espejo.duckdb')})"
```

---

### 1 · El par espejo
Devolvé, para 2023, cada socio con lo que declara Costa Rica y lo que declara
el socio, en dos columnas.
*Técnica: un `JOIN` de la tabla contra sí misma, filtrando por `lado`.*

### 2 · Por qué `FULL OUTER` y no `INNER`
Repetí el ejercicio 1 con `INNER JOIN` y contá las filas. Después con
`FULL OUTER JOIN`. **¿Cuántos socios se pierden con el `INNER`?**
*Esos son los que solo aparecen de un lado — y son un hallazgo, no ruido.*

### 3 · La brecha porcentual
Agregá una columna con la brecha en por ciento. Cuidado con la división entre
cero y con los nulos que deja el `FULL OUTER`.
*Técnica: `CASE WHEN ... THEN ... END`, no `NULLIF` a secas.*

### 4 · El agregado anual
Una fila por año: cuánto dice Costa Rica, cuánto dice el mundo, la brecha y su
porcentaje.
*Técnica: `GROUP BY` sobre la vista del ejercicio 3.*

### 5 · Cuántos socios explican la mitad
Para 2023, ordená los socios por su aporte a la brecha y calculá el acumulado.
**¿Cuántos hacen falta para llegar al 50 %?**
*Técnica: `SUM(...) OVER (ORDER BY ... DESC)` — suma acumulada, no `GROUP BY`.*

### 6 · El puesto de cada socio
Agregá una columna con la posición de cada socio dentro de su año.
*Técnica: `ROW_NUMBER() OVER (PARTITION BY anio ORDER BY brecha DESC)`.*

### 7 · Brechas persistentes
Socios con al menos 8 años de historia, con su brecha media, mínima, máxima y
desviación estándar.
*Técnica: `GROUP BY` con `HAVING COUNT(*) >= 8`.*
**Pensá qué significa una desviación baja con una media alta.**

### 8 · El año que cambió
Para cada socio, la variación de su brecha contra el año anterior.
*Técnica: `LAG(brecha_pc) OVER (PARTITION BY socio ORDER BY anio)`.*

### 9 · Los que declaran de más
Casos donde **Costa Rica declara más** que su socio — lo contrario de lo
esperado, porque las importaciones se valoran CIF y las exportaciones FOB.
*Técnica: un filtro simple, pero pensá primero qué signo buscás.*

### 10 · Tu propio chequeo de calidad
Inventá un chequeo que no esté en `02_analisis.sql` y escribilo. Debe devolver
**las filas que fallan**, no un booleano.
*Ideas: socios que desaparecen y reaparecen; brechas que cambian de signo;
valores que no crecen en diez años.*

---

## Cómo verificar

Corré tu consulta y compará contra la vista equivalente:

```sql
-- la tuya
SELECT ... ;
-- la de referencia
SELECT * FROM v_par WHERE anio = 2023;
```

Si el conteo de filas y los totales coinciden, está bien aunque el camino sea
distinto.

## La regla

**Veinte minutos peleándolo antes de mirar `02_analisis.sql`.** Si lo abrís
antes, el ejercicio no sirvió de nada.
