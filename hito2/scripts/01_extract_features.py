# -*- coding: utf-8 -*-
"""
R4 - Paso 1: Extraer caracteristicas de las imagenes del Grocery Store Dataset.

Idea: NO reentrenamos las redes (seria lento y necesitaria GPU). Usamos los
modelos preentrenados (ResNet50 y ViT) como "extractores de caracteristicas":
cada imagen entra a la red y sacamos el vector que la red genera justo antes de
su capa final. Ese vector resume lo que la red "ve". Despues (paso 2) entrenamos
un clasificador simple sobre esos vectores.

Tambien calculamos una caracteristica "tonta" (histograma de color) que servira
como BASELINE simple (Navaja de Occam): solo mira colores, no entiende objetos.

Uso:
  python 01_extract_features.py <dataset_dir> <out_dir> [coarse|fine] [limite_por_split]

Ejemplo:
  python 01_extract_features.py ../data/GroceryStoreDataset/dataset ../outputs coarse
"""
import os
import sys
import csv
import time
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet50, ResNet50_Weights, vit_b_16, ViT_B_16_Weights


def leer_clases(dataset_dir, granularidad):
    """Lee classes.csv y devuelve {id: nombre} para la granularidad elegida."""
    col_id = "Coarse Class ID (int)" if granularidad == "coarse" else "Class ID (int)"
    col_nombre = "Coarse Class Name (str)" if granularidad == "coarse" else "Class Name (str)"
    id2nombre = {}
    with open(os.path.join(dataset_dir, "classes.csv"), encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            id2nombre[int(fila[col_id])] = fila[col_nombre]
    return id2nombre


def leer_split(dataset_dir, nombre_txt, granularidad):
    """Lee train.txt/test.txt -> lista de (ruta_imagen, etiqueta_int)."""
    col = 2 if granularidad == "coarse" else 1  # columnas: ruta, id_fino, id_grueso
    items = []
    with open(os.path.join(dataset_dir, nombre_txt), encoding="utf-8") as f:
        for linea in f:
            partes = [p.strip() for p in linea.strip().split(",")]
            if len(partes) < 3:
                continue
            ruta = os.path.join(dataset_dir, partes[0])
            etiqueta = int(partes[col])
            items.append((ruta, etiqueta))
    return items


def histograma_color(img_rgb, bins=32):
    """Baseline simple: histograma de color por canal (R, G, B), normalizado."""
    arr = np.asarray(img_rgb)  # (H, W, 3) uint8
    vec = []
    for c in range(3):
        h, _ = np.histogram(arr[:, :, c], bins=bins, range=(0, 255))
        vec.append(h)
    vec = np.concatenate(vec).astype("float32")
    total = vec.sum()
    return vec / total if total > 0 else vec  # normaliza para que no dependa del tamano


def construir_modelos():
    """Carga ResNet50 y ViT preentrenados en ImageNet, sin su capa final."""
    resnet = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    resnet.fc = nn.Identity()      # quitamos la capa de clasificacion -> vector de 2048
    resnet.eval()

    vit = vit_b_16(weights=ViT_B_16_Weights.IMAGENET1K_V1)
    vit.heads = nn.Identity()      # quitamos la cabeza -> vector de 768
    vit.eval()
    return resnet, vit


def main():
    dataset_dir = sys.argv[1]
    out_dir = sys.argv[2]
    granularidad = sys.argv[3] if len(sys.argv) > 3 else "coarse"
    limite = int(sys.argv[4]) if len(sys.argv) > 4 else None
    batch = 16

    os.makedirs(out_dir, exist_ok=True)
    device = torch.device("cpu")
    torch.set_num_threads(os.cpu_count() or 4)

    id2nombre = leer_clases(dataset_dir, granularidad)
    n_clases = len(id2nombre)
    print(f"Granularidad: {granularidad} | {n_clases} clases")

    # Preprocesamiento comun para ambas redes (tamano 224 + normalizacion de ImageNet)
    tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    print("Cargando modelos preentrenados (la primera vez descarga los pesos)...")
    resnet, vit = construir_modelos()
    resnet.to(device); vit.to(device)

    for nombre_txt, split in [("train.txt", "train"), ("test.txt", "test")]:
        items = leer_split(dataset_dir, nombre_txt, granularidad)
        if limite:
            items = items[:limite]
        n = len(items)
        print(f"\n== {split}: {n} imagenes ==")

        feat_hist, feat_resnet, feat_vit, etiquetas = [], [], [], []
        t0 = time.time()
        buffer_tensores, buffer_idx = [], []

        def procesar_buffer():
            if not buffer_tensores:
                return
            lote = torch.stack(buffer_tensores).to(device)
            with torch.no_grad():
                fr = resnet(lote).cpu().numpy()
                fv = vit(lote).cpu().numpy()
            feat_resnet.extend(fr)
            feat_vit.extend(fv)
            buffer_tensores.clear(); buffer_idx.clear()

        for i, (ruta, etiqueta) in enumerate(items):
            try:
                img = Image.open(ruta).convert("RGB")
            except Exception as e:
                print(f"  (saltada {ruta}: {e})")
                continue
            feat_hist.append(histograma_color(img))
            etiquetas.append(etiqueta)
            buffer_tensores.append(tf(img)); buffer_idx.append(i)
            if len(buffer_tensores) >= batch:
                procesar_buffer()
            if (i + 1) % 200 == 0:
                print(f"  {i+1}/{n}  ({time.time()-t0:.0f}s)")
        procesar_buffer()

        X_hist = np.array(feat_hist, dtype="float32")
        X_resnet = np.array(feat_resnet, dtype="float32")
        X_vit = np.array(feat_vit, dtype="float32")
        y = np.array(etiquetas, dtype="int64")
        print(f"  hist {X_hist.shape} | resnet {X_resnet.shape} | vit {X_vit.shape}")

        np.savez_compressed(
            os.path.join(out_dir, f"features_{split}.npz"),
            hist=X_hist, resnet=X_resnet, vit=X_vit, y=y,
        )
        print(f"  guardado features_{split}.npz ({time.time()-t0:.0f}s)")

    # Guardamos los nombres de clase para el paso 2 y el servicio
    nombres = [id2nombre[i] for i in range(n_clases)]
    with open(os.path.join(out_dir, "clases.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(nombres))
    print("\nListo. Clases guardadas en clases.txt")


if __name__ == "__main__":
    main()
