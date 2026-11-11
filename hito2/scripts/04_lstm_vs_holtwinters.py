# -*- coding: utf-8 -*-
"""
Hito 2 - Serie temporal con Deep Learning (LSTM / GRU) vs el modelo clasico.

Compara, con EXACTAMENTE el mismo protocolo del Hito 1:
  - train = toda la serie menos los ultimos 28 dias
  - test  = ultimos 28 dias
  - metrica = MAE promedio por SKU

Modelos comparados:
  - Media movil 7d        (baseline)        \\  reusados de forecast_core.py
  - Naive estacional       (baseline)        |  (el mismo codigo que va a n8n)
  - Holt-Winters auto      (clasico, Hito 1) /
  - LSTM  (Deep Learning)  <- nuevo
  - GRU   (Deep Learning)  <- nuevo

Un SOLO modelo global se entrena con ventanas de todos los SKU (mas datos).
Entradas por dia: [venta_escalada, dia_semana(sin), dia_semana(cos), snap_CA].
Las features de calendario (dia de semana, SNAP) del horizonte se conocen de
antemano, asi que el pronostico recursivo es legitimo.

Uso:
  python 04_lstm_vs_holtwinters.py <csv_ventas> <out_dir>
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import torch
import torch.nn as nn

# Reusar las funciones clasicas del Hito 1 (python puro, las mismas de n8n)
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "scripts"))
from forecast_core import media_movil, naive_estacional, holt_winters_auto

H_TEST = 28       # dias de test (igual que Hito 1)
PERIODO = 7
VENTANA = 28      # dias que mira el LSTM para predecir el siguiente
EPOCAS = 40
SEED = 42

torch.manual_seed(SEED); np.random.seed(SEED)


def mae(real, pron):
    return float(np.mean(np.abs(np.array(real, float) - np.array(pron, float))))


# ---------------------------------------------------------------
# 1) Cargar datos y armar, por SKU, los arreglos que necesitamos
# ---------------------------------------------------------------
def cargar(csv_in):
    df = pd.read_csv(csv_in, parse_dates=["date"])
    series = {}
    for sku in sorted(df["item_id"].unique()):
        d = df[df["item_id"] == sku].sort_values("date")
        ventas = d["sales"].to_numpy(float)
        wday = d["wday"].to_numpy(float)                 # 1..7
        snap = d["snap_CA"].to_numpy(float) if "snap_CA" in d else np.zeros(len(d))
        if len(ventas) < 2 * PERIODO + H_TEST + VENTANA:
            continue
        series[sku] = {"ventas": ventas, "wday": wday, "snap": snap}
    return series


def feats_dia(venta_escalada, wday, snap):
    """Vector de features de un dia."""
    ang = 2 * np.pi * (wday / 7.0)
    return [venta_escalada, np.sin(ang), np.cos(ang), snap]


# ---------------------------------------------------------------
# 2) Modelo RNN (sirve para LSTM o GRU)
# ---------------------------------------------------------------
class RedRNN(nn.Module):
    def __init__(self, tipo="LSTM", n_feat=4, oculto=32):
        super().__init__()
        rnn = nn.LSTM if tipo == "LSTM" else nn.GRU
        self.rnn = rnn(input_size=n_feat, hidden_size=oculto, batch_first=True)
        self.fc = nn.Linear(oculto, 1)

    def forward(self, x):
        salida, _ = self.rnn(x)          # (batch, tiempo, oculto)
        ultimo = salida[:, -1, :]        # tomamos el ultimo paso temporal
        return self.fc(ultimo).squeeze(-1)


# ---------------------------------------------------------------
# 3) Construir ventanas de entrenamiento desde el TRAIN de todos los SKU
# ---------------------------------------------------------------
def construir_dataset(series):
    X, Y = [], []
    escalas = {}
    for sku, d in series.items():
        ventas, wday, snap = d["ventas"], d["wday"], d["snap"]
        tr = ventas[:-H_TEST]                           # solo train (sin tocar test)
        mu, sd = tr.mean(), tr.std()
        sd = sd if sd > 1e-6 else 1.0
        escalas[sku] = (mu, sd)
        ventas_esc = (ventas - mu) / sd
        # ventanas dentro del train
        for i in range(VENTANA, len(tr)):
            win = [feats_dia(ventas_esc[j], wday[j], snap[j]) for j in range(i - VENTANA, i)]
            X.append(win); Y.append(ventas_esc[i])
    return (torch.tensor(np.array(X), dtype=torch.float32),
            torch.tensor(np.array(Y), dtype=torch.float32), escalas)


def entrenar(modelo, X, Y, epocas=EPOCAS, batch=128):
    opt = torch.optim.Adam(modelo.parameters(), lr=1e-3)
    perdida = nn.MSELoss()
    n = len(X)
    for ep in range(epocas):
        perm = torch.randperm(n)
        total = 0.0
        modelo.train()
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            opt.zero_grad()
            pred = modelo(X[idx])
            l = perdida(pred, Y[idx])
            l.backward(); opt.step()
            total += l.item() * len(idx)
        if (ep + 1) % 10 == 0:
            print(f"    epoca {ep+1}/{epocas}  loss={total/n:.4f}")


# ---------------------------------------------------------------
# 4) Pronostico recursivo de 28 dias para un SKU
# ---------------------------------------------------------------
def pronosticar(modelo, d, escala):
    ventas, wday, snap = d["ventas"], d["wday"], d["snap"]
    mu, sd = escala
    ventas_esc = (ventas - mu) / sd
    tr_len = len(ventas) - H_TEST
    # ventana inicial = ultimos VENTANA dias del train
    ventana = [feats_dia(ventas_esc[j], wday[j], snap[j]) for j in range(tr_len - VENTANA, tr_len)]
    preds = []
    modelo.eval()
    with torch.no_grad():
        for k in range(H_TEST):
            x = torch.tensor([ventana], dtype=torch.float32)
            p_esc = float(modelo(x).item())
            p = max(0.0, p_esc * sd + mu)               # desescalar + no negativo
            preds.append(p)
            # el dia de semana y el SNAP del horizonte SON conocidos
            dia = tr_len + k
            ventana = ventana[1:] + [feats_dia(p_esc, wday[dia], snap[dia])]
    return preds


# ---------------------------------------------------------------
# 5) Main
# ---------------------------------------------------------------
def main():
    csv_in = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    print("[1/4] Cargando datos...")
    series = cargar(csv_in)
    print(f"      {len(series)} SKU")

    print("[2/4] Construyendo ventanas y entrenando LSTM y GRU...")
    X, Y, escalas = construir_dataset(series)
    print(f"      {len(X)} ventanas de entrenamiento")

    modelos_dl = {}
    for tipo in ["LSTM", "GRU"]:
        print(f"  -> {tipo}")
        m = RedRNN(tipo=tipo)
        entrenar(m, X, Y)
        modelos_dl[tipo] = m

    print("[3/4] Evaluando todos los modelos por SKU (MAE sobre 28 dias)...")
    filas = []
    ejemplo = None
    for sku, d in series.items():
        ventas = d["ventas"]
        train, test = ventas[:-H_TEST].tolist(), ventas[-H_TEST:].tolist()
        p_ma = media_movil(train, h=H_TEST, ventana=7)
        p_sn = naive_estacional(train, h=H_TEST, periodo=PERIODO)
        p_hw, _ = holt_winters_auto(train, h=H_TEST, periodo=PERIODO)
        p_lstm = pronosticar(modelos_dl["LSTM"], d, escalas[sku])
        p_gru = pronosticar(modelos_dl["GRU"], d, escalas[sku])
        filas.append({
            "item_id": sku,
            "MAE_media_movil": round(mae(test, p_ma), 2),
            "MAE_naive": round(mae(test, p_sn), 2),
            "MAE_holtwinters": round(mae(test, p_hw), 2),
            "MAE_LSTM": round(mae(test, p_lstm), 2),
            "MAE_GRU": round(mae(test, p_gru), 2),
        })
        if ejemplo is None:
            ejemplo = (sku, train, test, p_hw, p_lstm)

    res = pd.DataFrame(filas)
    res.to_csv(os.path.join(out_dir, "metricas_series_hito2.csv"), index=False)

    prom = res[["MAE_media_movil", "MAE_naive", "MAE_holtwinters",
                "MAE_LSTM", "MAE_GRU"]].mean().round(3)
    print("\n" + "=" * 56)
    print("MAE PROMEDIO (28 dias de test, 20 SKU)")
    print("=" * 56)
    for k, v in prom.items():
        print(f"  {k:22s}: {v}")
    # cuantos SKU gana el mejor DL al Holt-Winters
    mejor_dl = res[["MAE_LSTM", "MAE_GRU"]].min(axis=1)
    gana_dl = int((mejor_dl < res["MAE_holtwinters"]).sum())
    print("-" * 56)
    print(f"  El mejor DL le gana a Holt-Winters en {gana_dl}/{len(res)} SKU")
    print("=" * 56)

    # guardar resumen
    with open(os.path.join(out_dir, "metrics_series_hito2.json"), "w", encoding="utf-8") as f:
        json.dump({"mae_promedio": {k: float(v) for k, v in prom.items()},
                   "gana_dl_vs_hw": gana_dl, "n_sku": len(res)}, f, ensure_ascii=False, indent=2)

    # guardar modelos para el servicio
    torch.save({"LSTM": modelos_dl["LSTM"].state_dict(),
                "GRU": modelos_dl["GRU"].state_dict(),
                "escalas": escalas, "ventana": VENTANA}, os.path.join(out_dir, "modelo_series.pt"))

    # grafico comparacion
    plt.figure(figsize=(7.5, 4.3))
    nombres = ["Media movil", "Naive", "Holt-Winters\n(clasico)", "LSTM", "GRU"]
    valores = [prom["MAE_media_movil"], prom["MAE_naive"], prom["MAE_holtwinters"],
               prom["MAE_LSTM"], prom["MAE_GRU"]]
    mejor_idx = int(np.argmin(valores))
    colores = ["#9FB4CB"] * 5
    colores[mejor_idx] = "#2A9D8F"
    barras = plt.bar(nombres, valores, color=colores)
    plt.ylabel("MAE (menor = mejor)")
    plt.title("Serie temporal: clasico vs Deep Learning")
    for b, v in zip(barras, valores):
        plt.text(b.get_x() + b.get_width()/2, v + 0.05, f"{v:.2f}", ha="center", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "series_comparacion.png"), dpi=150)

    # grafico de ejemplo (un SKU): real vs HW vs LSTM
    sku, train, test, p_hw, p_lstm = ejemplo
    dias = range(len(test))
    plt.figure(figsize=(10, 4))
    plt.plot(dias, test, label="Real", color="black", linewidth=2)
    plt.plot(dias, p_hw, label="Holt-Winters", color="#1f77b4", linestyle="--")
    plt.plot(dias, p_lstm, label="LSTM", color="#E8820C", linestyle="--")
    plt.title(f"Pronostico 28 dias - {sku} (CA_1)")
    plt.xlabel("dia de test"); plt.ylabel("unidades"); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "series_ejemplo.png"), dpi=130)

    print("\n[4/4] Guardado: metricas_series_hito2.csv, metrics_series_hito2.json,")
    print("      modelo_series.pt, series_comparacion.png, series_ejemplo.png")


if __name__ == "__main__":
    main()
