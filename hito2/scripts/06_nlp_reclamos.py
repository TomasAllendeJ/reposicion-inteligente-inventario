# -*- coding: utf-8 -*-
"""
Hito 2 - R5 Transformer / NLP sobre los reclamos de clientes.

Hace 3 cosas:
  1) CLASIFICACION: baseline de reglas (palabras clave) vs Transformer
     (embeddings de un modelo tipo BERT + Regresion Logistica). Compara.
  2) RAG: convierte cada reclamo en un embedding y permite BUSQUEDA SEMANTICA;
     arma el contexto (citando el id del reclamo) para que el LLM responda
     sin inventar.
  3) SENAL DE NEGOCIO: cuenta los reclamos de 'quiebre de stock' por producto
     -> esto sube la prioridad de reposicion en la orquestacion (Fase 4).

Lee el PDF (documento no estructurado) y usa el CSV solo para las etiquetas
verdaderas (evaluacion).

Uso:
  python 06_nlp_reclamos.py <carpeta_reclamos> <out_dir>
"""
import os
import re
import sys
import json
import csv as csvmod
import numpy as np
import joblib

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

MODELO_EMB = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# --- Baseline: reglas por palabra clave (la "regla fija" de Navaja de Occam) ---
REGLAS = [
    ("quiebre_stock", ["agotado", "no hay", "sin stock", "sin reposicion",
                        "nunca tienen", "no encuentro", "jamas hay", "nunca hay"]),
    ("calidad", ["vencido", "mal estado", "roto", "aplastado", "mal sabor",
                 "viejo", "pesima calidad"]),
    ("precio", ["caro", "precio", "abuso", "subio", "cobraron"]),
    ("atencion", ["atencion", "cajero", "fila", "personal", "servicio", "grosero", "ayudo"]),
    ("positivo", ["excelente", "felicitaciones", "encanta", "fresco", "surtido", "oferta"]),
]


def clasificar_reglas(texto):
    t = texto.lower()
    for cat, claves in REGLAS:
        if any(k in t for k in claves):
            return cat
    return "otros"


def leer_pdf(pdf_path):
    """Extrae del PDF la lista de (id, texto) de cada reclamo."""
    reader = PdfReader(pdf_path)
    full = "\n".join(p.extract_text() or "" for p in reader.pages)
    # Cada reclamo empieza con [Rxxx] fecha - producto, y en la linea siguiente el texto
    bloques = re.split(r"\[(R\d{3})\]", full)
    items = []
    for i in range(1, len(bloques), 2):
        rid = bloques[i]
        cuerpo = bloques[i + 1]
        # el texto del reclamo es lo que viene despues del guion de la cabecera
        lineas = [l.strip() for l in cuerpo.strip().split("\n") if l.strip()]
        # linea 0 = resto de la cabecera (fecha - producto); el resto = texto
        texto = " ".join(lineas[1:]) if len(lineas) > 1 else ""
        items.append((rid, texto))
    return items


def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "reclamos"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    os.makedirs(out_dir, exist_ok=True)

    # 1) Leer el PDF (documento no estructurado) y las etiquetas del CSV
    print("[1/5] Leyendo PDF de reclamos...")
    items = leer_pdf(os.path.join(carpeta, "reclamos_clientes.pdf"))
    etiquetas, productos = {}, {}
    with open(os.path.join(carpeta, "reclamos.csv"), encoding="utf-8") as f:
        for r in csvmod.DictReader(f):
            etiquetas[r["id"]] = r["categoria"]
            productos[r["id"]] = r["producto"]
    ids = [rid for rid, _ in items if rid in etiquetas]
    textos = [t for rid, t in items if rid in etiquetas]
    y = [etiquetas[rid] for rid in ids]
    print(f"      {len(textos)} reclamos leidos del PDF")

    # 2) Embeddings con el Transformer (modelo multilingue tipo BERT)
    print("[2/5] Calculando embeddings con el Transformer (descarga la 1a vez)...")
    emb = SentenceTransformer(MODELO_EMB)
    X = emb.encode(textos, normalize_embeddings=True, show_progress_bar=False)
    print(f"      embeddings {X.shape}")

    # 3) CLASIFICACION: baseline reglas vs Transformer+LogReg (mismo test)
    print("[3/5] Comparando clasificacion...")
    idx_tr, idx_te = train_test_split(range(len(y)), test_size=0.3,
                                      random_state=42, stratify=y)
    y_te = [y[i] for i in idx_te]

    # baseline reglas (no necesita entrenar)
    pred_reglas = [clasificar_reglas(textos[i]) for i in idx_te]
    acc_reglas = accuracy_score(y_te, pred_reglas)
    f1_reglas = f1_score(y_te, pred_reglas, average="macro")

    # Transformer + Regresion Logistica
    clf = LogisticRegression(max_iter=2000, C=5.0)
    clf.fit(X[idx_tr], [y[i] for i in idx_tr])
    pred_emb = clf.predict(X[idx_te])
    acc_emb = accuracy_score(y_te, pred_emb)
    f1_emb = f1_score(y_te, pred_emb, average="macro")

    print(f"  Baseline (reglas)      acc={acc_reglas:.3f}  F1={f1_reglas:.3f}")
    print(f"  Transformer (embed+LR) acc={acc_emb:.3f}  F1={f1_emb:.3f}")

    # Modelo final entrenado con TODO, para el servicio
    clf_full = LogisticRegression(max_iter=2000, C=5.0).fit(X, y)

    # 4) RAG: busqueda semantica (demostracion)
    print("[4/5] RAG - busqueda semantica de ejemplo...")
    def buscar(consulta, k=3):
        q = emb.encode([consulta], normalize_embeddings=True)[0]
        sims = X @ q                      # coseno (vectores normalizados)
        top = np.argsort(sims)[::-1][:k]
        return [(ids[i], textos[i], float(sims[i])) for i in top]

    demo_query = "productos que estan siempre agotados"
    ejemplos = buscar(demo_query, k=3)
    print(f"  Consulta: '{demo_query}'")
    for rid, txt, s in ejemplos:
        print(f"   [{rid}] ({s:.2f}) {txt}")

    # 5) Senal de negocio: presion de reclamos de quiebre por producto
    print("[5/5] Presion de reclamos de quiebre por producto...")
    pred_all = clf_full.predict(X)
    presion = {}
    for rid, cat in zip(ids, pred_all):
        if cat == "quiebre_stock":
            presion[productos[rid]] = presion.get(productos[rid], 0) + 1
    presion_orden = sorted(presion.items(), key=lambda x: x[1], reverse=True)
    for prod, n in presion_orden[:8]:
        print(f"   {prod:18s}: {n} reclamos de quiebre")

    # --- Guardar resultados ---
    with open(os.path.join(out_dir, "metrics_nlp.json"), "w", encoding="utf-8") as f:
        json.dump({
            "n_reclamos": len(textos),
            "clasificacion": {
                "baseline_reglas": {"accuracy": round(acc_reglas, 3), "f1_macro": round(f1_reglas, 3)},
                "transformer_embeddings": {"accuracy": round(acc_emb, 3), "f1_macro": round(f1_emb, 3)},
            },
            "rag_demo": {"consulta": demo_query,
                         "resultados": [{"id": r, "texto": t, "score": round(s, 3)} for r, t, s in ejemplos]},
            "presion_quiebre_por_producto": dict(presion_orden),
        }, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "presion_reclamos.csv"), "w", newline="", encoding="utf-8") as f:
        w = csvmod.writer(f); w.writerow(["producto", "reclamos_quiebre"])
        w.writerows(presion_orden)

    joblib.dump({"clf": clf_full, "modelo_emb": MODELO_EMB, "clases": list(clf_full.classes_)},
                os.path.join(out_dir, "modelo_reclamos.joblib"))
    # Guardar embeddings + ids para el RAG del servicio
    np.savez_compressed(os.path.join(out_dir, "rag_index.npz"),
                        X=X, ids=np.array(ids), textos=np.array(textos, dtype=object))
    print("\nGuardado: metrics_nlp.json, presion_reclamos.csv, modelo_reclamos.joblib, rag_index.npz")


if __name__ == "__main__":
    main()
