# -*- coding: utf-8 -*-
"""Genera el Informe final del Hito 2 (Word)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Informe_Hito2.docx")
IMG = os.path.join(BASE, "outputs")
os.makedirs(IMG, exist_ok=True)
NAVY = RGBColor(0x0F, 0x24, 0x44)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
ORANGE = RGBColor(0xB5, 0x65, 0x1D)
DIAG = os.path.join(IMG, "diagrama_hito2.png")

# -------- Diagrama de arquitectura integrada --------
fig, ax = plt.subplots(figsize=(9.5, 3.0))
ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 4)
etapas = ["Disparador\n/ Ventas\n(Sheets)", "Preparar\nseries", "Modelos (servicio)\nLSTM + NLP",
          "Claude\n(recomendacion\nintegrada)", "Control\nhumano\n(Telegram)"]
x = 0.1
for i, t in enumerate(etapas):
    b = FancyBboxPatch((x, 1.5), 2.0, 1.1, boxstyle="round,pad=0.04", fc="#eaf0f7", ec="#0f2444", lw=1.4)
    ax.add_patch(b); ax.text(x + 1.0, 2.05, t, ha="center", va="center", fontsize=7.2)
    if i < len(etapas) - 1:
        ax.add_patch(FancyArrowPatch((x + 2.0, 2.05), (x + 2.3, 2.05), arrowstyle="-|>", mutation_scale=12, color="#0f2444"))
    x += 2.3
sal = ["Gmail", "Telegram", "Registro\n+ Tablero"]
for j, s in enumerate(sal):
    yb = 2.6 - j * 1.0
    b = FancyBboxPatch((x + 0.1, yb - 0.35), 1.5, 0.7, boxstyle="round,pad=0.04", fc="#e6f4f1", ec="#2a9d8f", lw=1.4)
    ax.add_patch(b); ax.text(x + 0.85, yb, s, ha="center", va="center", fontsize=7.2)
    ax.add_patch(FancyArrowPatch((x - 0.3, 2.05), (x + 0.1, yb), arrowstyle="-|>", mutation_scale=10, color="#2a9d8f"))
# modelo de imagenes (aparte, demo)
ax.add_patch(FancyBboxPatch((4.7, 0.1), 2.4, 0.8, boxstyle="round,pad=0.04", fc="#fbeede", ec="#b5651d", lw=1.2))
ax.text(5.9, 0.5, "Modelo de imagenes (ViT)\nendpoint para demo", ha="center", va="center", fontsize=6.8)
plt.tight_layout(); plt.savefig(DIAG, dpi=150, bbox_inches="tight"); plt.close()

# -------- Documento --------
doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)

def h(txt, size=14, color=NAVY, before=10):
    p = doc.add_paragraph(); r = p.add_run(txt); r.bold = True
    r.font.size = Pt(size); r.font.color.rgb = color
    p.paragraph_format.space_before = Pt(before); p.paragraph_format.space_after = Pt(4); return p

def para(txt, size=10.5):
    p = doc.add_paragraph(); r = p.add_run(txt); r.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(4); return p

def bullet(txt):
    p = doc.add_paragraph(style="List Bullet"); p.add_run(txt).font.size = Pt(10.5); return p

def tabla(filas, encabezados):
    t = doc.add_table(rows=1, cols=len(encabezados)); t.style = "Light Grid Accent 1"
    for i, e in enumerate(encabezados):
        t.rows[0].cells[i].paragraphs[0].add_run(e).bold = True
    for fila in filas:
        c = t.add_row().cells
        for i, v in enumerate(fila):
            c[i].text = str(v)
    return t

# Portada
p = doc.add_paragraph(); r = p.add_run("Sistema Inteligente de Reposición de Inventario")
r.bold = True; r.font.size = Pt(20); r.font.color.rgb = NAVY
p = doc.add_paragraph(); r = p.add_run("Informe Final — Hito 2 (Sistema Integrado)")
r.font.size = Pt(12); r.font.color.rgb = ORANGE
doc.add_paragraph("IA Generativa para la Gestión Industrial · Caso Retail (M5 Walmart, tienda CA_1)").runs[0].font.size = Pt(10)
doc.add_paragraph("Autor: Tomás Allende   |   Noviembre 2026").runs[0].font.size = Pt(10)

h("1. Resumen ejecutivo", before=6)
para("El sistema automatiza la decisión diaria de reposición de inventario de una tienda de retail. "
     "En el Hito 2 evoluciona a un sistema integrado que combina tres modelos de inteligencia artificial "
     "—pronóstico de demanda (serie temporal), reconocimiento de productos (imágenes) y análisis de "
     "reclamos de clientes (texto)— orquestados en n8n. Un modelo de lenguaje (Claude) interpreta los "
     "resultados y redacta una recomendación priorizada que, tras la aprobación humana por Telegram, se "
     "envía por correo y se registra, y alimenta un tablero. Cada modelo se comparó con su alternativa "
     "simple (Navaja de Occam) y la superó.")

h("2. Problema, usuario y decisión (R7)")
para("Una tienda de retail pierde ventas por quiebres de stock e inmoviliza capital por sobre-stock. El "
     "usuario es el ENCARGADO DE COMPRAS, que cada mañana decide, por cada producto (SKU), si reponer, "
     "cuánto y con qué prioridad. El indicador de negocio es quiebres evitados y capital inmovilizado "
     "reducido. El sistema convierte esa decisión manual en una recomendación diaria, priorizada y con "
     "control humano.")

h("3. Arquitectura del sistema integrado")
doc.add_picture(DIAG, width=Inches(6.3))
para("El flujo corre en n8n: lee las ventas (Google Sheets), llama por HTTP a un servicio Python que "
     "ejecuta los modelos pesados (LSTM y NLP), combina las señales, le pide a Claude una recomendación "
     "integrada, solicita la aprobación humana por Telegram y, al aprobar, envía por Gmail y Telegram, "
     "registra en Sheets y actualiza el tablero. El modelo de imágenes se expone como endpoint para la "
     "demostración en vivo.")
bullet("Servicio externo (R2): los modelos de Deep Learning no corren dentro de n8n; se ejecutan en un "
       "servicio FastAPI llamado por HTTP (expuesto con un túnel), entregando su código.")

h("4. Los datos (R8)")
bullet("Serie temporal y reposición: dataset público M5 (Walmart), tienda CA_1, 20 SKU de mayor venta.")
bullet("Imágenes: Grocery Store Dataset (Klasson et al.), 43 clases de productos de supermercado.")
bullet("Reclamos de clientes: conjunto simulado (90 reclamos) con supuesto documentado, ya que no se "
       "dispone de los reclamos reales de la tienda. El stock actual también se simula con supuestos.")

h("5. Modelo 1 — Serie temporal: Deep Learning vs. clásico (R3)")
para("Se pronostica la demanda diaria por SKU a 7 días y se compara el modelo clásico del Hito 1 "
     "(Holt-Winters) contra Deep Learning (LSTM y GRU), con el mismo protocolo (test de 28 días, MAE).")
tabla([["Media móvil 7d (baseline)", "7,91"], ["Naive estacional (baseline)", "8,06"],
       ["Holt-Winters (clásico)", "7,34"], ["GRU (Deep Learning)", "6,58"],
       ["LSTM (Deep Learning)", "6,46  — gana al clásico en 14/20 SKU"]],
      ["Método", "MAE (menor = mejor)"])
ej = os.path.join(IMG, "series_comparacion.png")
if os.path.exists(ej): doc.add_picture(ej, width=Inches(4.8))
para("El LSTM mejora el error respecto a Holt-Winters e incluso iguala a la referencia de statsmodels "
     "del Hito 1. Usa como entrada la venta escalada más features de calendario (día de la semana, SNAP).")

h("6. Modelo 2 — Imágenes: reconocimiento de productos (R4)")
para("Se usan modelos preentrenados como extractores de características y encima un clasificador simple. "
     "Se comparan tres enfoques sobre el conjunto de test (2.485 imágenes, 43 clases).")
tabla([["Baseline (histograma de color)", "0,32"], ["CNN — ResNet50", "0,85"],
       ["Transformer — ViT", "0,87  (gana)"]], ["Modelo", "Accuracy"])
ei = os.path.join(IMG, "r4_comparacion.png")
if os.path.exists(ei): doc.add_picture(ei, width=Inches(4.6))
para("El Vision Transformer (ViT) supera a la CNN y ambos superan por mucho al baseline, lo que justifica "
     "el uso de modelos preentrenados. Se expone como endpoint para reconocer un producto desde una foto.")

h("7. Modelo 3 — Texto / NLP: Transformer y RAG (R5)")
para("Sobre los reclamos de clientes se aplica un Transformer (modelo de embeddings multilingüe). Se "
     "clasifica cada reclamo por categoría y se compara contra una regla por palabras clave.")
tabla([["Baseline (reglas por palabra clave)", "0,89", "0,70"],
       ["Transformer (embeddings)", "0,96", "0,77"]], ["Enfoque", "Accuracy", "F1 macro"])
para("Además se implementa RAG (Retrieval-Augmented Generation): se convierten los reclamos en embeddings "
     "y, ante una consulta, se recuperan los más relevantes para que el LLM responda citando la fuente, "
     "evitando alucinaciones. De esta señal se obtiene la presión de reclamos de quiebre por producto, "
     "que ajusta la prioridad de reposición.")

h("8. LLM integrado, orquestación y control humano (R1, R6, R10, R11)")
bullet("LLM (R1): Claude (vía gateway, sin API key) recibe los resultados ya calculados —no los datos "
       "crudos— y entrega un JSON estructurado (diagnóstico, recomendación, prioridad, justificación, "
       "revisión humana).")
bullet("Orquestación (R6): un único flujo en n8n llama a los modelos, combina sus salidas y las entrega "
       "al LLM para una recomendación integrada.")
bullet("Control humano (R10): antes de enviar nada, el flujo pide aprobación por Telegram; si se rechaza, "
       "no se envía. Si un dato es dudoso, el LLM marca 'revisión humana'.")
bullet("Notificaciones (R11): correo por Gmail (obligatorio) y mensaje por Telegram, más registro histórico "
       "en Google Sheets; ambos incluyen el enlace al tablero.")

h("9. Tablero (R9)")
para("Los resultados se presentan en un tablero HTML. Existe una versión publicada (estática, para "
     "mostrar/entregar) y una versión en vivo servida por el propio servicio, que se actualiza con cada "
     "corrida del flujo y permite probar los modelos en tiempo real: subir una foto para reconocer el "
     "producto o escribir un reclamo para clasificarlo. Muestra KPIs, la comparación de los modelos, la "
     "presión de reclamos y la tabla de reposición.")

h("10. Evaluación de negocio (ROI) y riesgos (R10)")
para("Estimación con supuestos explícitos y conservadores (CLP/mes), como orden de magnitud:")
tabla([["Beneficio (quiebres evitados + horas ahorradas)", "$259.607"],
       ["Costo de operar (hosting + mantención; IA vía gateway)", "$26.000"],
       ["Neto mensual", "$233.607  (ROI ≈ 9×)"],
       ["Neto anual aproximado", "≈ $2,8 millones"]], ["Concepto", "CLP / mes"])
para("Lectura honesta: el ROI es alto en parte porque la IA está subsidiada por los créditos de gateway de "
     "n8n. Riesgos y controles: errores del modelo (comparación con baseline + revisión humana), "
     "alucinaciones del LLM (solo recibe resultados calculados, salida JSON, RAG que cita la fuente), "
     "datos sensibles (flujo exportado sin credenciales, reclamos simulados).")

h("11. Limitaciones")
bullet("Datos históricos (2016) como caso representativo; stock y reclamos simulados con supuestos.")
bullet("Los reclamos usan nombres de producto genéricos; en producción se mapearían a los SKU exactos.")
bullet("El servicio corre localmente con un túnel; en producción se desplegaría en un host estable.")

h("12. Cumplimiento de los 11 requisitos")
tabla([["R1 LLM", "Claude, salida JSON estructurada"], ["R2 Python", "Servicio FastAPI externo"],
       ["R3 Serie temporal", "LSTM/GRU vs Holt-Winters"], ["R4 Imágenes", "ViT vs ResNet vs baseline"],
       ["R5 Transformer/NLP", "Embeddings + RAG sobre reclamos"], ["R6 Automatización", "Flujo n8n orquestado"],
       ["R7 Contexto industrial", "Retail; encargado de compras"], ["R8 Datos", "M5 + Grocery + reclamos"],
       ["R9 Tablero", "HTML estático y en vivo"], ["R10 Negocio y ética", "ROI + riesgos + control humano"],
       ["R11 Notificaciones", "Gmail + Telegram + registro"]], ["Requisito", "Cómo se cumple"])

doc.save(OUT)
print("Informe generado:", OUT)
