# Sistema Inteligente de Reposicion de Inventario (Retail)

Proyecto Final - IA Generativa para la Gestion Industrial. Un sistema que, cada dia, lee las
ventas, **pronostica la demanda** de cada producto, decide **que reponer y cuanto**, y le pide a
**Claude** una recomendacion priorizada que entrega por **Gmail y Telegram**, con registro en
Google Sheets.

> Caso: tienda de retail (datos reales M5 Walmart, tienda CA_1, 20 SKU de mayor venta).

## Contenido del repositorio

- **Hito 1** (este README, carpeta `scripts/` y `n8n/`): flujo base — pronostico de demanda
  (Holt-Winters) + regla de reposicion + Claude + notificaciones.
- **Hito 2** (carpeta [`hito2/`](hito2/)): sistema **integrado** que agrega tres modelos de IA
  comparados con su alternativa simple — **serie temporal (LSTM)**, **imagenes (ViT)** y
  **texto/NLP (Transformer + RAG)** — orquestados en n8n con **control humano**, un **tablero**
  en HTML y evaluacion de **negocio (ROI)**. Ver [`hito2/README.md`](hito2/README.md).

## Arquitectura

```
Disparador diario -> Leer ventas (Google Sheets) -> Modelo (Python) ->
Claude (recomendacion JSON) -> Correo (Gmail) + Telegram + Registro (Sheets)
```

- **Datos / ingesta:** ventas diarias por SKU, leidas desde Google Sheets.
- **Python:** limpieza + modelo de serie temporal (Holt-Winters) + regla de reposicion.
- **LLM (Claude):** interpreta los resultados y entrega un JSON con diagnostico, recomendacion,
  prioridad, justificacion y una marca de *revision humana* cuando la confianza es baja.
- **Accion:** correo, mensaje y registro historico.

## Estructura del repositorio

```
.
|-- scripts/
|   |-- 01_limpieza.py      # limpieza y transformacion de los datos M5
|   |-- forecast_core.py    # modelo (media movil, Holt-Winters auto) en Python puro
|   `-- 02_modelo.py        # validacion, metricas (MAE) y graficos
|-- n8n/
|   |-- workflow_export.json  # flujo de n8n (sin credenciales)
|   |-- code_node_python.py   # codigo del nodo Code del flujo
|   |-- code_node_formato.js  # nodo que arma los mensajes
|   `-- prompt_llm.md         # prompt del LLM + esquema de salida
|-- requirements.txt
`-- README.md
```

## Datos

Se usan datos publicos del dataset **M5 Forecasting (Walmart)** de Kaggle. Por su tamano y licencia,
los datos crudos **no se incluyen** en el repositorio. Para reproducir:

1. Descargar `sales_train_evaluation.csv`, `calendar.csv` y `sell_prices.csv` de la competencia
   *M5 Forecasting - Accuracy* en Kaggle.
2. Colocarlos en una carpeta `m5_data/`.
3. Ejecutar la limpieza y el modelo (ver abajo).

## Como correr (parte Python)

```bash
pip install -r requirements.txt
python scripts/01_limpieza.py m5_data clean CA_1 20
python scripts/02_modelo.py clean/ca_1_top20_long.csv outputs
```

## Flujo en n8n

Importar `n8n/workflow_export.json` en n8n (Import from File). Luego conectar las credenciales
propias (Google Sheets, Gmail, Telegram) y seleccionar las planillas. El modelo (Claude) usa el
nodo de Anthropic via gateway.

## Resultados del modelo

Comparacion sobre 28 dias de prueba (MAE promedio):

| Metodo | MAE |
|---|---|
| Media movil 7d (baseline) | 7,91 |
| Naive estacional (baseline) | 8,06 |
| **Holt-Winters (modelo)** | **7,34** (gana al baseline en 10/20 SKU) |
| Holt-Winters statsmodels (referencia) | 6,49 |

## Declaracion del uso de IA

En este proyecto se utilizo un asistente de IA (**Claude**) como apoyo para escribir y comentar el
codigo, redactar textos y acelerar el desarrollo. El autor entiende y puede explicar cada parte del
codigo y del flujo. Ademas, el sistema usa un LLM (Claude) en tiempo de ejecucion para generar las
recomendaciones de reposicion.

## Autor

Tomas Allende - 2026
