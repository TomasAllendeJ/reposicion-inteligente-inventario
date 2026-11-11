# -*- coding: utf-8 -*-
"""
R4 - Paso 2: Entrenar un clasificador simple sobre las caracteristicas y COMPARAR
los 3 enfoques:
  1) Baseline (histograma de color)  <- la "alternativa simple" (Navaja de Occam)
  2) CNN preentrenada (ResNet50)
  3) Transformer de vision (ViT)

Sobre cada conjunto de caracteristicas entrenamos una Regresion Logistica
(clasificador lineal simple y explicable). Medimos en el conjunto de TEST con
accuracy y F1 macro. Guardamos el mejor modelo para el servicio y un grafico.

Uso:
  python 02_train_compare.py <out_dir>
Ejemplo:
  python 02_train_compare.py ../outputs
"""
import os
import sys
import json
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix


def main():
    out_dir = sys.argv[1]
    tr = np.load(os.path.join(out_dir, "features_train.npz"))
    te = np.load(os.path.join(out_dir, "features_test.npz"))
    clases = open(os.path.join(out_dir, "clases.txt"), encoding="utf-8").read().splitlines()

    y_tr, y_te = tr["y"], te["y"]
    enfoques = {
        "Baseline (histograma de color)": ("hist", "baseline_hist"),
        "CNN preentrenada (ResNet50)": ("resnet", "resnet50"),
        "Transformer de vision (ViT)": ("vit", "vit_b_16"),
    }

    resultados = []
    modelos = {}
    for nombre, (clave, backbone) in enfoques.items():
        X_tr, X_te = tr[clave], te[clave]
        # Escalar + Regresion Logistica (clasificador lineal simple)
        modelo = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0, n_jobs=-1),
        )
        modelo.fit(X_tr, y_tr)
        pred = modelo.predict(X_te)
        acc = accuracy_score(y_te, pred)
        f1 = f1_score(y_te, pred, average="macro")
        resultados.append({"enfoque": nombre, "backbone": backbone,
                           "accuracy": round(float(acc), 4), "f1_macro": round(float(f1), 4),
                           "dim": int(X_tr.shape[1])})
        modelos[backbone] = modelo
        print(f"{nombre:35s}  acc={acc:.3f}  F1={f1:.3f}  (dim {X_tr.shape[1]})")

    # Ordenar y elegir el mejor
    resultados.sort(key=lambda r: r["accuracy"], reverse=True)
    mejor = resultados[0]
    print(f"\nMEJOR MODELO: {mejor['enfoque']}  (accuracy {mejor['accuracy']})")

    # Guardar metricas
    with open(os.path.join(out_dir, "metrics_r4.json"), "w", encoding="utf-8") as f:
        json.dump({"n_clases": len(clases), "n_train": int(len(y_tr)),
                   "n_test": int(len(y_te)), "resultados": resultados,
                   "mejor_backbone": mejor["backbone"]}, f, ensure_ascii=False, indent=2)

    # Guardar el mejor modelo + metadatos para el servicio FastAPI
    joblib.dump({"modelo": modelos[mejor["backbone"]], "backbone": mejor["backbone"],
                 "clases": clases}, os.path.join(out_dir, "modelo_productos.joblib"))
    print("Guardado modelo_productos.joblib y metrics_r4.json")

    # Grafico de comparacion
    nombres = [r["enfoque"].replace(" (", "\n(") for r in resultados]
    accs = [r["accuracy"] for r in resultados]
    colores = ["#2A9D8F" if r["backbone"] == mejor["backbone"] else "#9FB4CB" for r in resultados]
    plt.figure(figsize=(7, 4.2))
    barras = plt.bar(nombres, accs, color=colores)
    plt.ylim(0, 1); plt.ylabel("Accuracy (test)")
    plt.title("R4 - Comparacion de modelos de reconocimiento de productos")
    for b, a in zip(barras, accs):
        plt.text(b.get_x() + b.get_width()/2, a + 0.02, f"{a:.2f}", ha="center", fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "r4_comparacion.png"), dpi=150)
    print("Guardado r4_comparacion.png")

    # Matriz de confusion del mejor (solo guardada, util para el informe)
    mejor_modelo = modelos[mejor["backbone"]]
    clave_mejor = {"baseline_hist": "hist", "resnet50": "resnet", "vit_b_16": "vit"}[mejor["backbone"]]
    pred = mejor_modelo.predict(te[clave_mejor])
    cm = confusion_matrix(y_te, pred)
    plt.figure(figsize=(9, 8))
    plt.imshow(cm, cmap="Blues"); plt.colorbar()
    plt.title(f"Matriz de confusion - {mejor['enfoque']}")
    plt.xlabel("Prediccion"); plt.ylabel("Real")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "r4_confusion.png"), dpi=130)
    print("Guardado r4_confusion.png")


if __name__ == "__main__":
    main()
