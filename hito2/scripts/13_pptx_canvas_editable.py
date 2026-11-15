# -*- coding: utf-8 -*-
"""Deck Hito 2 'Industrial Telemetry' — 100% editable (texto + graficos nativos)."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Presentacion_Hito2_Editable.pptx")

# ---- paleta ----
BG    = RGBColor(0x0A, 0x10, 0x18)
PANEL = RGBColor(0x0F, 0x1A, 0x26)
PANEL2= RGBColor(0x13, 0x21, 0x2F)
INK   = RGBColor(0xEA, 0xF1, 0xF7)
MUTE  = RGBColor(0x7E, 0x92, 0xA6)
FAINT = RGBColor(0x3A, 0x4A, 0x5C)
LINE  = RGBColor(0x1E, 0x2E, 0x3D)
TEAL  = RGBColor(0x35, 0xC2, 0xAD)
TEALD = RGBColor(0x1E, 0x5E, 0x57)
SLATE = RGBColor(0x2A, 0x3B, 0x4C)
CORAL = RGBColor(0xE4, 0x64, 0x7A)
AMBER = RGBColor(0xE7, 0xB1, 0x3A)

# ---- fuentes (ya instaladas en Windows) ----
DISP = "Bahnschrift"          # titulares industriales
NUM  = "Bahnschrift SemiBold" # numeros
BODY = "Segoe UI"
BODB = "Segoe UI Semibold"
MONO = "Consolas"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
EMUIN = 914400

def slide():
    s = prs.slides.add_slide(BLANK)
    f = s.background.fill; f.solid(); f.fore_color.rgb = BG
    return s

def txt(s, x, y, w, h, text, font=BODY, size=14, color=INK, bold=False,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None, line_spacing=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing: p.line_spacing = line_spacing
        r = p.add_run(); r.text = line
        r.font.name = font; r.font.size = Pt(size); r.font.bold = bold
        r.font.color.rgb = color
        if spacing is not None:
            rpr = r._r.get_or_add_rPr(); rpr.set("spc", str(int(spacing)))
    return tb

def rect(s, x, y, w, h, fill=None, line=None, lw=1.0):
    sp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    return sp

def card(s, x, y, w, h, fill=PANEL, line=LINE, lw=1.2, round=0.04):
    sp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.shadow.inherit = False
    try: sp.adjustments[0] = round
    except Exception: pass
    sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    return sp

def header(s, idx, kicker):
    txt(s, 0.73, 0.3, 7, 0.3, kicker, MONO, 9.5, MUTE)
    txt(s, 8.6, 0.3, 4.0, 0.3, f"{idx:02d} — 11", MONO, 9.5, TEAL, align=PP_ALIGN.RIGHT)
    rect(s, 0.73, 0.63, 11.87, 0.014, fill=LINE)
    rect(s, 0.73, 0.63, 1.1, 0.024, fill=TEAL)
    txt(s, 0.73, 6.98, 6, 0.25, "REPOSICIÓN INTELIGENTE DE INVENTARIO", MONO, 7.5, FAINT)
    txt(s, 7.6, 6.98, 5.0, 0.25, "TIENDA CA-1 · M5 WALMART", MONO, 7.5, FAINT, align=PP_ALIGN.RIGHT)

def tag(s, y, text, color=TEAL):
    txt(s, 0.73, y, 9, 0.3, text, MONO, 11, color, bold=True)

def arrow(s, x, y, w, color=TEAL):
    sp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.12))
    sp.shadow.inherit = False
    sp.fill.solid(); sp.fill.fore_color.rgb = color; sp.line.fill.background()
    try: sp.adjustments[0] = 0.5; sp.adjustments[1] = 0.6
    except Exception: pass
    return sp

def style_chart(chart, pct=False, cat_color=MUTE, lbl_size=11):
    chart.has_legend = False
    chart.has_title = False
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(lbl_size); ca.tick_labels.font.name = MONO
    ca.tick_labels.font.color.rgb = cat_color
    ca.format.line.color.rgb = LINE
    ca.has_major_gridlines = False; ca.has_minor_gridlines = False
    va = chart.value_axis
    va.visible = False
    va.has_major_gridlines = False; va.has_minor_gridlines = False
    va.format.line.fill.background()

# ===================== 01 · PORTADA =====================
s = slide()
txt(s, 0.73, 0.3, 10, 0.3, "PROYECTO FINAL · IA GENERATIVA PARA LA GESTIÓN INDUSTRIAL", MONO, 10, MUTE)
txt(s, 8.6, 0.3, 4.0, 0.3, "HITO 2", MONO, 10, TEAL, bold=True, align=PP_ALIGN.RIGHT)
rect(s, 0.73, 0.63, 11.87, 0.014, fill=LINE); rect(s, 0.73, 0.63, 1.1, 0.024, fill=TEAL)
txt(s, 0.66, 1.15, 12, 1.5, "REPOSICIÓN", DISP, 96, INK, bold=True)
txt(s, 0.66, 2.45, 12, 1.5, "INTELIGENTE", DISP, 96, INK, bold=True)
txt(s, 0.68, 3.75, 12, 0.9, "DE INVENTARIO", DISP, 44, TEAL, bold=True)
txt(s, 0.73, 4.9, 10, 0.4, "VER   ·   LEER   ·   PREDECIR", MONO, 14, INK, bold=True, spacing=100)
txt(s, 0.73, 5.4, 10, 0.4, "tres señales no estructuradas → una decisión priorizada", BODY, 13, MUTE)
rect(s, 0.74, 6.0, 3.0, 0.012, fill=LINE)
txt(s, 0.73, 6.2, 8, 0.3, "TOMÁS ALLENDE", MONO, 11, INK, bold=True)
txt(s, 0.73, 6.55, 8, 0.3, "20 SKU · DATOS REALES M5 · 2026", MONO, 9, FAINT)

# ===================== 02 · CONTEXTO =====================
s = slide(); header(s, 1, "HITO 2 · REPOSICIÓN CA-1"); tag(s, 1.0, "01 / CONTEXTO")
txt(s, 0.68, 1.5, 12, 0.8, "Decidir qué reponer,", DISP, 44, INK, bold=True)
txt(s, 0.68, 2.25, 12, 0.8, "cada día, sin adivinar.", DISP, 44, TEAL, bold=True)
cols = [("01", "DEMANDA", "¿Cuánto se venderá?", "Serie temporal de ventas"),
        ("02", "PRODUCTO", "¿Qué hay en góndola?", "Foto → identificación"),
        ("03", "RECLAMOS", "¿De qué se quejan?", "Texto del cliente")]
cw, gap = 3.78, 0.2
for i, (n, t, q, d) in enumerate(cols):
    x = 0.73 + i*(cw+gap)
    card(s, x, 3.5, cw, 2.1)
    txt(s, x+0.3, 3.75, cw-0.6, 0.3, n, MONO, 11, TEAL)
    txt(s, x+0.3, 4.05, cw-0.6, 0.5, t, NUM, 22, INK, bold=True)
    txt(s, x+0.3, 4.62, cw-0.6, 0.4, q, BODB, 13, INK, bold=True)
    txt(s, x+0.3, 5.0, cw-0.6, 0.4, d, BODY, 11.5, MUTE)
    rect(s, x+0.3, 5.42, 0.85, 0.028, fill=TEALD)
txt(s, 0.73, 5.95, 12, 0.4, "Las tres se combinan y un LLM entrega la recomendación. El encargado aprueba.",
    BODY, 13, MUTE)

# ===================== 03 · ARQUITECTURA =====================
s = slide(); header(s, 2, "HITO 2 · REPOSICIÓN CA-1"); tag(s, 1.0, "02 / ARQUITECTURA")
txt(s, 0.68, 1.5, 12, 0.8, "Un pipeline, orquestado en n8n.", DISP, 40, INK, bold=True)
def node(x, y, w, h, title, sub, c=INK, fill=PANEL, ln=LINE):
    card(s, x, y, w, h, fill=fill, line=ln)
    txt(s, x, y+h*0.22, w, 0.4, title, NUM, 13, c, bold=True, align=PP_ALIGN.CENTER)
    txt(s, x, y+h*0.55, w, 0.3, sub, MONO, 8.5, MUTE, align=PP_ALIGN.CENTER)
node(0.73, 3.3, 2.1, 0.95, "GOOGLE SHEETS", "ventas diarias")
card(s, 3.35, 2.9, 3.5, 1.75, fill=PANEL2, line=TEALD, lw=1.3)
txt(s, 3.35, 3.05, 3.5, 0.3, "3 MODELOS DE IA", MONO, 9.5, TEAL, bold=True, align=PP_ALIGN.CENTER)
for i, (m, d) in enumerate([("LSTM", "demanda"), ("ViT", "imagen"), ("Transformer+RAG", "texto")]):
    yy = 3.45 + i*0.37
    txt(s, 3.6, yy, 2.5, 0.3, "› " + m, BODY, 12, INK)
    txt(s, 5.6, yy, 1.1, 0.3, d, MONO, 8.5, MUTE, align=PP_ALIGN.RIGHT)
node(7.35, 3.3, 2.3, 0.95, "CLAUDE", "recomendación JSON", TEAL, ln=TEALD)
arrow(s, 2.9, 3.72, 0.4); arrow(s, 6.9, 3.72, 0.4)
node(7.35, 5.0, 2.3, 0.95, "APROBACIÓN", "Telegram · humano", AMBER, ln=RGBColor(0x5c,0x4a,0x1e))
arrow(s, 8.4, 4.3, 0.6).rotation = 90
node(0.73, 5.0, 3.0, 0.95, "CORREO · TELEGRAM · REGISTRO", "acción + Sheets")
arrow(s, 3.9, 5.42, 3.3, color=TEAL).rotation = 180
node(0.73, 6.25, 3.0, 0.7, "TABLERO HTML EN VIVO", "se actualiza cada corrida", TEAL, ln=TEALD)
arrow(s, 2.1, 5.98, 0.25).rotation = 90
txt(s, 7.35, 6.15, 5.3, 0.4, "El humano aprueba antes de cualquier envío.", BODY, 11.5, MUTE)
txt(s, 7.35, 6.5, 5.3, 0.4, "Modelos pesados fuera de n8n (servicio Python, HTTP).", BODY, 11.5, MUTE)

# ===================== helper slides de modelo (bar) =====================
def model_bar(idx, kicker, section, big, bigc, cats, vals, winner, numfmt, pct,
              stat, statsub, caption, ymax):
    s = slide(); header(s, idx, kicker); tag(s, 1.0, section)
    txt(s, 0.68, 1.45, 8.5, 1.1, big, DISP, 60, bigc, bold=True)
    txt(s, 7.7, 1.5, 4.9, 0.7, stat, NUM, 40, INK, bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 7.7, 2.35, 4.9, 0.3, statsub, MONO, 10.5, TEAL, align=PP_ALIGN.RIGHT)
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("v", vals)
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.73), Inches(3.0),
                            Inches(7.6), Inches(3.3), cd)
    chart = gf.chart; style_chart(chart, pct)
    chart.value_axis.maximum_scale = ymax; chart.value_axis.minimum_scale = 0
    plot = chart.plots[0]; plot.gap_width = 55
    plot.has_data_labels = True
    dl = plot.data_labels; dl.number_format = numfmt; dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.name = MONO; dl.font.size = Pt(11); dl.font.color.rgb = MUTE
    ser = plot.series[0]
    for i, pt in enumerate(ser.points):
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = TEAL if i == winner else SLATE
    card(s, 9.35, 3.0, 3.25, 3.3, fill=PANEL)
    txt(s, 9.65, 3.3, 2.65, 2.7, caption, BODY, 13, INK, line_spacing=1.25)
    return s

model_bar(3, "HITO 2 · SERIE TEMPORAL", "03 / MODELO · SERIE TEMPORAL", "LSTM", TEAL,
    ["Media móvil", "Naive", "Holt-Winters", "GRU", "LSTM"],
    [7.912, 8.064, 7.34, 6.578, 6.461], 4, '0.00', False,
    "6,46", "MAE · GANA 14/20 SKU",
    "Red neuronal con memoria vs Holt-Winters clásico. Mismo protocolo del Hito 1 "
    "(28 días de prueba). Navaja de Occam: el modelo complejo se justifica con datos.", 9.5)

model_bar(4, "HITO 2 · VISIÓN", "04 / MODELO · IMÁGENES", "ViT", TEAL,
    ["Baseline color", "ResNet50", "ViT"],
    [0.3175, 0.8483, 0.8684], 2, '0%', True,
    "87%", "ACCURACY · VS 32% BASELINE",
    "Vision Transformer preentrenado como extractor de características + clasificador. "
    "Identifica el producto por foto, sin reentrenar la red completa.", 1.0)

# ===================== 06 · NLP grouped =====================
s = slide(); header(s, 5, "HITO 2 · TEXTO"); tag(s, 1.0, "05 / MODELO · TEXTO / NLP")
txt(s, 0.68, 1.45, 9, 1.1, "Transformer + RAG", DISP, 54, TEAL, bold=True)
txt(s, 7.7, 1.5, 4.9, 0.7, "0,96", NUM, 40, INK, bold=True, align=PP_ALIGN.RIGHT)
txt(s, 7.7, 2.35, 4.9, 0.3, "ACCURACY · VS 0,89 REGLAS", MONO, 10.5, TEAL, align=PP_ALIGN.RIGHT)
cd = CategoryChartData(); cd.categories = ["Accuracy", "F1"]
cd.add_series("Reglas", [0.889, 0.702]); cd.add_series("Transformer", [0.963, 0.771])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.73), Inches(3.0),
                        Inches(7.6), Inches(3.3), cd)
chart = gf.chart; style_chart(chart)
chart.value_axis.maximum_scale = 1.08; chart.value_axis.minimum_scale = 0
chart.has_legend = True
from pptx.enum.chart import XL_LEGEND_POSITION
chart.legend.position = XL_LEGEND_POSITION.BOTTOM; chart.legend.include_in_layout = False
chart.legend.font.size = Pt(10); chart.legend.font.name = MONO; chart.legend.font.color.rgb = MUTE
plot = chart.plots[0]; plot.gap_width = 90
plot.has_data_labels = True; plot.data_labels.number_format = '0.00'
plot.data_labels.number_format_is_linked = False
plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
plot.data_labels.font.name = MONO; plot.data_labels.font.size = Pt(10); plot.data_labels.font.color.rgb = MUTE
plot.series[0].format.fill.solid(); plot.series[0].format.fill.fore_color.rgb = SLATE
plot.series[1].format.fill.solid(); plot.series[1].format.fill.fore_color.rgb = TEAL
card(s, 9.35, 3.0, 3.25, 3.3, fill=PANEL)
txt(s, 9.65, 3.3, 2.65, 2.7,
    "Embeddings multilingües: clasifica por significado, no por palabra exacta. "
    "RAG busca el reclamo real y cita la fuente — control anti-alucinación.",
    BODY, 13, INK, line_spacing=1.25)

# ===================== 07 · CONTROL =====================
s = slide(); header(s, 6, "HITO 2 · ORQUESTACIÓN"); tag(s, 1.0, "06 / ORQUESTACIÓN + CONTROL")
txt(s, 0.68, 1.5, 12, 0.8, "El humano aprueba.", DISP, 50, INK, bold=True)
txt(s, 0.68, 2.35, 12, 0.8, "Siempre.", DISP, 50, AMBER, bold=True)
steps = [("01", "CLAUDE", "JSON priorizado:\ndiagnóstico, cuánto,\nprioridad, revisión", TEAL),
         ("02", "TELEGRAM", "aprueba o rechaza\nantes de enviar", AMBER),
         ("03", "ACCIÓN", "correo + mensaje +\nregistro histórico", INK)]
cw, gap = 3.6, 0.5
for i, (n, t, d, c) in enumerate(steps):
    x = 0.73 + i*(cw+gap)
    card(s, x, 3.5, cw, 2.0)
    txt(s, x+0.28, 3.72, cw-0.5, 0.3, n, MONO, 11, c)
    txt(s, x+0.28, 4.02, cw-0.5, 0.5, t, NUM, 19, c, bold=True)
    txt(s, x+0.28, 4.55, cw-0.5, 0.9, d, BODY, 11.5, MUTE, line_spacing=1.1)
    if i < 2: arrow(s, x+cw+0.08, 4.45, 0.34)
txt(s, 0.73, 5.85, 12, 0.4, "n8n · Claude vía API propia (claude-haiku) · nada se envía sin aprobación.", BODY, 12.5, MUTE)
txt(s, 0.73, 6.3, 12, 0.4, "El sistema asiste al encargado — no lo reemplaza.", BODB, 12.5, INK, bold=True)

# ===================== 08 · TABLERO =====================
s = slide(); header(s, 7, "HITO 2 · SALIDA"); tag(s, 1.0, "07 / SALIDA · DASHBOARD HTML")
txt(s, 0.68, 1.5, 12, 0.9, "Tablero en vivo.", DISP, 50, TEAL, bold=True)
for i, (v, l) in enumerate([("6", "productos a reponer"), ("3", "prioridad alta"), ("20", "SKU monitoreados")]):
    x = 0.73 + i*2.7
    card(s, x, 3.3, 2.45, 1.5)
    txt(s, x+0.28, 3.5, 2.0, 0.8, v, NUM, 40, INK, bold=True)
    txt(s, x+0.3, 4.35, 2.1, 0.3, l, MONO, 9, MUTE)
card(s, 8.95, 3.3, 3.65, 2.3, fill=PANEL2, line=TEALD, lw=1.3)
txt(s, 9.25, 3.5, 3.1, 0.3, "PRUEBA EN VIVO", MONO, 9.5, TEAL, bold=True)
for i, t in enumerate(["Foto → ViT reconoce producto", "Reclamo → categoría + RAG", "Reponedor registra stock"]):
    txt(s, 9.25, 3.95 + i*0.45, 3.2, 0.4, "› " + t, BODY, 11.5, INK)
txt(s, 0.73, 5.9, 12, 0.4, "Se actualiza con cada corrida del flujo. Demostración interactiva de los 3 modelos.", BODY, 12.5, MUTE)
txt(s, 0.73, 6.3, 12, 0.4, "Servido por el servicio local (FastAPI) — no una captura estática.", BODY, 12.5, MUTE)

# ===================== 09 · ROI =====================
s = slide(); header(s, 8, "HITO 2 · NEGOCIO"); tag(s, 1.0, "08 / EVALUACIÓN DE NEGOCIO")
txt(s, 0.62, 1.35, 4, 1.8, "9×", DISP, 120, TEAL, bold=True)
txt(s, 3.5, 1.75, 9, 0.6, "ROI mensual", NUM, 26, INK, bold=True)
txt(s, 3.52, 2.4, 9, 0.4, "por cada $1 de costo, $9 de beneficio", MONO, 11, MUTE)
# ¿De dónde sale el ahorro? — desglose
txt(s, 0.73, 3.3, 10, 0.3, "DE DÓNDE SALE EL BENEFICIO", MONO, 10, AMBER, bold=True)
bd = [("+$140.000", TEAL, "Ventas recuperadas", "menos quiebres (8%→3%): se dejan de perder ~372 ventas/mes × margen"),
      ("+$120.000", TEAL, "Horas del encargado", "30 h/mes que ya no gasta decidiendo \"a ojo\" (1 h/día × $4.000)"),
      ("−$26.000",  MUTE, "Costo de operar", "hosting + mantención. La IA cuesta $0 (gateway n8n)")]
for i, (v, c, t, d) in enumerate(bd):
    y = 3.75 + i*0.7
    txt(s, 0.73, y, 2.1, 0.5, v, NUM, 22, c, bold=True)
    txt(s, 3.0, y-0.02, 3.0, 0.4, t, BODB, 13, INK, bold=True)
    txt(s, 3.0, y+0.32, 9.5, 0.4, d, BODY, 10.5, MUTE)
rect(s, 0.74, 5.95, 11.85, 0.014, fill=LINE)
txt(s, 0.73, 6.15, 7, 0.5, "= $234.000 neto / mes", NUM, 24, INK, bold=True)
txt(s, 8.3, 6.2, 4.3, 0.5, "≈ $2,8 M al año", NUM, 22, TEAL, bold=True, align=PP_ALIGN.RIGHT)
txt(s, 0.73, 6.75, 12, 0.3, "Supuestos explícitos y conservadores, declarados con honestidad.", BODY, 10, FAINT)

# ===================== 10 · TRABAJO FUTURO =====================
s = slide(); header(s, 9, "HITO 2 · ROADMAP"); tag(s, 1.0, "09 / TRABAJO FUTURO")
txt(s, 0.68, 1.5, 12, 0.9, "Cerrar el ciclo.", DISP, 50, INK, bold=True)
rect(s, 1.0, 3.05, 0.02, 2.55, fill=TEALD)
steps = [("01", "Catálogo SKU ↔ producto real", "FOODS_2_019 ↔ manzana ↔ Apple. La base que conecta foto, reclamo y reposición."),
         ("02", "Foto → conteo → reposición", "El catálogo traduce la foto a SKU y el conteo alimenta la decisión automática."),
         ("03", "Reclamo → fecha al cliente", "“No hay papel”: estima con historial + lead time cuándo se repone y avisa al cliente.")]
for i, (n, t, d) in enumerate(steps):
    y = 3.1 + i*0.9
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.88), Inches(y), Inches(0.26), Inches(0.26))
    c.shadow.inherit = False; c.fill.solid(); c.fill.fore_color.rgb = BG
    c.line.color.rgb = TEAL; c.line.width = Pt(2)
    txt(s, 0.6, y-0.3, 0.6, 0.25, n, MONO, 8.5, TEAL)
    txt(s, 1.4, y-0.08, 10, 0.4, t, BODB, 17, INK, bold=True)
    txt(s, 1.4, y+0.35, 10.5, 0.4, d, BODY, 11.5, MUTE)
txt(s, 0.73, 6.25, 12, 0.4, "Las tres se apoyan en un mapeo robusto producto / reclamo ↔ SKU.", BODB, 12.5, TEAL, bold=True)

# ===================== 11 · CIERRE =====================
s = slide(); header(s, 10, "HITO 2 · CIERRE"); tag(s, 1.0, "10 / CIERRE")
txt(s, 0.68, 1.75, 12, 0.8, "Ver, leer, predecir —", DISP, 48, INK, bold=True)
txt(s, 0.68, 2.6, 12, 0.8, "y decidir con control humano.", DISP, 48, TEAL, bold=True)
txt(s, 0.73, 3.9, 8, 0.3, "LIMITACIONES DECLARADAS", MONO, 10, AMBER, bold=True)
for i, t in enumerate(["Stock actual simulado (sin acceso al inventario real)",
                       "Reclamos simulados, con distribución documentada",
                       "Reclamo aún no mapeado a SKU exacto"]):
    txt(s, 0.73, 4.35 + i*0.42, 9, 0.35, "— " + t, BODY, 12.5, MUTE)
rect(s, 0.74, 5.85, 4.5, 0.012, fill=LINE)
txt(s, 0.73, 6.05, 9, 0.3, "Datos reales M5 Walmart (CA-1) · Grocery Store Dataset · reclamos simulados.", BODY, 11, FAINT)
txt(s, 0.73, 6.4, 9, 0.3, "IA usada como apoyo; el autor comprende y explica cada parte.", BODY, 11, FAINT)
txt(s, 7.5, 3.9, 5.1, 1.3, "TOMÁS\nALLENDE", DISP, 42, FAINT, bold=True, align=PP_ALIGN.RIGHT)

prs.save(OUT)
print("OK ->", OUT, "| slides:", len(prs.slides._sldIdLst))
