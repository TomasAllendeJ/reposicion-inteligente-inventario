# -*- coding: utf-8 -*-
"""
forecast_core.py
------------------------------------------------------------------
Funciones de pronostico de demanda en PYTHON PURO (solo libreria estandar).
NO usa pandas ni statsmodels, por lo que este codigo se puede pegar
TAL CUAL en el nodo "Code" de n8n.

Contiene:
  - media_movil(...)          -> baseline simple (Navaja de Occam)
  - naive_estacional(...)     -> baseline ingenuo (mismo dia, semana pasada)
  - holt_winters(...)         -> modelo: tendencia + estacionalidad semanal
  - punto_de_reorden(...)     -> regla de reposicion de inventario

Todo trabaja con listas de numeros (no DataFrames), igual que en n8n.
------------------------------------------------------------------
"""

# ===============================================================
# BASELINE 1: Media movil
#   Pronostica los proximos H dias como el promedio de los ultimos
#   `ventana` dias observados. Es una linea plana (modelo simple).
# ===============================================================
def media_movil(historial, h=7, ventana=7):
    ultimos = historial[-ventana:]
    promedio = sum(ultimos) / len(ultimos)
    return [max(0.0, promedio) for _ in range(h)]


# ===============================================================
# BASELINE 2: Naive estacional
#   Pronostica cada dia futuro como lo que paso el MISMO dia de la
#   semana anterior. Baseline mas exigente para datos con patron semanal.
# ===============================================================
def naive_estacional(historial, h=7, periodo=7):
    pron = []
    for i in range(h):
        pron.append(max(0.0, historial[-periodo + (i % periodo)]))
    return pron


# ===============================================================
# MODELO: Holt-Winters aditivo (tendencia + estacionalidad semanal)
#   alpha -> suaviza el nivel
#   beta  -> suaviza la tendencia
#   gamma -> suaviza la estacionalidad
#   periodo = 7 (semana)
#
#   Ecuaciones (aditivas):
#     nivel_t   = alpha*(y_t - estacional) + (1-alpha)*(nivel + tendencia)
#     tend_t    = beta*(nivel_t - nivel_{t-1}) + (1-beta)*tend
#     estac_t   = gamma*(y_t - nivel_t) + (1-gamma)*estac
#   Pronostico h pasos:
#     y_(t+h) = nivel_t + h*tend_t + estacional[(t+h) mod periodo]
# ===============================================================
def holt_winters(historial, h=7, periodo=7, alpha=0.4, beta=0.05, gamma=0.3, phi=0.95):
    y = list(historial)
    n = len(y)
    if n < 2 * periodo:
        # Si hay poca historia, caemos al baseline simple (robustez)
        return media_movil(y, h=h, ventana=min(periodo, n))

    # --- Inicializacion ---
    # nivel inicial = promedio de la primera semana
    nivel = sum(y[:periodo]) / periodo
    # tendencia inicial = diferencia promedio entre la 2a y la 1a semana
    tendencia = (sum(y[periodo:2 * periodo]) - sum(y[:periodo])) / (periodo * periodo)
    # estacionalidad inicial = cuanto se desvia cada dia del nivel
    estacional = [y[i] - nivel for i in range(periodo)]

    # --- Recorrer la serie actualizando nivel, tendencia y estacionalidad ---
    for t in range(n):
        valor = y[t]
        idx = t % periodo
        nivel_ant = nivel
        nivel = alpha * (valor - estacional[idx]) + (1 - alpha) * (nivel + tendencia)
        tendencia = beta * (nivel - nivel_ant) + (1 - beta) * tendencia
        estacional[idx] = gamma * (valor - nivel) + (1 - gamma) * estacional[idx]

    # --- Pronosticar h pasos hacia adelante (con tendencia AMORTIGUADA) ---
    # phi<1 hace que la tendencia pese cada vez menos hacia el futuro,
    # evitando que el pronostico se dispare en horizontes largos.
    pron = []
    damp = 0.0   # suma acumulada phi + phi^2 + ... + phi^i
    for i in range(1, h + 1):
        damp += phi ** i
        idx = (n - 1 + i) % periodo
        valor = nivel + damp * tendencia + estacional[idx]
        pron.append(max(0.0, valor))   # la demanda no puede ser negativa
    return pron


# ===============================================================
# REGLA DE REPOSICION (decision de negocio)
#   punto_reorden = demanda esperada en el lead time + stock de seguridad
#   Si el stock actual cae por debajo -> hay que reponer.
# ===============================================================
def punto_de_reorden(pron_demanda, stock_actual, lead_time=7, stock_seguridad=0):
    demanda_lead = sum(pron_demanda[:lead_time])
    punto = demanda_lead + stock_seguridad
    reponer = stock_actual < punto
    # cantidad sugerida: lo que falta para cubrir el lead time + seguridad
    cantidad = max(0, round(punto - stock_actual))
    return {
        "demanda_esperada_lead": round(demanda_lead, 1),
        "punto_reorden": round(punto, 1),
        "stock_actual": stock_actual,
        "reponer": reponer,
        "cantidad_sugerida": cantidad,
    }


# ===============================================================
# MODELO AUTO-AJUSTADO: Holt-Winters que busca sus mejores parametros
#   Prueba varias combinaciones de alpha/beta/gamma, elige la que
#   menos error comete en un tramo de validacion interno, y con esa
#   pronostica. Sigue siendo python puro -> va al Code node de n8n.
# ===============================================================
def _mae(real, pron):
    return sum(abs(r - p) for r, p in zip(real, pron)) / len(real)

def holt_winters_auto(historial, h=7, periodo=7, val=28):
    """
    Holt-Winters que busca sus mejores parametros (alpha/beta/gamma):
      1. Separa un tramo de validacion interno (ultimos `val` dias).
      2. Prueba combinaciones y se queda con la de menor error.
      3. Reentrena con TODA la historia usando esos parametros y pronostica.
    Devuelve: (pronostico, "holt_winters")
    """
    y = list(historial)
    if len(y) < 2 * periodo + val:
        return holt_winters(y, h=h, periodo=periodo), "holt_winters"

    tr, va = y[:-val], y[-val:]

    alphas = [0.2, 0.4, 0.6]
    betas  = [0.01, 0.05, 0.1]
    gammas = [0.2, 0.4, 0.6]
    mejor = (1e18, 0.4, 0.05, 0.3)   # (error, alpha, beta, gamma)
    for a in alphas:
        for b in betas:
            for g in gammas:
                err = _mae(va, holt_winters(tr, h=val, periodo=periodo,
                                            alpha=a, beta=b, gamma=g))
                if err < mejor[0]:
                    mejor = (err, a, b, g)

    _, a, b, g = mejor
    return holt_winters(y, h=h, periodo=periodo, alpha=a, beta=b, gamma=g), "holt_winters"


# Prueba rapida si se ejecuta directo
if __name__ == "__main__":
    serie = [10, 12, 9, 11, 30, 40, 8] * 10  # 10 semanas con patron
    print("media_movil   :", [round(x, 1) for x in media_movil(serie)])
    print("naive_estac.  :", [round(x, 1) for x in naive_estacional(serie)])
    print("holt_winters  :", [round(x, 1) for x in holt_winters(serie)])
    pron, metodo = holt_winters_auto(serie)
    print("holt_winters_auto:", [round(x, 1) for x in pron], "| metodo:", metodo)
    print("reorden       :", punto_de_reorden(pron, stock_actual=50))
