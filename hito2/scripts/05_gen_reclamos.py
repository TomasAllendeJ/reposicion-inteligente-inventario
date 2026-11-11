# -*- coding: utf-8 -*-
"""
Hito 2 - Genera un set SIMULADO de reclamos/resenas de clientes.

Supuesto documentado (R8): no tenemos acceso a los reclamos reales de la
tienda, asi que generamos un conjunto realista con plantillas por categoria y
productos tipicos de supermercado. Cada reclamo trae su categoria y sentimiento
"verdaderos" para poder EVALUAR despues la clasificacion.

Salida:
  reclamos/reclamos.csv            (con etiquetas, para evaluar)
  reclamos/reclamos_clientes.pdf   (documento no estructurado = entrada del sistema)

Uso:
  python 05_gen_reclamos.py <out_dir>
"""
import os
import sys
import csv
import random
from datetime import date, timedelta
from fpdf import FPDF

random.seed(42)

PRODUCTOS = ["leche", "pan", "huevos", "arroz", "fideos", "aceite", "cafe",
             "azucar", "yogur", "queso", "jamon", "bebida cola", "agua mineral",
             "cerveza", "detergente", "papel higienico", "galletas", "cereal",
             "mantequilla", "atun en lata"]

# Plantillas por categoria. 4 categorias negativas + 1 positiva.
PLANTILLAS = {
    "quiebre_stock": [
        "Hace semanas que no encuentro {p}, siempre esta agotado.",
        "Vine tres veces y nunca hay {p} en la gondola.",
        "Otra vez sin {p}, es imposible comprarlo en esta tienda.",
        "Nunca tienen {p}, me tengo que ir a otro supermercado.",
        "Llevo un mes buscando {p} y jamas hay stock.",
        "El {p} esta permanentemente sin reposicion, muy molesto.",
    ],
    "calidad": [
        "El {p} que compre estaba vencido.",
        "Compre {p} en mal estado, tuve que botarlo.",
        "El {p} venia con el envase roto y aplastado.",
        "El {p} tenia mal sabor, parecia viejo.",
        "Me vendieron {p} en mal estado, pesima calidad.",
    ],
    "precio": [
        "El {p} subio demasiado de precio este mes.",
        "El {p} esta mucho mas caro que en la competencia.",
        "Me cobraron el {p} mas caro que el precio marcado en gondola.",
        "Los precios del {p} son un abuso ultimamente.",
    ],
    "atencion": [
        "Pesima atencion, nadie supo decirme donde estaba el {p}.",
        "Las cajas con fila eterna y faltaba personal.",
        "El cajero fue grosero cuando pregunte por el {p}.",
        "Nadie me ayudo a encontrar el {p}, muy mal servicio.",
    ],
    "positivo": [
        "Excelente variedad de {p}, siempre fresco.",
        "Muy buena atencion, encontre el {p} al tiro.",
        "Me encanta que siempre haya {p} en oferta.",
        "Felicitaciones, el {p} siempre esta bien surtido.",
    ],
}
SENTIMIENTO = {"quiebre_stock": "negativo", "calidad": "negativo",
               "precio": "negativo", "atencion": "negativo", "positivo": "positivo"}

# Pesos: mas reclamos de quiebre (es el foco del proyecto de reposicion)
PESOS = {"quiebre_stock": 0.40, "calidad": 0.20, "precio": 0.15,
         "atencion": 0.12, "positivo": 0.13}


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "reclamos"
    os.makedirs(out_dir, exist_ok=True)
    n = 90
    hoy = date(2026, 11, 10)

    cats = list(PESOS.keys())
    pesos = [PESOS[c] for c in cats]
    filas = []
    for i in range(n):
        cat = random.choices(cats, weights=pesos)[0]
        prod = random.choice(PRODUCTOS)
        texto = random.choice(PLANTILLAS[cat]).format(p=prod)
        fecha = hoy - timedelta(days=random.randint(0, 60))
        filas.append({"id": f"R{i+1:03d}", "fecha": fecha.isoformat(),
                      "producto": prod, "texto": texto,
                      "categoria": cat, "sentimiento": SENTIMIENTO[cat]})
    filas.sort(key=lambda r: r["fecha"])

    # CSV con etiquetas (para evaluar la clasificacion)
    csv_path = os.path.join(out_dir, "reclamos.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "fecha", "producto", "texto",
                                          "categoria", "sentimiento"])
        w.writeheader(); w.writerows(filas)

    # PDF = documento no estructurado (la ENTRADA que el sistema debera leer)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Reclamos y resenas de clientes - Tienda CA_1", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Documento interno simulado para el Hito 2 (buzon de atencion al cliente).",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    for r in filas:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"[{r['id']}]  {r['fecha']}  -  {r['producto']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, r["texto"])
        pdf.ln(1)
    pdf_path = os.path.join(out_dir, "reclamos_clientes.pdf")
    pdf.output(pdf_path)

    # Resumen por categoria
    from collections import Counter
    print(f"Generados {n} reclamos.")
    for c, k in Counter(r["categoria"] for r in filas).most_common():
        print(f"  {c:15s}: {k}")
    print("Guardado:", csv_path)
    print("Guardado:", pdf_path)


if __name__ == "__main__":
    main()
