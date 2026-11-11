# Evaluación de negocio y análisis de riesgos (R10)

Sistema inteligente de reposición de inventario — Tienda CA_1. Hito 2.

## 1. Caso de negocio

- **Usuario / quién decide:** el **encargado de compras** de la tienda, que cada mañana decide qué productos reponer.
- **Decisión recurrente:** por cada SKU, reponer o no, cuánto y con qué prioridad.
- **Indicador de negocio:** quiebres de stock evitados y capital inmovilizado reducido.
- **Valor del sistema:** convierte una decisión manual "a ojo" en una recomendación diaria, priorizada y con control humano, apoyada en tres modelos (pronóstico, imágenes, texto).

## 2. Estimación de ROI (CLP/mes)

> **Importante:** es una **estimación con supuestos explícitos y conservadores**, no datos financieros reales de la tienda. El objetivo es mostrar el orden de magnitud y el método, no una cifra exacta.

**Supuestos:**

| Supuesto | Valor |
|---|---|
| SKU gestionados | 20 |
| Demanda promedio diaria por SKU (dato real) | 24,8 u |
| Precio promedio / margen | $1.500 / 25% ($375 por u) |
| Tasa de quiebre sin sistema → con sistema | 8% → 3% de SKU-días |
| Venta perdida en un día de quiebre | 50% de la demanda |
| Horas/día del encargado decidiendo a mano | 1 h ($4.000/h) |

**Resultado:**

| Concepto | CLP/mes |
|---|---|
| Beneficio — ventas recuperadas (quiebres evitados) | 139.607 |
| Beneficio — horas ahorradas (automatización) | 120.000 |
| **Beneficio total** | **259.607** |
| Costo — hosting del servicio | 10.000 |
| Costo — mantención (2 h/mes) | 16.000 |
| Costo — IA (gateway de n8n) | 0 (incluido en créditos) |
| **Costo total de operar** | **26.000** |
| **Neto mensual** | **233.607** |
| **ROI mensual** | **≈ 9×** |
| **Neto anual aproximado** | **≈ $2,8 millones** |

**Lectura honesta:** el ROI es alto en parte porque el costo de IA está **subsidiado por los créditos de gateway de n8n** (sin API key propia). En un escenario con API pagada el costo subiría, pero el beneficio (quiebres evitados + horas) lo mantiene positivo. Incluso reduciendo a la mitad el supuesto de quiebres evitados, el sistema sigue siendo rentable (neto ≈ $164.000/mes).

*(Reproducible: `scripts/08_roi.py` → `outputs/roi.json`.)*

## 3. Riesgos del sistema y controles

| Riesgo | Mitigación / control |
|---|---|
| **Error del modelo de pronóstico** (promociones, feriados, eventos no modelados) | Se compara contra baselines (Navaja de Occam); se mide el error (MAE/WMAPE); si la confianza es baja → marca **revisión humana** y no repone automático. |
| **Alucinaciones del LLM** (Claude inventa cifras o productos) | Claude recibe **solo los resultados ya calculados** (no datos crudos), responde en **JSON estructurado**, y el **RAG cita la fuente** de los reclamos. Regla: dato dudoso → `revision_humana=true`. |
| **Acción incorrecta automática** (pedir de más/de menos) | **Punto de control humano:** antes de notificar, el flujo pide **aprobación por Telegram**; nada crítico se ejecuta sin un "Aprobar". |
| **Datos sensibles** (ventas, reclamos de clientes) | El flujo exportado va **sin credenciales**; los reclamos son **simulados** (sin datos personales reales); no se almacena PII. |
| **Dependencia del servicio local / túnel** | Limitación documentada; en producción el servicio se desplegaría en un host estable (Hugging Face Space, nube). |

## 4. Sesgos y limitaciones

- **Sesgo de historia:** el pronóstico funciona mejor en SKU con historia larga y estable; productos nuevos o intermitentes tienen más error.
- **Stock simulado:** el stock actual se simula con supuestos; en producción vendría del sistema de inventario real.
- **Reclamos simulados:** la señal de presión de reclamos usa un set generado; con reclamos reales podría cambiar la priorización.
- **Mapeo reclamos↔SKU:** los reclamos usan nombres de producto genéricos; en producción se mapearían a los SKU exactos.

## 5. Punto de control humano (resumen)

El sistema está diseñado para **asistir, no reemplazar** al encargado:
1. Los modelos calculan y proponen.
2. Claude redacta una recomendación clara y priorizada.
3. El encargado **aprueba o rechaza por Telegram**.
4. Solo tras la aprobación se envían las órdenes y se registra la decisión.
