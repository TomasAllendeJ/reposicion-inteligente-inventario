# Hito 2 — Sistema integrado de reposición de inventario

Evolución del Hito 1 a un **sistema integrado** que combina tres modelos de IA
(serie temporal, imágenes y texto), orquestados en **n8n**, con **control humano**,
**notificaciones** y un **tablero** en HTML. Caso: retail (tienda CA_1, datos reales
M5 Walmart + reclamos de clientes simulados).

> 📄 Para una explicación en palabras simples de todo el proyecto y cada concepto,
> ver **`Explicacion_Hito2.pdf`**. Para el ROI y los riesgos, **`Negocio_y_Riesgos.md`**.

## Arquitectura

```
Disparador → Leer ventas (Sheets) → Preparar series
   → [HTTP] Pronóstico LSTM (servicio)   \
   → [HTTP] Presión de reclamos (NLP)     → Combinar → Decidir reposición
   → Claude (recomendación integrada JSON)
   → Control humano (aprobación por Telegram)
   → Gmail + Telegram + Registro (Sheets) + actualizar Tablero
```

Los modelos pesados corren **fuera de n8n**, en un **servicio FastAPI** (`service/app.py`)
que n8n llama por HTTP (a través de un túnel ngrok, porque n8n es cloud).

## Los tres modelos (cada uno comparado con su alternativa simple)

| Componente | Modelo | Baseline | Resultado |
|---|---|---|---|
| **Serie temporal** (R3) | LSTM / GRU (PyTorch) | Holt-Winters, media móvil | **LSTM MAE 6,46** vs Holt-Winters 7,34 (gana en 14/20 SKU) |
| **Imágenes** (R4) | ViT (Vision Transformer) | histograma de color | **ViT 0,87** vs ResNet 0,85 vs baseline 0,32 |
| **Texto / NLP** (R5) | Transformer (embeddings) + RAG | reglas por palabra clave | **Transformer 0,96** vs reglas 0,89 |

Métricas en `resultados/` (`metrics_*.json`) y gráficos (`*.png`).

## Estructura

```
hito2/
├── scripts/
│   ├── 01_extract_features.py   # imágenes: extrae características (ResNet/ViT)
│   ├── 02_train_compare.py      # imágenes: baseline vs CNN vs ViT
│   ├── 04_lstm_vs_holtwinters.py# serie: LSTM/GRU vs Holt-Winters
│   ├── 05_gen_reclamos.py       # genera reclamos simulados (PDF+CSV)
│   ├── 06_nlp_reclamos.py       # NLP: clasificación + RAG + presión por producto
│   ├── 07_tablero_datos.py      # consolida datos del tablero
│   ├── 08_roi.py                # evaluación de negocio (ROI)
│   └── 09_explicativo.py        # genera el PDF explicativo
├── service/app.py               # servicio FastAPI con los 3 modelos + tablero
├── tablero/
│   ├── index.html               # tablero estático (publicable)
│   └── live.html                # tablero en vivo (servido por el servicio)
├── n8n/workflow_hito2_sin_credenciales.json
├── reclamos/                    # set simulado de reclamos (PDF + CSV)
├── resultados/                  # métricas y gráficos
├── requirements.txt
├── Negocio_y_Riesgos.md         # ROI + riesgos (R10)
└── Explicacion_Hito2.pdf        # guía en simple
```

## Datos
- **Serie temporal / reposición:** M5 Forecasting (Walmart), tienda CA_1, 20 SKU.
- **Imágenes:** Grocery Store Dataset (Klasson et al.), 43 clases.
- **Reclamos:** set **simulado** (supuesto documentado), generado con `05_gen_reclamos.py`.
- El stock actual se simula con supuestos explícitos.

## Cómo correr

```bash
# 1) Entorno e instalación (torch CPU)
python -m venv .venv
.venv/Scripts/python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2) Modelos (ver cada script; requieren descargar los datasets)
.venv/Scripts/python.exe scripts/01_extract_features.py <dataset> outputs coarse
.venv/Scripts/python.exe scripts/02_train_compare.py outputs
.venv/Scripts/python.exe scripts/04_lstm_vs_holtwinters.py <ventas.csv> outputs
.venv/Scripts/python.exe scripts/05_gen_reclamos.py reclamos
.venv/Scripts/python.exe scripts/06_nlp_reclamos.py reclamos outputs

# 3) Servicio (expone los 3 modelos + el tablero)
.venv/Scripts/python.exe -m uvicorn service.app:app --host 0.0.0.0 --port 8000
#   Tablero en vivo:  http://localhost:8000/tablero
#   Docs/pruebas:     http://localhost:8000/docs

# 4) Túnel para que n8n (cloud) alcance el servicio
ngrok http 8000
#   Pega la URL de ngrok en los 3 nodos HTTP del flujo n8n.
```

## Flujo n8n
Importar `n8n/workflow_hito2_sin_credenciales.json`, conectar credenciales propias
(Gmail, Telegram, Google Sheets), poner la URL de ngrok en los nodos HTTP y pulsar
"Ejecutar (demo)". Claude usa el **gateway de n8n** (sin API key).

## Control humano y ética (R10)
Antes de enviar nada, el flujo pide **aprobación por Telegram**. El LLM recibe solo
resultados ya calculados (no datos crudos), responde en **JSON estructurado** y usa
**RAG** para citar la fuente de los reclamos. Si un dato es dudoso, marca
`revision_humana`. ROI y riesgos en `Negocio_y_Riesgos.md`.
