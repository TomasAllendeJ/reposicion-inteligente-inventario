# -*- coding: utf-8 -*-
"""Presentacion del Hito 2 (defensa), diseno profesional (python-pptx)."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Presentacion_Hito2.pptx")
IMG = os.path.join(BASE, "outputs")

NAVY = RGBColor(0x0F, 0x24, 0x44); NAVY2 = RGBColor(0x1B, 0x3A, 0x63)
TEAL = RGBColor(0x2A, 0x9D, 0x8F); ORANGE = RGBColor(0xE8, 0x82, 0x0C)
INK = RGBColor(0x2B, 0x2B, 0x2B); GREY = RGBColor(0x5B, 0x66, 0x72)
LIGHT = RGBColor(0xF3, 0xF5, 0xF8); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLUETX = RGBColor(0xBF, 0xD0, 0xE2)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height; BLANK = prs.slide_layouts[6]

def slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = bg; r.line.fill.background(); r.shadow.inherit = False
    return s

def box(s, x, y, w, h, color, line=None, radius=0.08):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    sp = s.shapes.add_shape(shape, x, y, w, h)
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    if line: sp.line.color.rgb = line; sp.line.width = Pt(1)
    else: sp.line.fill.background()
    sp.shadow.inherit = False
    try:
        if radius: sp.adjustments[0] = radius
    except Exception: pass
    return sp

def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=4):
    tb = s.shapes.add_textbox(x, y, w, h); tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    if isinstance(runs, str): runs = [(runs, 18, INK, False)]
    first = True
    for item in runs:
        txt_, size, color, bold = item[:4]
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space); first = False
        r = p.add_run(); r.text = txt_; r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color; r.font.name = "Calibri"
    return tb

def bullets(s, x, y, w, h, items, size=17, color=INK, gap=9):
    tb = s.shapes.add_textbox(x, y, w, h); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(gap)
        rb = p.add_run(); rb.text = "■  "; rb.font.size = Pt(size-3); rb.font.color.rgb = TEAL
        r = p.add_run(); r.text = it; r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = "Calibri"
    return tb

def header(s, num, title, sub=None):
    box(s, 0, 0, Inches(0.22), SH, TEAL, radius=0)
    box(s, Inches(0.6), Inches(0.5), Inches(0.72), Inches(0.72), NAVY, radius=0.18)
    text(s, Inches(0.6), Inches(0.5), Inches(0.72), Inches(0.72), [(str(num), 26, WHITE, True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(1.5), Inches(0.5), SW - Inches(2), Inches(0.75), [(title, 27, NAVY, True)], anchor=MSO_ANCHOR.MIDDLE)
    if sub:
        text(s, Inches(1.5), Inches(1.2), SW - Inches(2), Inches(0.35), [(sub, 13, TEAL, True)])
    box(s, Inches(0.6), Inches(1.64), SW - Inches(1.2), Pt(2), LIGHT, radius=0)

def kpi(s, x, y, w, num, label, color=TEAL):
    box(s, x, y, w, Inches(1.7), WHITE, line=LIGHT, radius=0.08)
    box(s, x, y, w, Inches(0.12), color, radius=0)
    text(s, x, y + Inches(0.25), w, Inches(0.9), [(num, 38, NAVY, True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x, y + Inches(1.12), w, Inches(0.5), [(label, 12.5, GREY, False)], align=PP_ALIGN.CENTER)

def mesa(s, rows, x, y, w, h, hl_row=None):
    tb = s.shapes.add_table(len(rows), len(rows[0]), x, y, w, h).table
    for ri, fila in enumerate(rows):
        for ci, val in enumerate(fila):
            cell = tb.cell(ri, ci); cell.text = val
            pr = cell.text_frame.paragraphs[0].runs[0]; pr.font.size = Pt(13); pr.font.name = "Calibri"
            if ri == 0:
                pr.font.bold = True; pr.font.color.rgb = WHITE; cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
            else:
                hl = (ri == hl_row); cell.fill.solid(); cell.fill.fore_color.rgb = (RGBColor(0xDE,0xF2,0xEF) if hl else WHITE)
                pr.font.bold = hl; pr.font.color.rgb = (TEAL if hl else INK)
    return tb

# 1. Portada
s = slide(NAVY)
box(s, 0, 0, Inches(0.35), SH, TEAL, radius=0)
box(s, Inches(0.9), Inches(2.0), Inches(1.4), Inches(0.14), TEAL, radius=0)
text(s, Inches(0.9), Inches(2.25), SW - Inches(1.8), Inches(1.9),
     [("Sistema Inteligente de", 32, WHITE, True), ("Reposición de Inventario", 40, WHITE, True)], space=2)
text(s, Inches(0.9), Inches(4.35), SW - Inches(1.8), Inches(0.9),
     [("Hito 2 — Sistema integrado  ·  IA Generativa para la Gestión Industrial", 18, BLUETX, False),
      ("Caso Retail  ·  Datos reales M5 Walmart (tienda CA_1) + reclamos de clientes", 14, RGBColor(0x9F,0xB4,0xCB), False)], space=5)
text(s, Inches(0.9), Inches(6.05), SW - Inches(1.8), Inches(0.5), [("Tomás Allende   |   Noviembre 2026", 14, WHITE, False)])

# 2. La idea
s = slide(LIGHT); box(s, 0, 0, Inches(0.22), SH, TEAL, radius=0)
text(s, Inches(1.0), Inches(1.0), SW - Inches(2), Inches(0.6), [("La idea en una frase", 16, TEAL, True)])
text(s, Inches(1.0), Inches(1.7), SW - Inches(2), Inches(2.6),
     [("El sistema decide cada día qué reponer. Le dimos tres sentidos: ojos (ver productos), "
       "memoria (predecir ventas) y lectura (entender reclamos). Claude los integra y recomienda; "
       "tú apruebas antes de actuar.", 28, NAVY, True)], space=6)
etapas = ["Datos", "3 modelos de IA", "Claude integra", "Tú apruebas", "Acción"]
x = Inches(0.8); y = Inches(5.2); w = Inches(2.1)
for i, e in enumerate(etapas):
    box(s, x, y, w, Inches(0.9), WHITE, line=RGBColor(0xD6,0xDE,0xE8), radius=0.12)
    text(s, x, y, w, Inches(0.9), [(e, 14, NAVY, True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 4:
        text(s, x + w, y, Inches(0.45), Inches(0.9), [("→", 20, TEAL, True)], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    x += w + Inches(0.45)

# 3. Problema
s = slide(); header(s, 1, "El problema y el usuario")
bullets(s, Inches(0.8), Inches(2.0), SW - Inches(1.5), Inches(4.6),
    ["La tienda pierde ventas por quiebres de stock e inmoviliza capital por sobre-stock.",
     "Hoy la reposición se decide 'a ojo', sin aprovechar los datos.",
     "Usuario: el ENCARGADO DE COMPRAS, que cada mañana decide qué reponer, cuánto y con qué prioridad.",
     "Indicador de negocio: quiebres evitados y capital inmovilizado reducido.",
     "El sistema entrega una recomendación diaria, priorizada y con control humano."], size=19)

# 4. Arquitectura
s = slide(); header(s, 2, "Arquitectura del sistema integrado")
diag = os.path.join(IMG, "diagrama_hito2.png")
if os.path.exists(diag): s.shapes.add_picture(diag, Inches(0.8), Inches(2.0), width=Inches(11.7))
text(s, Inches(0.8), Inches(5.9), Inches(11.7), Inches(1.2),
     [("n8n orquesta: lee ventas → llama a los modelos (servicio Python por HTTP) → Claude integra "
       "→ control humano por Telegram → Gmail + Telegram + registro + tablero.", 14, GREY, False)])

# 5. Serie temporal
s = slide(); header(s, 3, "Modelo 1 — Serie temporal (LSTM)", "Deep Learning vs. clásico (R3)")
bullets(s, Inches(0.8), Inches(2.0), Inches(6.2), Inches(4.3),
    ["Pronóstico de demanda a 7 días por producto.",
     "Comparado con Holt-Winters (clásico) y baselines, mismo protocolo (MAE en 28 días).",
     "El LSTM usa la venta + día de la semana + días SNAP.",
     "Gana al clásico en 14 de 20 productos."], size=16)
mesa(s, [["Método", "MAE"], ["Media móvil", "7,91"], ["Naive", "8,06"],
         ["Holt-Winters", "7,34"], ["GRU", "6,58"], ["LSTM", "6,46"]], Inches(7.2), Inches(2.0), Inches(2.6), Inches(2.9), hl_row=5)
sc = os.path.join(IMG, "series_comparacion.png")
if os.path.exists(sc): s.shapes.add_picture(sc, Inches(10.0), Inches(2.0), width=Inches(2.9))

# 6. Imagenes
s = slide(); header(s, 4, "Modelo 2 — Imágenes (ViT)", "Reconocimiento de productos (R4)")
bullets(s, Inches(0.8), Inches(2.0), Inches(6.2), Inches(4.3),
    ["Modelos preentrenados como extractores de características + clasificador simple.",
     "Baseline simple: histograma de color (Navaja de Occam).",
     "El Vision Transformer (ViT) gana a la CNN (ResNet50).",
     "Se expone como endpoint para reconocer un producto desde una foto, en vivo."], size=16)
ic = os.path.join(IMG, "r4_comparacion.png")
if os.path.exists(ic): s.shapes.add_picture(ic, Inches(7.3), Inches(2.2), width=Inches(5.3))

# 7. NLP
s = slide(); header(s, 5, "Modelo 3 — Texto / NLP + RAG", "Reclamos de clientes (R5)")
bullets(s, Inches(0.8), Inches(2.0), SW - Inches(1.5), Inches(4.3),
    ["Un Transformer (embeddings) clasifica los reclamos por categoría: 96% vs 89% de las reglas simples.",
     "Embeddings = convertir frases en números que capturan el significado (búsqueda por sentido).",
     "RAG: ante una consulta, busca los reclamos relevantes y Claude responde citando la fuente (anti-alucinación).",
     "Se obtiene la 'presión de reclamos de quiebre' por producto, que sube la prioridad de reposición."], size=18)

# 8. LLM + control humano
s = slide(); header(s, 6, "IA integrada y control humano", "R1 + R6 + R10 + R11")
bullets(s, Inches(0.8), Inches(2.0), SW - Inches(1.5), Inches(4.3),
    ["Claude (vía gateway, sin API key) recibe los resultados ya calculados, no los datos crudos.",
     "Combina las tres señales y entrega UNA recomendación integrada en JSON.",
     "Control humano: antes de enviar, pide aprobación por Telegram; si se rechaza, no se envía nada.",
     "Si un dato es dudoso, marca 'revisión humana'.",
     "Notifica por Gmail + Telegram + registro, con el enlace al tablero."], size=18)

# 9. Tablero
s = slide(); header(s, 7, "El tablero (R9)", "Salida en HTML")
bullets(s, Inches(0.8), Inches(2.0), SW - Inches(1.5), Inches(4.3),
    ["Dos versiones: una publicada (estática, para mostrar) y una en vivo (servida por el servicio).",
     "El tablero en vivo se actualiza con cada corrida del flujo.",
     "Permite probar los modelos en tiempo real: subir una foto o escribir un reclamo.",
     "Muestra KPIs, la comparación de los modelos, la presión de reclamos y la tabla de reposición."], size=19)

# 10. Negocio
s = slide(NAVY); box(s, 0, 0, Inches(0.22), SH, TEAL, radius=0)
text(s, Inches(0.9), Inches(0.7), SW - Inches(1.8), Inches(0.9), [("Valor de negocio (ROI)", 30, WHITE, True)])
kpi(s, Inches(1.0), Inches(2.1), Inches(2.7), "$260k", "Beneficio / mes")
kpi(s, Inches(4.0), Inches(2.1), Inches(2.7), "$26k", "Costo / mes")
kpi(s, Inches(7.0), Inches(2.1), Inches(2.7), "9×", "ROI mensual")
kpi(s, Inches(10.0), Inches(2.1), Inches(2.4), "$2,8M", "Neto anual")
text(s, Inches(1.0), Inches(4.5), SW - Inches(2), Inches(1.6),
     [("Estimación con supuestos explícitos. La IA no suma costo porque usa el gateway de n8n.", 17, BLUETX, False),
      ("Beneficio = quiebres evitados + horas ahorradas al encargado.", 16, ORANGE, True)], space=8)

# 11. Robustez / riesgos
s = slide(); header(s, 8, "Riesgos y controles (R10)")
bullets(s, Inches(0.8), Inches(2.0), SW - Inches(1.5), Inches(4.3),
    ["Error del modelo → comparación con baseline + marca de revisión humana.",
     "Alucinaciones del LLM → recibe solo resultados calculados, salida JSON, RAG que cita la fuente.",
     "Acción incorrecta → aprobación humana obligatoria antes de actuar.",
     "Datos sensibles → flujo exportado sin credenciales, reclamos simulados.",
     "El sistema asiste, no reemplaza, al encargado."], size=19)

# 12. Requisitos
s = slide(); header(s, 9, "Los 11 requisitos, cumplidos")
bullets(s, Inches(0.8), Inches(2.0), Inches(6.2), Inches(4.3),
    ["R1 LLM (Claude, JSON)", "R2 Python (servicio)", "R3 Serie temporal (LSTM)",
     "R4 Imágenes (ViT)", "R5 Transformer/NLP (RAG)", "R6 Automatización (n8n)"], size=18)
bullets(s, Inches(7.0), Inches(2.0), Inches(5.6), Inches(4.3),
    ["R7 Contexto industrial (retail)", "R8 Datos (M5 + Grocery + reclamos)", "R9 Tablero (HTML)",
     "R10 Negocio y ética (ROI, riesgos)", "R11 Notificaciones (Gmail + Telegram)"], size=18)

# 13. Cierre
s = slide(NAVY); box(s, 0, Inches(3.5), SW, Inches(0.12), TEAL, radius=0)
text(s, Inches(0.9), Inches(2.3), SW - Inches(1.8), Inches(1.2), [("Demostración en vivo", 40, WHITE, True)])
text(s, Inches(0.9), Inches(3.8), SW - Inches(1.8), Inches(0.9),
     [("Ejecutar el flujo → aprobar en Telegram → ver el tablero + subir una foto en vivo.", 20, BLUETX, False)])
text(s, Inches(0.9), Inches(6.4), SW - Inches(1.8), Inches(0.5), [("Gracias.  —  Tomás Allende", 16, WHITE, True)])

prs.save(OUT); print("Presentacion generada:", OUT, "| slides:", len(prs.slides._sldIdLst))
