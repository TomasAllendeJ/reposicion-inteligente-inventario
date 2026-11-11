# -*- coding: utf-8 -*-
"""
Hito 2 - R10: Evaluacion de negocio (ROI) con SUPUESTOS EXPLICITOS.
Calcula el beneficio mensual (quiebres evitados + horas ahorradas), el costo de
operar el sistema y un ROI simple. Todo en CLP. Los supuestos estan arriba y son
conservadores; se documentan como estimacion (no datos reales de la tienda).

Uso:
  python 08_roi.py <csv_ventas> <out_dir>
"""
import os
import sys
import json
import pandas as pd

# ------------------------- SUPUESTOS (documentados) -------------------------
N_SKU = 20
DIAS_MES = 30
PRECIO_PROM = 1500          # CLP por unidad (producto de supermercado)
MARGEN = 0.25              # 25% de margen -> CLP 375 por unidad
TASA_QUIEBRE_SIN = 0.08    # 8% de SKU-dias con quiebre decidiendo "a ojo"
TASA_QUIEBRE_CON = 0.03    # 3% con el sistema (anticipa la reposicion)
FRAC_VENTA_PERDIDA = 0.5   # en un dia de quiebre se pierde ~50% de la demanda
HORAS_MANUAL_DIA = 1.0     # horas/dia que el encargado dedicaba a decidir a mano
COSTO_HORA = 4000          # CLP/hora del encargado de compras
# Costo de operar el sistema al mes
COSTO_N8N = 0              # gateway de IA incluido en los creditos de n8n
COSTO_HOSTING = 10000      # CLP: servidor del servicio de modelos
HORAS_MANTENCION = 2.0     # horas/mes de mantencion
COSTO_HORA_MANT = 8000     # CLP/hora (perfil data)


def main():
    csv_in = sys.argv[1]
    out_dir = sys.argv[2]
    # Demanda promedio diaria real por SKU (de los datos limpios)
    df = pd.read_csv(csv_in, parse_dates=["date"])
    dem_prom = float(df.groupby("item_id")["sales"].mean().mean())

    margen_u = PRECIO_PROM * MARGEN
    sku_dias_mes = N_SKU * DIAS_MES
    quiebres_evitados = (TASA_QUIEBRE_SIN - TASA_QUIEBRE_CON) * sku_dias_mes
    u_perdidas_por_quiebre = dem_prom * FRAC_VENTA_PERDIDA
    u_recuperadas_mes = quiebres_evitados * u_perdidas_por_quiebre
    beneficio_ventas = u_recuperadas_mes * margen_u

    horas_ahorradas_mes = HORAS_MANUAL_DIA * DIAS_MES
    beneficio_horas = horas_ahorradas_mes * COSTO_HORA

    beneficio_mes = beneficio_ventas + beneficio_horas
    costo_mes = COSTO_N8N + COSTO_HOSTING + HORAS_MANTENCION * COSTO_HORA_MANT
    neto_mes = beneficio_mes - costo_mes
    roi = (neto_mes / costo_mes) if costo_mes else None

    r = {
        "moneda": "CLP",
        "supuestos": {
            "n_sku": N_SKU, "demanda_prom_dia_sku": round(dem_prom, 1),
            "precio_prom": PRECIO_PROM, "margen": MARGEN, "margen_unidad": margen_u,
            "tasa_quiebre_sin": TASA_QUIEBRE_SIN, "tasa_quiebre_con": TASA_QUIEBRE_CON,
            "frac_venta_perdida": FRAC_VENTA_PERDIDA,
            "horas_manual_dia": HORAS_MANUAL_DIA, "costo_hora": COSTO_HORA,
        },
        "beneficio": {
            "quiebres_evitados_sku_dias_mes": round(quiebres_evitados, 1),
            "unidades_recuperadas_mes": round(u_recuperadas_mes, 1),
            "beneficio_ventas_mes": round(beneficio_ventas),
            "horas_ahorradas_mes": horas_ahorradas_mes,
            "beneficio_horas_mes": round(beneficio_horas),
            "beneficio_total_mes": round(beneficio_mes),
        },
        "costo": {
            "hosting_mes": COSTO_HOSTING, "mantencion_mes": round(HORAS_MANTENCION * COSTO_HORA_MANT),
            "gateway_ia": COSTO_N8N, "costo_total_mes": round(costo_mes),
        },
        "resultado": {
            "neto_mes": round(neto_mes), "roi_mensual": round(roi, 1) if roi else None,
            "beneficio_anual": round(beneficio_mes * 12), "costo_anual": round(costo_mes * 12),
            "neto_anual": round(neto_mes * 12),
        },
    }
    with open(os.path.join(out_dir, "roi.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)

    print("== ROI (CLP/mes) ==")
    print(f"  Demanda prom/dia por SKU (real): {dem_prom:.1f} u")
    print(f"  Beneficio ventas (quiebres evitados): {beneficio_ventas:,.0f}")
    print(f"  Beneficio horas ahorradas:            {beneficio_horas:,.0f}")
    print(f"  Beneficio total:                      {beneficio_mes:,.0f}")
    print(f"  Costo operar sistema:                 {costo_mes:,.0f}")
    print(f"  Neto mensual:                         {neto_mes:,.0f}")
    print(f"  ROI mensual:                          {roi:.1f}x  ({roi*100:.0f}%)")
    print(f"  Neto anual:                           {neto_mes*12:,.0f}")
    print("Guardado roi.json")


if __name__ == "__main__":
    main()
