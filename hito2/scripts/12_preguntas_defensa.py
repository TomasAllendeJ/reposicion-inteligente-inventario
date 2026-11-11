# -*- coding: utf-8 -*-
"""Genera la hoja de Preguntas y Respuestas para la defensa (Word)."""
import os
from docx import Document
from docx.shared import Pt, RGBColor

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "Preguntas_Defensa.docx")
NAVY = RGBColor(0x0F, 0x24, 0x44)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
ORANGE = RGBColor(0xB5, 0x65, 0x1D)

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)

t = doc.add_paragraph(); r = t.add_run("Hoja de preparación para la defensa — Hito 2")
r.bold = True; r.font.size = Pt(18); r.font.color.rgb = NAVY
s = doc.add_paragraph(); r = s.add_run("Preguntas típicas del profesor y respuestas listas (en tus palabras). "
                                       "Recuerda: responde con calma, apóyate en los números y sé honesto con las limitaciones.")
r.font.size = Pt(10); r.font.color.rgb = ORANGE


def seccion(txt):
    p = doc.add_paragraph(); r = p.add_run(txt); r.bold = True; r.font.size = Pt(13); r.font.color.rgb = TEAL
    p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(2)


def qa(q, a):
    pq = doc.add_paragraph(); rq = pq.add_run("P: " + q); rq.bold = True; rq.font.size = Pt(10.5); rq.font.color.rgb = NAVY
    pq.paragraph_format.space_before = Pt(6); pq.paragraph_format.space_after = Pt(1)
    pa = doc.add_paragraph(); ra = pa.add_run("R: " + a); ra.font.size = Pt(10.5)
    pa.paragraph_format.space_after = Pt(3)


seccion("Sobre el proyecto en general")
qa("¿De qué trata tu proyecto y quién es el usuario?",
   "Es un sistema que decide, cada día, qué productos reponer en una tienda de retail. El usuario es el "
   "encargado de compras, que antes decidía 'a ojo'. El sistema le entrega una recomendación priorizada, "
   "apoyada en tres modelos de IA, y él aprueba antes de que se envíe.")
qa("¿Cuál es el indicador de negocio?",
   "Quiebres de stock evitados y capital inmovilizado reducido. Es decir, menos ventas perdidas por falta "
   "de producto y menos plata inmovilizada en productos que no rotan.")
qa("¿Por qué comparas cada modelo con uno simple (Navaja de Occam)?",
   "Porque hay que demostrar que el modelo complejo vale la pena. Si una solución simple da casi lo mismo, "
   "no se justifica la complejidad. En mi caso, los tres modelos le ganan claramente a su alternativa simple, "
   "y eso está medido.")

seccion("Serie temporal (LSTM)")
qa("¿Qué es Holt-Winters y qué es un LSTM?",
   "Holt-Winters es una fórmula clásica que descompone la serie en nivel, tendencia y patrón semanal. El LSTM "
   "es una red neuronal con memoria: lee la serie día a día y recuerda lo anterior para predecir lo que viene. "
   "Es Deep Learning, aprende patrones más complejos.")
qa("¿Cómo mediste que el LSTM es mejor?",
   "Con el MAE (error absoluto medio: por cuántas unidades me equivoco en promedio) sobre 28 días de prueba, "
   "el mismo protocolo del Hito 1. Holt-Winters dio 7,34 y el LSTM 6,46, ganándole en 14 de 20 productos.")
qa("¿Qué usa el LSTM como entrada?",
   "La venta escalada de cada día más features de calendario: el día de la semana y si es día SNAP (un "
   "beneficio que sube el consumo). Eso le da información que el clásico no aprovecha tan bien.")
qa("¿Por qué el LSTM corre fuera de n8n?",
   "Porque n8n no permite importar librerías pesadas como PyTorch en su nodo de código. Por eso los modelos "
   "de Deep Learning corren en un servicio Python aparte, que n8n llama por HTTP.")

seccion("Imágenes (ViT)")
qa("¿Qué es una CNN y qué es un ViT? ¿Por qué ganó el ViT?",
   "La CNN (ResNet) mira la imagen por pedacitos: bordes, texturas, formas. El ViT (Vision Transformer) parte "
   "la foto en parches y presta atención a los importantes. En mis datos el ViT dio 87% y la CNN 85%; ambos "
   "muy por encima del baseline de color (32%).")
qa("¿Qué significa 'preentrenado' y 'extractor de características'?",
   "Preentrenado: la red ya aprendió a ver con millones de imágenes; yo la reutilizo. Extractor de "
   "características: en vez de reentrenar todo, uso la red para convertir cada foto en un vector de números y "
   "encima pongo un clasificador simple. Así corre rápido y sin GPU.")

seccion("Texto / NLP (Transformer + RAG)")
qa("¿Qué es un Transformer y qué son los embeddings?",
   "El Transformer es la arquitectura detrás de ChatGPT y Claude; usa 'atención' para decidir qué palabras "
   "importan. Los embeddings son convertir una frase en números que capturan su significado: frases "
   "parecidas quedan con números parecidos, así puedo buscar por sentido y no por palabra exacta.")
qa("¿Qué es RAG y para qué lo usas?",
   "RAG es Retrieval-Augmented Generation: en vez de que el LLM invente, primero BUSCA los reclamos "
   "relevantes y recién ahí responde citando la fuente. Es mi control anti-alucinación en el texto.")
qa("¿Por qué los reclamos son simulados?",
   "Porque no tengo acceso a los reclamos reales de la tienda. Los generé con un supuesto documentado, "
   "realista en su distribución (la mayoría de quiebre de stock). El enunciado permite datos simulados si se "
   "explican, y así lo hice.")

seccion("El LLM (Claude) y la integración")
qa("¿Cómo evitas que Claude invente (alucine)?",
   "Varias capas: Claude recibe solo los resultados ya calculados, no los datos crudos; responde en un JSON "
   "estructurado con campos fijos; usa RAG para citar la fuente de los reclamos; y si un dato es dudoso marca "
   "'revisión humana'. Además, nada se envía sin mi aprobación.")
qa("¿Qué es el 'gateway' de Claude?",
   "Es la forma de usar Claude dentro de n8n con los créditos de la plataforma, sin necesidad de una API key "
   "propia. Por eso en el flujo el modelo no pide credenciales.")
qa("¿Qué es el punto de control humano?",
   "Antes de hacer cualquier acción, el sistema me manda la recomendación por Telegram y ESPERA que yo "
   "apruebe. Si rechazo, no se envía nada. El sistema asiste, no reemplaza al encargado.")

seccion("Arquitectura y herramientas")
qa("¿Qué es el servicio y qué es HTTP?",
   "El servicio es un programa en mi PC que tiene los tres modelos. HTTP es el idioma con que dos programas "
   "se hablan por internet: n8n le pregunta ('dame el pronóstico') y el servicio responde.")
qa("¿Qué es ngrok y por qué lo usas?",
   "Mi n8n es cloud (vive en internet) y mi servicio corre en mi PC, que no tiene dirección pública. ngrok le "
   "da una dirección pública temporal a mi PC, como un puente, para que n8n pueda alcanzarlo.")

seccion("Tablero")
qa("¿El tablero es en vivo?",
   "Hay dos: uno publicado (estático, para mostrar) y uno en vivo servido por mi propio servicio. El en vivo "
   "se actualiza con cada corrida del flujo y permite probar los modelos: subir una foto o escribir un "
   "reclamo y ver el resultado al instante.")

seccion("Negocio y riesgos")
qa("¿Cómo calculaste el ROI? ¿Es realista?",
   "Con supuestos explícitos y conservadores: beneficio por quiebres evitados (~5% menos de quiebres) más "
   "horas ahorradas al encargado, contra el costo de operar. Da un beneficio de ~$260.000/mes y un ROI de "
   "unas 9 veces. Soy honesto: el ROI es alto en parte porque la IA no cuesta (usa el gateway de n8n).")
qa("¿Cuáles son los riesgos del sistema?",
   "Errores del modelo (lo controlo comparando con baseline y con la marca de revisión humana), alucinaciones "
   "del LLM (lo controlo con la salida JSON y el RAG), y datos sensibles (el flujo se exporta sin credenciales "
   "y los reclamos son simulados).")

seccion("Datos y limitaciones")
qa("¿De dónde salen los datos? ¿El stock es real?",
   "Las ventas son reales (dataset M5 de Walmart, tienda CA_1). Las imágenes son del Grocery Store Dataset. "
   "El stock actual lo simulo con supuestos, porque no tengo el sistema de inventario de la tienda; lo dejo "
   "documentado como limitación.")
qa("¿Qué mejorarías en el futuro?",
   "Mapear los reclamos a los códigos SKU exactos, desplegar el servicio en un host estable en vez de un "
   "túnel local, y entrenar el LSTM con más features (promociones, feriados). También probar más modelos de "
   "imágenes y de texto.")

doc.save(OUT)
print("Hoja de Q&A generada:", OUT)
