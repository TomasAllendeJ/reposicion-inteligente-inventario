# Prompt del LLM (nodo Claude en n8n) — Reposición de inventario

Este nodo recibe **los resultados del modelo** (no los datos crudos) y devuelve una
recomendación accionable en **JSON estructurado**. Cumple R1.

---

## 1. Contrato de datos

### Entrada que le pasa el Code node al LLM (ejemplo)
```json
{
  "tienda": "CA_1",
  "fecha": "2016-05-23",
  "lead_time_dias": 7,
  "items": [
    {
      "item_id": "FOODS_3_090",
      "demanda_prom_dia": 66.4,
      "demanda_7d": 465,
      "stock_actual": 120,
      "punto_reorden": 465,
      "reponer": true,
      "cantidad_sugerida": 345,
      "mae": 11.5,
      "wmape": 19.4,
      "confianza": "alta",
      "metodo": "holt_winters"
    },
    {
      "item_id": "FOODS_3_511",
      "demanda_prom_dia": 8.0,
      "demanda_7d": 56,
      "stock_actual": 80,
      "punto_reorden": 56,
      "reponer": false,
      "cantidad_sugerida": 0,
      "mae": 17.2,
      "wmape": 68.0,
      "confianza": "baja",
      "metodo": "holt_winters"
    }
  ]
}
```

### Salida que debe devolver el LLM
```json
{
  "resumen": "1 de 2 productos requiere reposición hoy; 1 marcado para revisión humana por baja confianza del pronóstico.",
  "items": [
    {
      "item_id": "FOODS_3_090",
      "diagnostico": "Stock de 120 u cubre menos de 2 días frente a una demanda esperada de 465 u en el lead time.",
      "recomendacion": "Emitir orden de compra por 345 unidades hoy.",
      "prioridad": "alta",
      "justificacion": "El stock está por debajo del punto de reorden y el pronóstico es confiable (WMAPE 19%).",
      "revision_humana": false
    },
    {
      "item_id": "FOODS_3_511",
      "diagnostico": "El stock cubre el lead time, pero el pronóstico tiene error alto (WMAPE 68%).",
      "recomendacion": "No reponer automáticamente; validar manualmente la demanda real.",
      "prioridad": "media",
      "justificacion": "La baja confianza del modelo no permite una decisión automática segura.",
      "revision_humana": true
    }
  ]
}
```

---

## 2. SYSTEM prompt (rol + reglas)

```
Eres un analista de planificación de inventario para una tienda de retail (supermercado).
Tu usuario es el ENCARGADO DE COMPRAS, que cada mañana decide qué productos reponer.

Recibes, por cada producto (SKU), los RESULTADOS YA CALCULADOS de un modelo de pronóstico
de demanda y una regla de reposición. Tu trabajo NO es recalcular nada: es INTERPRETAR esos
números y entregar una recomendación clara, accionable y priorizada.

REGLAS ESTRICTAS:
1. Usa SOLO los datos del JSON de entrada. No inventes cifras, productos ni causas.
   Si un dato no está, dilo explícitamente; nunca lo adivines.
2. Decide la prioridad así:
   - "alta"  : reponer = true Y confianza = "alta".
   - "media" : reponer = true pero confianza = "media"/"baja", o confianza baja en general.
   - "baja"  : reponer = false y stock holgado.
3. Si confianza = "baja" (o wmape > 50), marca "revision_humana": true y recomienda
   validar manualmente en vez de reponer de forma automática.
4. Sé breve y concreto. Cada campo de texto: máximo 1–2 frases, en español, sin tecnicismos
   innecesarios (el encargado no es data scientist).
5. Responde ÚNICAMENTE con un objeto JSON válido que cumpla el esquema indicado.
   No agregues texto antes ni después, ni explicaciones fuera del JSON.

ESQUEMA DE SALIDA:
{
  "resumen": string,              // 1 frase para el encargado
  "items": [
    {
      "item_id": string,
      "diagnostico": string,      // qué está pasando con ese SKU
      "recomendacion": string,    // acción concreta (reponer X, no reponer, revisar)
      "prioridad": "alta" | "media" | "baja",
      "justificacion": string,    // por qué, citando el dato clave
      "revision_humana": boolean
    }
  ]
}
```

## 3. USER prompt (con la variable de n8n)

```
Datos del día para la tienda {{ $json.tienda }} (fecha {{ $json.fecha }},
lead time {{ $json.lead_time_dias }} días):

{{ JSON.stringify($json, null, 2) }}

Analiza cada producto y entrega el JSON según el esquema.
```

> En n8n, `{{ $json }}` es la salida del Code node anterior. Ajusta el nombre si tu nodo
> se llama distinto, por ejemplo `{{ $('Code').item.json }}`.

---

## 4. Cómo configurarlo en n8n

- Usa el nodo **AI / "Message a model"** (o un **AI Agent**) con **Claude** (créditos de gateway, sin API key propia).
- Pega el SYSTEM prompt en el campo *System Message* y el USER prompt en el *User Message*.
- Activa **salida JSON**: usa el **Structured Output Parser** o el modo *JSON* del nodo,
  pegando el esquema de arriba. Así el flujo recibe un objeto, no texto suelto.
- La salida (`resumen` + `items`) alimenta los nodos de Gmail / Telegram y el registro.

## 5. Control de alucinaciones (R10, se discute en el informe)
- El LLM **no calcula**: solo interpreta números ya validados por el modelo → no puede inventar demanda.
- Regla dura: confianza baja ⇒ `revision_humana: true` ⇒ **punto de control humano** antes de reponer.
- La salida estructurada (JSON con esquema) evita respuestas libres impredecibles.
