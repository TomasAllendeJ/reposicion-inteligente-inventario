# -*- coding: utf-8 -*-
"""Genera un PDF explicativo (en simple) de todo el Hito 2."""
import os
from fpdf import FPDF

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Explicacion_Hito2.pdf")

NAVY = (15, 36, 68)
TEAL = (42, 157, 143)
GREY = (90, 100, 112)
DARK = (30, 40, 52)
LIGHT = (242, 245, 248)

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=16)
pdf.add_page()
pdf.set_margins(18, 16, 18)
ANCHO = 174  # ancho util


def h1(txt):
    pdf.set_font("Helvetica", "B", 19); pdf.set_text_color(*NAVY)
    pdf.multi_cell(ANCHO, 8, txt, new_x="LMARGIN", new_y="NEXT")


def sub(txt):
    pdf.set_font("Helvetica", "", 10.5); pdf.set_text_color(*TEAL)
    pdf.multi_cell(ANCHO, 5.5, txt, new_x="LMARGIN", new_y="NEXT"); pdf.ln(2)


def h2(txt):
    pdf.ln(3)
    pdf.set_fill_color(*NAVY); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12.5)
    pdf.cell(ANCHO, 8, "  " + txt, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(2)


def p(txt):
    pdf.set_font("Helvetica", "", 10.5); pdf.set_text_color(*DARK)
    pdf.multi_cell(ANCHO, 5.2, txt, new_x="LMARGIN", new_y="NEXT"); pdf.ln(1.5)


def concepto(term, desc):
    pdf.set_fill_color(*LIGHT)
    pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(*TEAL)
    pdf.cell(ANCHO, 6, "  " + term, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_font("Helvetica", "", 10); pdf.set_text_color(*DARK)
    pdf.multi_cell(ANCHO, 5, "  " + desc, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(2)


def res(txt):
    pdf.set_font("Helvetica", "B", 10.5); pdf.set_text_color(*TEAL)
    pdf.multi_cell(ANCHO, 5.3, "Resultado: " + txt, new_x="LMARGIN", new_y="NEXT"); pdf.ln(2)


# ---------------- Portada ----------------
h1("Sistema Inteligente de Reposicion de Inventario")
sub("Guia del Hito 2 en palabras simples - que construimos, como y por que. "
    "Para alinearnos y para que puedas explicar cada parte en la defensa.")

h2("La idea en una frase")
p("El sistema decide, cada dia, que productos reponer en una tienda de supermercado. "
  "Para eso le dimos tres 'sentidos': ojos (ver productos en fotos), memoria (predecir "
  "cuanto se vendera) y lectura (entender los reclamos de clientes). Al final, una IA "
  "(Claude) junta todo y propone una recomendacion priorizada, que TU apruebas antes de "
  "que se envie.")

h2("Conceptos base (se repiten en todo el proyecto)")
concepto("Modelo de IA", "un programa que aprende patrones de muchos datos para hacer predicciones.")
concepto("Preentrenado", "un modelo que ya aprendio con millones de ejemplos; nosotros lo reutilizamos (como contratar a alguien con el ojo ya entrenado).")
concepto("Accuracy", "porcentaje de aciertos. MAE: error promedio, por cuantas unidades te equivocas (menor = mejor).")
concepto("Baseline / Navaja de Occam", "la solucion simple con la que comparamos. Si el modelo complejo no le gana, se dice y se discute (lo pide el profe).")

# ---------------- Fase 1 ----------------
h2("Fase 1 - Los OJOS: reconocer productos en fotos")
p("Que hace: le muestras la foto de un producto y adivina que es (manzana, pan, etc.).")
concepto("CNN (ej. ResNet50)", "IA que mira la imagen por pedacitos: bordes, texturas, formas. Es la forma clasica de 'ver' con IA.")
concepto("ViT (Vision Transformer)", "IA mas moderna: parte la foto en parches y 'presta atencion' a los importantes.")
concepto("Extractor de caracteristicas", "usamos la red preentrenada para convertir cada foto en una lista de numeros, y encima ponemos un clasificador simple. Asi corre rapido y sin GPU.")
res("baseline por color 32% -> ResNet 85% -> ViT 87% (gano). La IA aplasta a lo simple.")

# ---------------- Fase 2 ----------------
h2("Fase 2 - La MEMORIA: predecir cuanto se vendera")
p("Que hace: predice la demanda de cada producto los proximos 7 dias, para decidir si hay que reponer.")
concepto("Serie temporal", "datos que avanzan en el tiempo (las ventas de cada dia).")
concepto("Holt-Winters (tu modelo del Hito 1)", "una formula clasica que mira 3 cosas: nivel (cuanto se vende), tendencia (si sube o baja) y estacionalidad (el patron de la semana).")
concepto("LSTM / GRU", "redes neuronales CON MEMORIA: van leyendo la serie dia a dia y recuerdan lo que paso antes para predecir lo que viene. Son 'Deep Learning'.")
res("Holt-Winters MAE 7,34 -> LSTM 6,46 (mejor, le gana en 14 de 20 productos).")

# ---------------- Fase 3 ----------------
h2("Fase 3 - La LECTURA: entender los reclamos (NLP)")
p("Que hace: lee reclamos de clientes (en PDF) y entiende de que se quejan, para subir la "
  "prioridad de los productos mas reclamados.")
concepto("NLP", "procesamiento de lenguaje natural: IA que entiende texto.")
concepto("Transformer", "la arquitectura de IA detras de ChatGPT y Claude. Usa 'atencion': decide que palabras son las importantes.")
concepto("Embeddings", "convertir cada frase en numeros que capturan su SIGNIFICADO. Frases parecidas -> numeros parecidos. Permite buscar por significado, no por palabra exacta.")
concepto("RAG", "en vez de que la IA invente, primero BUSCA los reclamos relevantes y responde citando la fuente. Es el truco anti-alucinacion.")
res("reglas por palabra clave 89% -> Transformer 96%.")

# ---------------- Fase 4 ----------------
h2("Fase 4 - JUNTAR TODO: la orquestacion")
p("Que hace: conecta los 3 modelos en un solo flujo que corre solo (en la plataforma n8n).")
concepto("n8n", "la plataforma donde se arma el flujo de pasos (leer datos, llamar modelos, enviar correo...).")
concepto("Servicio y HTTP", "un programa en TU PC que tiene los 3 modelos. n8n lo 'llama' por internet. HTTP es el idioma con que dos programas se hablan (uno pregunta, el otro responde).")
concepto("Tunel (ngrok)", "le da una direccion publica a tu PC, para que n8n (que vive en internet) pueda alcanzar tu servicio.")
concepto("Control humano", "antes de hacer algo, el sistema te manda la recomendacion por Telegram y ESPERA tu aprobacion. Nada critico se hace solo.")
p("Flujo completo: lee ventas (Google Sheets) -> pronostica con el LSTM + trae los reclamos "
  "-> Claude redacta UNA recomendacion integrada -> te pide aprobar por Telegram -> si "
  "apruebas: correo (Gmail) + Telegram + registro + se actualiza el tablero.")

# ---------------- Fase 5 ----------------
h2("Fase 5 - El TABLERO (salida en HTML)")
p("Que hace: una pagina web que muestra los resultados.")
concepto("Dashboard", "panel visual con KPIs, graficos y tablas.")
concepto("Dos versiones", "una PUBLICADA (estatica, para mostrar/entregar) y una EN VIVO (servida por tu PC) que se actualiza con cada corrida y permite probar los modelos: subir una foto o escribir un reclamo y ver el resultado al instante.")

# ---------------- Fase 6 ----------------
h2("Fase 6 - NEGOCIO y riesgos")
p("Que hace: estima cuanto plata ahorra el sistema y que riesgos tiene.")
concepto("ROI (retorno de inversion)", "beneficio vs costo. Estimado: beneficio ~$260.000/mes (quiebres evitados + horas ahorradas), costo ~$26.000/mes -> ROI aprox 9x.")
concepto("Riesgos y controles", "errores del modelo (comparamos vs baseline + revision humana), alucinaciones del LLM (recibe solo resultados calculados, salida en JSON, RAG que cita la fuente), datos sensibles (flujo sin credenciales, reclamos simulados).")

# ---------------- Cierre ----------------
h2("En resumen: los 11 requisitos del profe, cumplidos")
p("1) LLM (Claude)  -  2) Codigo Python  -  3) Serie temporal (LSTM)  -  4) Imagenes (ViT)  -  "
  "5) Transformer/NLP (RAG)  -  6) Automatizacion (n8n)  -  7) Contexto industrial (retail)  -  "
  "8) Datos (M5 Walmart + reclamos)  -  9) Tablero (HTML)  -  10) Negocio y etica (ROI + riesgos)  -  "
  "11) Notificaciones (Gmail + Telegram).")
p("Idea para recordar: Fase 1 = ojos, Fase 2 = memoria, Fase 3 = lectura, Fase 4 = juntar "
  "todo con control humano, Fase 5 = mostrarlo, Fase 6 = el valor de negocio.")

pdf.output(OUT)
print("PDF generado:", OUT)
