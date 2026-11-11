# -*- coding: utf-8 -*-
"""
Hito 2 - Consolida los datos reales para el TABLERO (R9).
Genera outputs/tablero_datos.json con:
  - KPIs del sistema
  - metricas de los 3 modelos (serie, imagen, NLP)
  - presion de reclamos por producto
  - tabla de reposicion de los 20 SKU (pronostico LSTM + regla de reorden)

Uso:
  python 07_tablero_datos.py <csv_ventas> <out_dir>
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import date, timedelta
import torch
import torch.nn as nn

H = 7
VENTANA = 28
STOCK = {"FOODS_2_019": 41, "FOODS_2_197": 107, "FOODS_3_064": 213, "FOODS_3_080": 225,
         "FOODS_3_090": 159, "FOODS_3_099": 83, "FOODS_3_120": 378, "FOODS_3_252": 465,
         "FOODS_3_282": 56, "FOODS_3_295": 132, "FOODS_3_499": 95, "FOODS_3_501": 283,
         "FOODS_3_511": 74, "FOODS_3_555": 109, "FOODS_3_586": 291, "FOODS_3_587": 420,
         "FOODS_3_681": 66, "FOODS_3_714": 94, "FOODS_3_739": 80, "FOODS_3_741": 183}
_MAP = {5: 1, 6: 2, 0: 3, 1: 4, 2: 5, 3: 6, 4: 7}


class RedRNN(nn.Module):
    def __init__(self, tipo="LSTM", n_feat=4, oculto=32):
        super().__init__()
        rnn = nn.LSTM if tipo == "LSTM" else nn.GRU
        self.rnn = rnn(input_size=n_feat, hidden_size=oculto, batch_first=True)
        self.fc = nn.Linear(oculto, 1)
    def forward(self, x):
        o, _ = self.rnn(x)
        return self.fc(o[:, -1, :]).squeeze(-1)


def feats(v, wday, snap=0.0):
    ang = 2 * np.pi * (wday / 7.0)
    return [v, np.sin(ang), np.cos(ang), snap]


def pronosticar(modelo, ventas, fechas):
    mu, sd = ventas.mean(), ventas.std()
    sd = sd if sd > 1e-6 else 1.0
    esc = (ventas - mu) / sd
    wday = [_MAP[f.weekday()] for f in fechas]
    win = [feats(esc[i], wday[i]) for i in range(len(ventas))][-VENTANA:]
    while len(win) < VENTANA:
        win.insert(0, win[0])
    preds = []
    ultima = fechas[-1]
    with torch.no_grad():
        for k in range(1, H + 1):
            x = torch.tensor([win], dtype=torch.float32)
            pe = float(modelo(x).item())
            preds.append(max(0.0, pe * sd + mu))
            d = ultima + timedelta(days=k)
            win = win[1:] + [feats(pe, _MAP[d.weekday()])]
    return preds


def main():
    csv_in = sys.argv[1]
    out_dir = sys.argv[2]
    df = pd.read_csv(csv_in, parse_dates=["date"])

    d = torch.load(os.path.join(out_dir, "modelo_series.pt"), map_location="cpu", weights_only=False)
    modelo = RedRNN("LSTM"); modelo.load_state_dict(d["LSTM"]); modelo.eval()

    # Tabla de reposicion por SKU
    repos = []
    ejemplo = None
    for sku in sorted(df["item_id"].unique()):
        s = df[df["item_id"] == sku].sort_values("date").tail(90)
        ventas = s["sales"].to_numpy(float)
        fechas = [x.date() for x in s["date"]]
        pron = pronosticar(modelo, ventas, fechas)
        demanda7 = round(float(sum(pron)), 1)
        stock = int(STOCK.get(sku, int(round(float(np.mean(pron)) * 5))))
        punto = demanda7
        reponer = bool(stock < punto)
        repos.append({
            "item_id": sku, "demanda_7d": demanda7, "demanda_prom_dia": round(demanda7 / H, 1),
            "stock_actual": stock, "punto_reorden": round(float(punto), 1), "reponer": reponer,
            "cantidad_sugerida": max(0, int(round(punto - stock))),
            "prioridad": ("alta" if reponer and demanda7 / H >= 20 else ("media" if reponer else "baja")),
        })
        if sku == "FOODS_3_064":
            ejemplo = {"sku": sku, "pronostico": [round(float(x), 1) for x in pron],
                       "historia": [round(float(x), 1) for x in ventas[-21:].tolist()]}

    # Cargar metricas ya calculadas
    def carga(p, default):
        return json.load(open(os.path.join(out_dir, p), encoding="utf-8")) if os.path.exists(os.path.join(out_dir, p)) else default

    m_serie = carga("metrics_series_hito2.json", {})
    m_img = carga("metrics_r4.json", {})
    m_nlp = carga("metrics_nlp.json", {})

    n_reponer = sum(1 for r in repos if r["reponer"])
    n_alta = sum(1 for r in repos if r["prioridad"] == "alta")

    tablero = {
        "generado": date.today().isoformat(),
        "kpis": {
            "n_sku": len(repos), "n_reponer": n_reponer, "n_prioridad_alta": n_alta,
            "mae_lstm": m_serie.get("mae_promedio", {}).get("MAE_LSTM"),
            "mae_holtwinters": m_serie.get("mae_promedio", {}).get("MAE_holtwinters"),
            "acc_vit": next((r["accuracy"] for r in m_img.get("resultados", []) if r["backbone"] == "vit_b_16"), None),
            "acc_nlp": m_nlp.get("clasificacion", {}).get("transformer_embeddings", {}).get("accuracy"),
        },
        "serie": {"mae": m_serie.get("mae_promedio", {}), "ejemplo": ejemplo,
                  "gana_dl_vs_hw": m_serie.get("gana_dl_vs_hw")},
        "imagen": m_img.get("resultados", []),
        "nlp": {"clasificacion": m_nlp.get("clasificacion", {}),
                "presion": m_nlp.get("presion_quiebre_por_producto", {})},
        "reposicion": repos,
    }
    with open(os.path.join(out_dir, "tablero_datos.json"), "w", encoding="utf-8") as f:
        json.dump(tablero, f, ensure_ascii=False, indent=2)
    print("Guardado tablero_datos.json")
    print(f"  {len(repos)} SKU | {n_reponer} a reponer | {n_alta} prioridad alta")
    print(f"  MAE LSTM {tablero['kpis']['mae_lstm']} | ViT {tablero['kpis']['acc_vit']} | NLP {tablero['kpis']['acc_nlp']}")


if __name__ == "__main__":
    main()
