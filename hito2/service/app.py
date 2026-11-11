# -*- coding: utf-8 -*-
"""
Hito 2 - SERVICIO UNIFICADO (FastAPI) con los 3 modelos del sistema.
Es el "servicio Python externo" que n8n llama por HTTP (cumple R2).

Endpoints:
  GET  /                  -> salud (que modelos cargaron)
  POST /predict_imagen    -> (foto)     reconoce el producto (ViT)         [R4]
  POST /pronostico        -> (ventas)   demanda 7 dias con el LSTM         [R3]
  POST /clasificar_reclamo-> (texto)    categoria del reclamo (Transformer)[R5]
  POST /buscar_rag        -> (consulta) reclamos relevantes + contexto RAG [R5]
  GET  /presion_reclamos  -> presion de quiebre por producto (senal negocio)

Arrancar (desde la carpeta hito2):
  .venv/Scripts/python.exe -m uvicorn service.app:app --host 0.0.0.0 --port 8000
Ver y probar: http://localhost:8000/docs
"""
import io
import os
import json
import numpy as np
import joblib
from datetime import date, timedelta, datetime
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights, vit_b_16, ViT_B_16_Weights

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
app = FastAPI(title="Sistema de reposicion - servicio de modelos (Hito 2)")

# ============================================================== IMAGEN (R4)
_img = {"modelo": None, "clases": None, "red": None, "backbone": None}
_tf = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def _cargar_imagen():
    p = os.path.join(OUT, "modelo_productos.joblib")
    if not os.path.exists(p):
        return
    d = joblib.load(p)
    _img["modelo"] = d["modelo"]; _img["clases"] = d["clases"]; _img["backbone"] = d["backbone"]
    if d["backbone"] == "resnet50":
        red = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2); red.fc = nn.Identity()
    elif d["backbone"] == "vit_b_16":
        red = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1); red.heads = nn.Identity()
    else:
        red = None
    if red is not None:
        red.eval()
    _img["red"] = red

def _feat_imagen(img):
    x = _tf(img).unsqueeze(0)
    with torch.no_grad():
        return _img["red"](x).cpu().numpy()

# ============================================================== SERIE (R3)
VENTANA = 28
class RedRNN(nn.Module):
    def __init__(self, tipo="LSTM", n_feat=4, oculto=32):
        super().__init__()
        rnn = nn.LSTM if tipo == "LSTM" else nn.GRU
        self.rnn = rnn(input_size=n_feat, hidden_size=oculto, batch_first=True)
        self.fc = nn.Linear(oculto, 1)
    def forward(self, x):
        o, _ = self.rnn(x)
        return self.fc(o[:, -1, :]).squeeze(-1)

_serie = {"modelo": None}
def _cargar_serie():
    p = os.path.join(OUT, "modelo_series.pt")
    if not os.path.exists(p):
        return
    d = torch.load(p, map_location="cpu", weights_only=False)
    m = RedRNN(tipo="LSTM"); m.load_state_dict(d["LSTM"]); m.eval()
    _serie["modelo"] = m

# wday segun convencion M5 (Sabado=1 ... Viernes=7)
_MAP_WDAY = {5: 1, 6: 2, 0: 3, 1: 4, 2: 5, 3: 6, 4: 7}
def _wday_m5(d):
    return _MAP_WDAY[d.weekday()]
def _feats_dia(venta_esc, wday, snap=0.0):
    ang = 2 * np.pi * (wday / 7.0)
    return [venta_esc, np.sin(ang), np.cos(ang), snap]

# ============================================================== RECLAMOS (R5)
_nlp = {"clf": None, "clases": None, "emb": None, "X": None, "ids": None, "textos": None, "presion": {}}
def _cargar_nlp():
    p = os.path.join(OUT, "modelo_reclamos.joblib")
    if not os.path.exists(p):
        return
    from sentence_transformers import SentenceTransformer
    d = joblib.load(p)
    _nlp["clf"] = d["clf"]; _nlp["clases"] = d["clases"]
    _nlp["emb"] = SentenceTransformer(d["modelo_emb"])
    idx = os.path.join(OUT, "rag_index.npz")
    if os.path.exists(idx):
        z = np.load(idx, allow_pickle=True)
        _nlp["X"] = z["X"]; _nlp["ids"] = z["ids"]; _nlp["textos"] = z["textos"]
    mj = os.path.join(OUT, "metrics_nlp.json")
    if os.path.exists(mj):
        _nlp["presion"] = json.load(open(mj, encoding="utf-8")).get("presion_quiebre_por_producto", {})

# ============================================================== STARTUP
@app.on_event("startup")
def _startup():
    _cargar_imagen(); _cargar_serie(); _cargar_nlp()

@app.get("/")
def salud():
    return {"imagen": _img["modelo"] is not None, "serie": _serie["modelo"] is not None,
            "reclamos": _nlp["clf"] is not None}

# -------------------------------------------------------------- IMAGEN
@app.post("/predict_imagen")
async def predict_imagen(file: UploadFile = File(...)):
    if _img["modelo"] is None:
        return JSONResponse(status_code=503, content={"error": "modelo de imagen no cargado"})
    try:
        img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"imagen invalida: {e}"})
    proba = _img["modelo"].predict_proba(_feat_imagen(img))[0]
    orden = np.argsort(proba)[::-1][:3]
    top3 = [{"producto": _img["clases"][i], "confianza": round(float(proba[i]), 4)} for i in orden]
    return {"producto": top3[0]["producto"], "confianza": top3[0]["confianza"],
            "revision_humana": bool(top3[0]["confianza"] < 0.5), "top3": top3}

# -------------------------------------------------------------- SERIE
class EntradaPronostico(BaseModel):
    ventas: list[float]
    fechas: list[str] | None = None   # ["YYYY-MM-DD", ...] alineadas con ventas
    horizonte: int = 7

def _forecast(ventas_list, fechas_list, horizonte):
    """Pronostico recursivo de `horizonte` dias con el LSTM. Funcion reutilizable."""
    ventas = np.array(ventas_list, dtype=float)
    if len(ventas) < 2:
        return None
    if fechas_list:
        fechas = [date.fromisoformat(s) for s in fechas_list]
        wday_hist = [_wday_m5(f) for f in fechas]
        ultima = fechas[-1]
    else:
        wday_hist = [((i % 7) + 1) for i in range(len(ventas))]
        ultima = date.today()
    mu, sd = ventas.mean(), ventas.std()
    sd = sd if sd > 1e-6 else 1.0
    ventas_esc = (ventas - mu) / sd
    win = [_feats_dia(ventas_esc[i], wday_hist[i]) for i in range(len(ventas))][-VENTANA:]
    while len(win) < VENTANA:
        win.insert(0, win[0])
    preds = []
    m = _serie["modelo"]
    with torch.no_grad():
        for k in range(1, horizonte + 1):
            x = torch.tensor([win], dtype=torch.float32)
            p_esc = float(m(x).item())
            preds.append(round(max(0.0, p_esc * sd + mu), 2))
            dia = ultima + timedelta(days=k)
            win = win[1:] + [_feats_dia(p_esc, _wday_m5(dia))]
    return {"pronostico": preds, "demanda_total": round(float(sum(preds)), 1),
            "demanda_prom_dia": round(float(np.mean(preds)), 2), "modelo": "LSTM"}


@app.post("/pronostico")
def pronostico(e: EntradaPronostico):
    if _serie["modelo"] is None:
        return JSONResponse(status_code=503, content={"error": "modelo de serie no cargado"})
    r = _forecast(e.ventas, e.fechas, e.horizonte)
    if r is None:
        return JSONResponse(status_code=400, content={"error": "muy pocos datos"})
    return r


class SerieSKU(BaseModel):
    ventas: list[float]
    fechas: list[str] | None = None

class EntradaBatch(BaseModel):
    series: dict[str, SerieSKU]   # {item_id: {ventas, fechas}}
    horizonte: int = 7

@app.post("/pronostico_batch")
def pronostico_batch(e: EntradaBatch):
    """Pronostica TODOS los SKU de una sola llamada (lo que usa n8n)."""
    if _serie["modelo"] is None:
        return JSONResponse(status_code=503, content={"error": "modelo de serie no cargado"})
    salida = {}
    for sku, s in e.series.items():
        r = _forecast(s.ventas, s.fechas, e.horizonte)
        if r is not None:
            salida[sku] = r
    return {"pronosticos": salida, "n_sku": len(salida)}

# -------------------------------------------------------------- RECLAMOS
class EntradaTexto(BaseModel):
    texto: str
class EntradaConsulta(BaseModel):
    consulta: str
    k: int = 3

@app.post("/clasificar_reclamo")
def clasificar_reclamo(e: EntradaTexto):
    if _nlp["clf"] is None:
        return JSONResponse(status_code=503, content={"error": "modelo de reclamos no cargado"})
    v = _nlp["emb"].encode([e.texto], normalize_embeddings=True)
    proba = _nlp["clf"].predict_proba(v)[0]
    i = int(np.argmax(proba))
    return {"categoria": _nlp["clases"][i], "confianza": round(float(proba[i]), 4)}

@app.post("/buscar_rag")
def buscar_rag(e: EntradaConsulta):
    if _nlp["X"] is None:
        return JSONResponse(status_code=503, content={"error": "indice RAG no cargado"})
    q = _nlp["emb"].encode([e.consulta], normalize_embeddings=True)[0]
    sims = _nlp["X"] @ q
    top = np.argsort(sims)[::-1][:e.k]
    resultados = [{"id": str(_nlp["ids"][i]), "texto": str(_nlp["textos"][i]),
                   "score": round(float(sims[i]), 3)} for i in top]
    contexto = "\n".join(f"[{r['id']}] {r['texto']}" for r in resultados)
    return {"consulta": e.consulta, "resultados": resultados, "contexto_para_llm": contexto}

@app.get("/presion_reclamos")
def presion_reclamos():
    return {"presion_quiebre_por_producto": _nlp["presion"]}

# ============================================================== TABLERO EN VIVO
# Guarda la ultima corrida del workflow y sirve el tablero HTML.
TAB_FILE = os.path.join(OUT, "tablero_live.json")
HTML_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tablero", "live.html")

def _leer_corrida():
    if os.path.exists(TAB_FILE):
        try:
            return json.load(open(TAB_FILE, encoding="utf-8"))
        except Exception:
            return None
    return None

@app.post("/tablero/datos")
async def tablero_guardar(payload: dict):
    """n8n llama aqui al final de cada corrida con la recomendacion."""
    payload["generado_en"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(TAB_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"ok": True, "generado_en": payload["generado_en"]}

@app.get("/tablero/datos")
def tablero_datos():
    """El tablero lee la ultima corrida desde aqui."""
    c = _leer_corrida()
    return {"corrida": c}

@app.get("/tablero", response_class=HTMLResponse)
def tablero():
    if os.path.exists(HTML_FILE):
        return HTMLResponse(open(HTML_FILE, encoding="utf-8").read())
    return HTMLResponse("<h1>Falta tablero/live.html</h1>", status_code=404)
