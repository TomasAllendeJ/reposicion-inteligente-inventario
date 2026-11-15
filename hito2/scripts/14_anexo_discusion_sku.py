# -*- coding: utf-8 -*-
"""Agrega al informe la discusion por SKU (modelo simple vs LSTM) sin regenerar el resto."""
import os
from docx import Document
from docx.shared import Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(BASE, "Informe_Hito2.docx")
NAVY = RGBColor(0x0F, 0x24, 0x44); TEAL = RGBColor(0x2A, 0x9D, 0x8F)

doc = Document(DOC)

# --- separador / titulo ---
doc.add_page_break()
h = doc.add_paragraph(); r = h.add_run("Discusión por SKU: ¿cuándo conviene el modelo simple?")
r.bold = True; r.font.size = Pt(15); r.font.color.rgb = NAVY

p = doc.add_paragraph()
p.add_run("De los 20 SKU, el enfoque de Deep Learning (LSTM/GRU) logra el menor MAE en 12, "
    "y un modelo simple —media móvil o naive— o clásico —Holt-Winters— en 8. La conclusión no es "
    "elegir un único modelo, sino un esquema campeón-retador por SKU: se entrena cada candidato, se "
    "mide su MAE en validación y se elige el menor; ante empate se conserva el simple (Navaja de Occam), "
    "porque es más barato de operar e interpretar.").font.size = Pt(10.5)

p = doc.add_paragraph()
p.add_run("Conviene quedarse con el modelo simple en los SKU de demanda estable o marcadamente "
    "estacional, donde Holt-Winters iguala o supera al LSTM; y en series de bajo volumen o muy planas, "
    "donde basta la media móvil o el naive. En cambio, el LSTM paga su complejidad en los SKU volátiles "
    "o con patrones no lineales (p. ej. FOODS_3_555: 2,77 vs Holt-Winters 4,73; FOODS_3_586: 4,96 vs 7,28; "
    "FOODS_3_120: 10,12 vs 11,56). Caso especial FOODS_3_511: Holt-Winters se dispara (MAE 17,24) por un "
    "quiebre de patrón y el LSTM es mucho más robusto (5,85) — un ejemplo claro de cuándo el modelo clásico "
    "NO sirve.").font.size = Pt(10.5)

cap = doc.add_paragraph(); r = cap.add_run("SKU donde el modelo simple/clásico es el mejor (menor MAE):")
r.bold = True; r.font.size = Pt(10.5); r.font.color.rgb = TEAL

filas = [
    ("SKU", "Mejor modelo (simple)", "MAE", "MAE LSTM", "Por qué"),
    ("FOODS_3_739", "Holt-Winters", "3,35", "6,08", "Fuerte estacionalidad semanal"),
    ("FOODS_3_064", "Holt-Winters", "4,82", "5,64", "Serie estable y regular"),
    ("FOODS_3_099", "Holt-Winters", "4,56", "4,57", "Empate: se prefiere el simple"),
    ("FOODS_2_197", "Holt-Winters", "5,42", "5,81", "Patrón estacional claro"),
    ("FOODS_3_090", "Holt-Winters", "11,48", "13,09", "Alta demanda estacional"),
    ("FOODS_3_499", "Media móvil", "5,61", "6,68", "Demanda plana, poca señal"),
    ("FOODS_3_681", "Naive estacional", "6,43", "6,78", "Repite bien semana a semana"),
    ("FOODS_3_714", "Naive estacional", "5,96", "6,34", "Bajo volumen, estable"),
]
t = doc.add_table(rows=len(filas), cols=5); t.style = "Light Grid Accent 1"
for i, fila in enumerate(filas):
    for j, val in enumerate(fila):
        c = t.cell(i, j); c.text = ""
        rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(9)
        if i == 0: rr.bold = True

p = doc.add_paragraph()
p.add_run("En los 12 SKU restantes el LSTM/GRU obtiene el menor MAE, lo que justifica el modelo de "
    "Deep Learning como opción por defecto, reservando el modelo simple para los 8 SKU anteriores. "
    "Esta política híbrida responde directamente a la observación del Hito 1 sobre en qué casos conviene "
    "el modelo simple.").font.size = Pt(10.5)

doc.save(DOC)
print("OK -> anexo agregado a", DOC)
