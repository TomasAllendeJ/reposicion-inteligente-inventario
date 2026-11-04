# -*- coding: utf-8 -*-
"""
02_modelo.py
------------------------------------------------------------------
Paso 2: Modelo de pronostico de demanda + comparacion con baselines.

Que hace:
  1. Carga el dataset limpio (una serie diaria por SKU).
  2. Separa train / test (ultimos 28 dias = test).
  3. Pronostica con:
       - Media movil 7d        (baseline simple)
       - Naive estacional       (baseline ingenuo)
       - Holt-Winters PURO      (nuestro codigo para n8n)
       - Holt-Winters statsmodels (referencia de libreria, para validar)
  4. Calcula MAE, MAPE y WMAPE por SKU y en promedio.
  5. Valida que nuestro Holt-Winters puro da un error similar al de statsmodels.
  6. Guarda tabla de metricas (CSV) y graficos (PNG) para el informe.

Uso:
  python 02_modelo.py "../clean/ca_1_top20_long.csv" "../outputs"
------------------------------------------------------------------
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # sin ventana, solo guardar imagenes
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Importamos NUESTRAS funciones en python puro (las mismas que iran a n8n)
from forecast_core import media_movil, naive_estacional, holt_winters, holt_winters_auto

# ---------------------------------------------------------------
# Parametros
# ---------------------------------------------------------------
CSV_IN  = sys.argv[1] if len(sys.argv) > 1 else "../clean/ca_1_top20_long.csv"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "../outputs"
H_TEST  = 28       # dias de prueba (horizonte de evaluacion)
PERIODO = 7        # estacionalidad semanal
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------
# Metricas de error
# ---------------------------------------------------------------
def mae(real, pron):
    return float(np.mean(np.abs(np.array(real) - np.array(pron))))

def mape(real, pron):
    real = np.array(real, dtype=float); pron = np.array(pron, dtype=float)
    mask = real > 0                      # evitamos dividir por cero
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((real[mask] - pron[mask]) / real[mask])) * 100)

def wmape(real, pron):
    # WMAPE = suma de errores / suma de ventas. Estandar en retail, estable.
    real = np.array(real, dtype=float); pron = np.array(pron, dtype=float)
    denom = real.sum()
    return float(np.abs(real - pron).sum() / denom * 100) if denom > 0 else np.nan

# ---------------------------------------------------------------
# Cargar datos
# ---------------------------------------------------------------
print(f"[1/4] Cargando {CSV_IN} ...")
df = pd.read_csv(CSV_IN, parse_dates=["date"])
skus = sorted(df["item_id"].unique())
print(f"      {len(skus)} SKU encontrados")

filas = []           # metricas por SKU
series_para_plot = {}  # guardamos algunas para graficar

# ---------------------------------------------------------------
# Loop por SKU
# ---------------------------------------------------------------
print("[2/4] Entrenando y evaluando por SKU ...")
for sku in skus:
    serie = df[df["item_id"] == sku].sort_values("date")["sales"].tolist()
    if len(serie) < 2 * PERIODO + H_TEST:
        continue  # muy corto, lo saltamos

    train, test = serie[:-H_TEST], serie[-H_TEST:]

    # --- Pronosticos de cada metodo (sobre el train, horizonte H_TEST) ---
    p_ma   = media_movil(train, h=H_TEST, ventana=7)
    p_sn   = naive_estacional(train, h=H_TEST, periodo=PERIODO)
    p_hw, metodo_elegido = holt_winters_auto(train, h=H_TEST, periodo=PERIODO)  # auto (va a n8n)

    # --- Holt-Winters de statsmodels (referencia de libreria) ---
    try:
        modelo = ExponentialSmoothing(train, trend="add", seasonal="add",
                                       seasonal_periods=PERIODO,
                                       initialization_method="estimated").fit()
        p_sm = [max(0.0, v) for v in modelo.forecast(H_TEST)]
    except Exception as e:
        p_sm = [np.nan] * H_TEST

    filas.append({
        "item_id": sku,
        "metodo_n8n": metodo_elegido,
        "MAE_media_movil":  round(mae(test, p_ma), 2),
        "MAE_naive_estac":  round(mae(test, p_sn), 2),
        "MAE_holtwinters":  round(mae(test, p_hw), 2),
        "MAE_hw_statsmodels": round(mae(test, p_sm), 2),
        "WMAPE_media_movil": round(wmape(test, p_ma), 1),
        "WMAPE_holtwinters": round(wmape(test, p_hw), 1),
        "MAPE_holtwinters":  round(mape(test, p_hw), 1),
    })
    series_para_plot[sku] = (train, test, p_hw, p_ma)

# ---------------------------------------------------------------
# Tabla de resultados
# ---------------------------------------------------------------
print("[3/4] Resumiendo resultados ...")
res = pd.DataFrame(filas)
res_path = os.path.join(OUT_DIR, "metricas_por_sku.csv")
res.to_csv(res_path, index=False)

prom = res[["MAE_media_movil", "MAE_naive_estac",
            "MAE_holtwinters", "MAE_hw_statsmodels"]].mean().round(2)

# Cuantos SKU gana Holt-Winters al mejor baseline
mejor_baseline = res[["MAE_media_movil", "MAE_naive_estac"]].min(axis=1)
gana_hw = (res["MAE_holtwinters"] < mejor_baseline).sum()

print("\n" + "=" * 62)
print("COMPARACION DE MODELOS (MAE promedio sobre los 28 dias de test)")
print("=" * 62)
print(f"  Media movil 7d (baseline)   : {prom['MAE_media_movil']}")
print(f"  Naive estacional (baseline) : {prom['MAE_naive_estac']}")
print(f"  Holt-Winters PURO (n8n)     : {prom['MAE_holtwinters']}")
print(f"  Holt-Winters statsmodels    : {prom['MAE_hw_statsmodels']}")
print("-" * 62)
print(f"  Holt-Winters le gana al mejor baseline en {gana_hw}/{len(res)} SKU")
# Validacion: diferencia entre nuestro HW y el de statsmodels
dif = (res["MAE_holtwinters"] - res["MAE_hw_statsmodels"]).abs().mean()
print(f"  [VALIDACION] Dif. media |HW_puro - HW_statsmodels| = {dif:.2f} MAE")
print("=" * 62)
print("\nMetricas por SKU:")
print(res.to_string(index=False))

# ---------------------------------------------------------------
# Graficos para el informe (3 SKU de ejemplo)
# ---------------------------------------------------------------
print("\n[4/4] Generando graficos ...")
ejemplos = list(series_para_plot.keys())[:3]
for sku in ejemplos:
    train, test, p_hw, p_ma = series_para_plot[sku]
    dias_test = range(len(train), len(train) + len(test))
    plt.figure(figsize=(11, 4))
    # mostramos solo los ultimos 90 dias de train para que se vea claro
    ini = max(0, len(train) - 90)
    plt.plot(range(ini, len(train)), train[ini:], label="Historia (real)", color="#555")
    plt.plot(dias_test, test, label="Real (test)", color="black", linewidth=2)
    plt.plot(dias_test, p_hw, label="Holt-Winters", color="#1f77b4", linestyle="--")
    plt.plot(dias_test, p_ma, label="Media movil", color="#d62728", linestyle=":")
    plt.title(f"Demanda diaria - {sku}  (CA_1)")
    plt.xlabel("dia"); plt.ylabel("unidades"); plt.legend(); plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, f"pronostico_{sku}.png")
    plt.savefig(fig_path, dpi=110); plt.close()
    print(f"      guardado: {fig_path}")

print(f"\n[OK] Metricas en: {os.path.abspath(res_path)}")
