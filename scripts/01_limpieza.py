# -*- coding: utf-8 -*-
"""
01_limpieza.py
------------------------------------------------------------------
Proyecto Final IA Generativa - Caso: Retail y logistica (M5 Walmart)
Paso 1: Limpieza y transformacion de datos.

Que hace este script:
  1. Lee los 3 archivos crudos de M5 (ventas, calendario, precios).
  2. Filtra UNA tienda (por defecto CA_1).
  3. Elige los TOP N productos (SKU) por volumen total de ventas.
  4. Pasa las ventas de formato ANCHO (un dia por columna) a formato
     LARGO (una fila por producto-dia).  --> esto es lo clave para
     poder trabajar series de tiempo.
  5. Une el calendario (fechas, feriados, SNAP) y los precios.
  6. Limpia: quita el periodo previo al lanzamiento del producto
     (cuando todavia no tenia precio = no estaba a la venta).
  7. Guarda un CSV limpio y ordenado + imprime un resumen para el informe.

Uso:
  python 01_limpieza.py <carpeta_datos> <carpeta_salida> [STORE_ID] [TOP_N]
Ejemplo:
  python 01_limpieza.py "../m5_data" "../clean" CA_1 20
------------------------------------------------------------------
"""

import sys
import os
import pandas as pd

# ---------------------------------------------------------------
# 0) Parametros de entrada (con valores por defecto)
# ---------------------------------------------------------------
DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "../m5_data"   # donde estan los csv crudos
OUT_DIR  = sys.argv[2] if len(sys.argv) > 2 else "../clean"      # donde guardamos el resultado
STORE_ID = sys.argv[3] if len(sys.argv) > 3 else "CA_1"          # tienda a analizar
TOP_N    = int(sys.argv[4]) if len(sys.argv) > 4 else 20          # cuantos SKU elegir

os.makedirs(OUT_DIR, exist_ok=True)
print(f"[CONFIG] tienda={STORE_ID} | top_n={TOP_N} | datos={DATA_DIR}")

# ---------------------------------------------------------------
# 1) Cargar los archivos crudos
# ---------------------------------------------------------------
print("[1/6] Cargando archivos crudos...")
ventas    = pd.read_csv(os.path.join(DATA_DIR, "sales_train_evaluation.csv"))
calendar  = pd.read_csv(os.path.join(DATA_DIR, "calendar.csv"))
precios   = pd.read_csv(os.path.join(DATA_DIR, "sell_prices.csv"))
print(f"       ventas crudas: {ventas.shape[0]} series x {ventas.shape[1]} columnas")

# ---------------------------------------------------------------
# 2) Filtrar la tienda elegida
# ---------------------------------------------------------------
print(f"[2/6] Filtrando tienda {STORE_ID}...")
ventas = ventas[ventas["store_id"] == STORE_ID].copy()
print(f"       productos en {STORE_ID}: {ventas.shape[0]}")

# Columnas que identifican al producto (no son dias)
id_cols  = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
# Columnas de dias (d_1, d_2, ...)
day_cols = [c for c in ventas.columns if c.startswith("d_")]

# ---------------------------------------------------------------
# 3) Elegir el Top N de productos por volumen total de ventas
#    (asi nos quedamos con los que SI se venden, no los intermitentes)
# ---------------------------------------------------------------
print(f"[3/6] Seleccionando Top {TOP_N} SKU por volumen RECIENTE (ultimo ano)...")
# Usamos solo los ultimos 365 dias para no elegir productos ya descontinuados
dias_recientes = day_cols[-365:]
ventas["total_reciente"] = ventas[dias_recientes].sum(axis=1)
top_items = (ventas.sort_values("total_reciente", ascending=False)
                   .head(TOP_N)["item_id"].tolist())
ventas = ventas[ventas["item_id"].isin(top_items)].copy()
ventas = ventas.drop(columns=["total_reciente"])
print(f"       SKU elegidos: {top_items}")

# ---------------------------------------------------------------
# 4) Pasar de formato ANCHO a LARGO (melt)
#    Antes: 1 fila por producto, 1941 columnas de dias
#    Despues: 1 fila por (producto, dia)
# ---------------------------------------------------------------
print("[4/6] Transformando a formato largo (melt)...")
largo = ventas.melt(id_vars=id_cols,
                    value_vars=day_cols,
                    var_name="d",            # d_1, d_2, ...
                    value_name="sales")      # unidades vendidas ese dia
print(f"       filas tras melt: {len(largo):,}")

# ---------------------------------------------------------------
# 5) Unir con el calendario y con los precios
# ---------------------------------------------------------------
print("[5/6] Uniendo calendario y precios...")
# 5a) calendario: nos da la fecha real, feriados y SNAP a partir del codigo "d"
cal_cols = ["d", "date", "wm_yr_wk", "weekday", "wday", "month", "year",
            "event_name_1", "event_type_1", "snap_CA"]
largo = largo.merge(calendar[cal_cols], on="d", how="left")

# 5b) precios: el precio es SEMANAL (por wm_yr_wk), se une por tienda+item+semana
largo = largo.merge(precios, on=["store_id", "item_id", "wm_yr_wk"], how="left")

# Convertir la fecha a tipo fecha de verdad y ordenar
largo["date"] = pd.to_datetime(largo["date"])
largo = largo.sort_values(["item_id", "date"]).reset_index(drop=True)

# ---------------------------------------------------------------
# 6) Limpieza final
# ---------------------------------------------------------------
print("[6/6] Limpieza final...")
filas_antes = len(largo)

# 6a) Quitar el periodo PREVIO al lanzamiento del producto:
#     si no hay precio (sell_price NaN) es porque el producto aun no se
#     vendia. Esas "ventas 0" no son demanda real, son ausencia de producto.
largo = largo[largo["sell_price"].notna()].copy()
filas_pre_lanzamiento = filas_antes - len(largo)

# 6b) Columnas de evento: rellenar nulos con "none" (dia sin feriado)
largo["event_name_1"] = largo["event_name_1"].fillna("none")
largo["event_type_1"] = largo["event_type_1"].fillna("none")

# 6c) Chequeo de sanidad: no deberian quedar ventas negativas
neg = (largo["sales"] < 0).sum()

# Dejar solo las columnas utiles y ordenadas
cols_finales = ["date", "item_id", "dept_id", "cat_id", "store_id",
                "sales", "sell_price", "weekday", "wday", "month", "year",
                "event_name_1", "event_type_1", "snap_CA"]
largo = largo[cols_finales]

# ---------------------------------------------------------------
# Guardar resultado
# ---------------------------------------------------------------
out_path = os.path.join(OUT_DIR, f"{STORE_ID.lower()}_top{TOP_N}_long.csv")
largo.to_csv(out_path, index=False)

# ---------------------------------------------------------------
# Resumen para el informe
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("RESUMEN DE LIMPIEZA")
print("=" * 60)
print(f"Tienda analizada        : {STORE_ID}")
print(f"SKU seleccionados       : {TOP_N}")
print(f"Rango de fechas         : {largo['date'].min().date()} a {largo['date'].max().date()}")
print(f"Filas finales           : {len(largo):,}")
print(f"Filas pre-lanzamiento quitadas (sin precio): {filas_pre_lanzamiento:,}")
print(f"Ventas negativas        : {neg}")
pct_cero = (largo['sales'] == 0).mean() * 100
print(f"% de dias con 0 ventas  : {pct_cero:.1f}%")
print(f"Precio: min={largo['sell_price'].min():.2f}  max={largo['sell_price'].max():.2f}")
print("\nTop SKU por venta total (unidades):")
resumen_sku = (largo.groupby('item_id')['sales']
                    .agg(['sum', 'mean', 'std'])
                    .sort_values('sum', ascending=False)
                    .round(2))
resumen_sku.columns = ['total_unidades', 'prom_diario', 'desv_std']
print(resumen_sku.to_string())
print("=" * 60)
print(f"\n[OK] Archivo limpio guardado en:\n     {os.path.abspath(out_path)}")
