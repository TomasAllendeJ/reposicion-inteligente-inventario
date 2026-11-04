# ================================================================
# NODO CODE (Python) - Procesa las ventas que llegan de Google Sheets
# Lee _items (filas: item_id, date, sales), arma el historial por SKU,
# pronostica la demanda y calcula la reposicion. Sin imports.
# ================================================================

def media_movil(hist, h, ventana=7):
    ult = hist[-ventana:]
    prom = sum(ult) / len(ult)
    return [max(0.0, prom) for _ in range(h)]

def naive_estacional(hist, h, periodo=7):
    out = []
    for i in range(h):
        out.append(max(0.0, hist[-periodo + (i % periodo)]))
    return out

def holt_winters(hist, h, periodo=7, alpha=0.4, beta=0.05, gamma=0.3, phi=0.95):
    y = list(hist); n = len(y)
    if n < 2 * periodo:
        return media_movil(y, h, min(periodo, n))
    nivel = sum(y[:periodo]) / periodo
    tend = (sum(y[periodo:2*periodo]) - sum(y[:periodo])) / (periodo * periodo)
    estac = [y[i] - nivel for i in range(periodo)]
    for t in range(n):
        val = y[t]; idx = t % periodo; nant = nivel
        nivel = alpha * (val - estac[idx]) + (1 - alpha) * (nivel + tend)
        tend = beta * (nivel - nant) + (1 - beta) * tend
        estac[idx] = gamma * (val - nivel) + (1 - gamma) * estac[idx]
    out = []; damp = 0.0
    for i in range(1, h + 1):
        damp += phi ** i; idx = (n - 1 + i) % periodo
        out.append(max(0.0, nivel + damp * tend + estac[idx]))
    return out

def _mae(real, pron):
    return sum(abs(a - b) for a, b in zip(real, pron)) / len(real)

def holt_winters_auto(hist, h, periodo=7, val=28):
    y = list(hist)
    if len(y) < 2 * periodo + val:
        return holt_winters(y, h, periodo), "holt_winters"
    tr = y[:-val]; va = y[-val:]
    mejor = (1e18, 0.4, 0.05, 0.3)
    for a in [0.2, 0.4, 0.6]:
        for b in [0.01, 0.05, 0.1]:
            for g in [0.2, 0.4, 0.6]:
                e = _mae(va, holt_winters(tr, val, periodo, a, b, g))
                if e < mejor[0]:
                    mejor = (e, a, b, g)
    _, a, b, g = mejor
    return holt_winters(y, h, periodo, a, b, g), "holt_winters"

def wmape(real, pron):
    denom = 0.0; err = 0.0
    for a, p in zip(real, pron):
        denom += a; err += abs(a - p)
    if denom == 0:
        return None
    return err / denom * 100.0

def punto_de_reorden(pron, stock, lead_time=7, seguridad=0):
    demanda_lead = sum(pron[:lead_time])
    punto = demanda_lead + seguridad
    return {
        "punto_reorden": round(punto, 1),
        "reponer": stock < punto,
        "cantidad_sugerida": max(0, int(round(punto - stock))),
    }

# ---------------- 1) Leer las filas que llegan de Google Sheets ----------------
filas = []
for it in _items:
    try:
        j = it["json"]
    except (TypeError, KeyError):
        j = it
    filas.append(j)

# Agrupar por producto, ordenado por fecha
por_sku = {}
fecha_max = ""
for r in filas:
    sku = str(r["item_id"])
    try:
        s = float(r["sales"])
    except (TypeError, ValueError):
        s = 0.0
    d = str(r["date"])
    por_sku.setdefault(sku, []).append((d, s))
    if d > fecha_max:
        fecha_max = d

HIST = {}
for sku in por_sku:
    pares = sorted(por_sku[sku])
    HIST[sku] = [v for _, v in pares]

# ---------------- 2) Stock actual (en produccion vendria de otra fuente) --------
STOCK = {"FOODS_2_019": 41, "FOODS_2_197": 107, "FOODS_3_064": 213, "FOODS_3_080": 225,
         "FOODS_3_090": 159, "FOODS_3_099": 83, "FOODS_3_120": 378, "FOODS_3_252": 465,
         "FOODS_3_282": 56, "FOODS_3_295": 132, "FOODS_3_499": 95, "FOODS_3_501": 283,
         "FOODS_3_511": 74, "FOODS_3_555": 109, "FOODS_3_586": 291, "FOODS_3_587": 420,
         "FOODS_3_681": 66, "FOODS_3_714": 94, "FOODS_3_739": 80, "FOODS_3_741": 183}

# ---------------- 3) Pronostico + reposicion por SKU ----------------
LEAD_TIME = 7
PERIODO = 7
items_out = []
for sku in sorted(HIST.keys()):
    serie = HIST[sku]
    pron, metodo = holt_winters_auto(serie, LEAD_TIME, PERIODO)
    demanda_lead = sum(pron)
    demanda_prom = demanda_lead / LEAD_TIME
    if len(serie) > LEAD_TIME + 2 * PERIODO:
        pron_bt, _ = holt_winters_auto(serie[:-LEAD_TIME], LEAD_TIME, PERIODO)
        wm = wmape(serie[-LEAD_TIME:], pron_bt)
    else:
        wm = None
    if wm is None:
        conf = "media"
    elif wm <= 30:
        conf = "alta"
    elif wm <= 50:
        conf = "media"
    else:
        conf = "baja"
    # stock: del diccionario, o un estimado si no esta
    if sku in STOCK:
        stock = STOCK[sku]
    else:
        stock = int(round(demanda_prom * 5))
    ro = punto_de_reorden(pron, stock, LEAD_TIME)
    items_out.append({
        "item_id": sku,
        "demanda_prom_dia": round(demanda_prom, 1),
        "demanda_7d": round(demanda_lead, 1),
        "stock_actual": stock,
        "punto_reorden": ro["punto_reorden"],
        "reponer": ro["reponer"],
        "cantidad_sugerida": ro["cantidad_sugerida"],
        "wmape": (round(wm, 1) if wm is not None else None),
        "confianza": conf,
        "metodo": metodo,
    })

salida = {"tienda": "CA_1", "fecha": fecha_max, "lead_time_dias": LEAD_TIME, "items": items_out}
return [{"json": salida}]
