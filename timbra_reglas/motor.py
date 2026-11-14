#!/usr/bin/env python3
"""Motor de la base de reglas fiscales de Timbra (v0.4.1).

Uso (también: timbra-reglas <comando> o python -m timbra_reglas <comando>):
  python motor.py probar                                  corre los casos de reglas.yaml
  python motor.py valor UMA_MENSUAL 2026-03-15            valor + estado (vigente / arrastrado / por_confirmar / sin firma)
  python motor.py impacto IVA_TASA_GENERAL                qué parámetros y reglas dependen de él
  python motor.py vigencias 2027-01-01                    qué vence, qué se arrastra y qué revisar
  python motor.py simular IVA_TASA_GENERAL=10 2027-01-01  "¿y si el IVA baja a 10%?"
  python motor.py exportar 2026-01 2026-12                JSON mes por mes con valor, fuente, firma y estado

Requisito: PyYAML. Todo importe y tasa es Decimal; nunca float.
"""
import ast
import json
import os
import sys
import datetime as dt
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path

import yaml

AQUI = Path(__file__).parent


def dir_base() -> Path:
    """Carpeta con parametros.yaml y reglas.yaml: TIMBRA_REGLAS_BASE, junto al motor (paquete plano de un
    release), ./base (instalado con pip) o ../base (repo clonado)."""
    env = os.environ.get("TIMBRA_REGLAS_BASE")
    candidatas = ([Path(env)] if env else []) + [AQUI, AQUI / "base", AQUI.parent / "base"]
    for c in candidatas:
        if (c / "parametros.yaml").is_file() and (c / "reglas.yaml").is_file():
            return c
    raise FileNotFoundError("No encontré parametros.yaml y reglas.yaml: " + ", ".join(str(c) for c in candidatas))
VERSION_MOTOR = "0.5.0"

# Estados de un tramo. Los NO_APLICABLES nunca se usan salvo en simulación.
ESTADOS_APLICABLES = {"vigente", "por_confirmar"}
ESTADOS_NO_APLICABLES = {"propuesta", "aprobado_congreso_pendiente_dof"}
ESTADOS_VALIDOS = ESTADOS_APLICABLES | ESTADOS_NO_APLICABLES


class SinValor(Exception):
    """No hay valor vigente (o solo hay propuesta) para esa fecha: la app debe AVISAR, no inventar."""


def red(x, n=2):
    return x.quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)


class Base:
    def __init__(self, propuestas=False, simular=None, base_dir=None):
        base = Path(base_dir) if base_dir else dir_base()
        self.p = yaml.safe_load((base / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
        self.r = yaml.safe_load((base / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
        self.propuestas = propuestas
        self.simular = {k: D(v) for k, v in (simular or {}).items()}
        self.validar()

    # ---------- integridad (esto debe correr en CI antes de desplegar) ----------
    def validar(self):
        e = []
        for pid, p in self.p.items():
            if "formula" in p:
                e += [f"{pid}: la fórmula usa {d}, que no existe" for d in self.dependencias(pid) if d not in self.p]
                continue
            vals = p.get("valores", [])
            e += [f"{pid} {v.get('desde')}: valor sin fuente" for v in vals if not v.get("fuente")]
            e += [f"{pid} {v.get('desde')}: estado desconocido '{v.get('estado')}'" for v in vals
                  if v.get("estado", "vigente") not in ESTADOS_VALIDOS]
            reales = sorted([v for v in vals if v.get("estado", "vigente") in ESTADOS_APLICABLES], key=lambda v: v["desde"])
            for a, b in zip(reales, reales[1:]):
                if a.get("hasta") is None or a["hasta"] >= b["desde"]:
                    e.append(f"{pid}: vigencias encimadas {a['desde']} / {b['desde']}")
                elif (dt.date.fromisoformat(b["desde"]) - dt.date.fromisoformat(a["hasta"])).days != 1:
                    e.append(f"{pid}: hueco entre {a['hasta']} y {b['desde']}")
            if p.get("tipo") in ("tabla", "tabla_por_mes") and p.get("columnas", [None, None])[:2] == ["limite_inferior", "limite_superior"]:
                for v in vals:
                    grupos = v["valor"].items() if p["tipo"] == "tabla_por_mes" else [("", v["valor"])]
                    for g, filas in grupos:
                        for f1, f2 in zip(filas, filas[1:]):
                            if D(f1[1]) + D("0.01") != D(f2[0]):
                                e.append(f"{pid} {v['desde']} {g}: renglones no contiguos {f1[1]} → {f2[0]}")
        ids = [r["id"] for r in self.r]
        e += [f"regla {i} repetida" for i in sorted({i for i in ids if ids.count(i) > 1})]
        for r in self.r:
            e += [f"{r['id']}: usa {pid}, que no existe" for pid in r.get("parametros", []) if pid not in self.p]
            if r.get("casos") and r.get("calculadora") not in CALC:
                e.append(f"{r['id']}: calculadora '{r.get('calculadora')}' no existe")
        if e:
            raise ValueError("Base inconsistente:\n  " + "\n  ".join(e))

    # ---------- resolución por fecha ----------
    def tramo(self, pid, fecha):
        ok = [v for v in self.p[pid].get("valores", [])
              if v["desde"] <= fecha and (v.get("hasta") is None or fecha <= v["hasta"])
              and (v.get("estado", "vigente") in ESTADOS_APLICABLES or self.propuestas)]
        if not ok:
            pend = [v for v in self.p[pid].get("valores", []) if v.get("estado") in ESTADOS_NO_APLICABLES
                    and v["desde"] <= fecha and (v.get("hasta") is None or fecha <= v["hasta"])]
            extra = f" (hay {pend[-1]['estado']}: {pend[-1]['valor']}; no se aplica sin DOF)" if pend else ""
            raise SinValor(f"{pid}: no hay valor vigente al {fecha}{extra}")
        return max(ok, key=lambda v: v["desde"])

    def detalle(self, pid, fecha):
        """Valor + todo lo que la pantalla necesita para decir si es firme o estimación."""
        p = self.p[pid]
        if pid in self.simular:
            return {"valor": self.simular[pid], "estado": "simulado", "fuente": "simulación", "validado": False}
        if "formula" in p:
            deps = {d: self.detalle(d, fecha) for d in self.dependencias(pid)}
            valor = red(self._eval(ast.parse(p["formula"], mode="eval").body, fecha), p.get("decimales", 2))
            estados = {x["estado"] for x in deps.values()}
            estado = next((s for s in ("simulado", "propuesta", "arrastrado", "por_confirmar") if s in estados), "vigente")
            return {"valor": valor, "estado": estado, "fuente": p.get("fuente"),
                    "validado": all(x["validado"] for x in deps.values()), "formula": p["formula"]}
        t = self.tramo(pid, fecha)
        v = t["valor"]
        conv = lambda fila: [None if c is None else (D(str(c)) if str(c).replace(".", "").isdigit() else c) for c in fila]
        if p["tipo"] == "tabla":
            v = [conv(fila) for fila in v]
        elif p["tipo"] == "tabla_por_mes":
            v = {str(k): [conv(fila) for fila in filas] for k, filas in v.items()}
        elif p["tipo"] not in ("texto", "lista", "tabla_por_mes"):
            v = D(str(v))
        estado = t.get("estado", "vigente")
        if estado in ESTADOS_APLICABLES and t.get("confirmado_hasta") and fecha > t["confirmado_hasta"]:
            estado = "arrastrado"
        firma = p.get("firma") or {}
        pend = [x for x in p.get("valores", []) if x.get("estado") in ESTADOS_NO_APLICABLES
                and x["desde"] <= fecha and (x.get("hasta") is None or fecha <= x["hasta"])]
        out = {"valor": v, "estado": estado, "fuente": t["fuente"], "validado": bool(firma.get("validado")),
               "desde": t["desde"], "hasta": t.get("hasta"), "confirmado_hasta": t.get("confirmado_hasta")}
        if pend and not self.propuestas:
            out["reforma_pendiente"] = {"valor": str(pend[-1]["valor"]), "estado": pend[-1]["estado"], "fuente": pend[-1]["fuente"]}
        return out

    def valor(self, pid, fecha):
        return self.detalle(pid, fecha)["valor"]

    def _eval(self, n, fecha):
        if isinstance(n, ast.BinOp):
            a, b = self._eval(n.left, fecha), self._eval(n.right, fecha)
            ops = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b, ast.Div: lambda: a / b}
            if type(n.op) in ops:
                return ops[type(n.op)]()
        if isinstance(n, ast.Constant):
            return D(str(n.value))
        if isinstance(n, ast.Name):
            return self.valor(n.id, fecha)
        raise ValueError(f"Fórmula no permitida: {ast.dump(n)}")

    # ---------- conexiones ----------
    def dependencias(self, pid):
        f = self.p[pid].get("formula")
        return {n.id for n in ast.walk(ast.parse(f, mode="eval")) if isinstance(n, ast.Name)} if f else set()

    def impacto(self, pid):
        afectados, cola = set(), [pid]
        while cola:
            x = cola.pop()
            for otro in self.p:
                if x in self.dependencias(otro) and otro not in afectados:
                    afectados.add(otro)
                    cola.append(otro)
        todos = afectados | {pid}
        reglas = [f"{r['id']} {r['nombre']}" for r in self.r if todos & set(r.get("parametros", []))]
        return sorted(afectados), reglas


# ---------- calculadoras (una por regla con número) ----------
def isr_tarifa(base, tabla):
    for li, _ls, cuota, pct in reversed(tabla):
        if base >= li:
            return red(cuota + (base - li) * pct / 100)
    return D("0.00")


def calc_isr_art96_mensual(b, f, base):
    return isr_tarifa(D(base), b.valor("ISR_TARIFA_MENSUAL", f))


def tabla_106(b, f, meses):
    """Art. 106 con las tablas OFICIALES del Anexo 8: enero = mensual, feb-nov = acumulada, diciembre = anual."""
    m = int(meses)
    if m == 1:
        return b.valor("ISR_TARIFA_MENSUAL", f)
    if m == 12:
        return b.valor("ISR_TARIFA_ANUAL", f)
    return b.valor("ISR_TARIFA_ACUMULADA_106", f)[f"{m:02d}"]


def calc_isr_art96_acumulada(b, f, base, meses):
    return isr_tarifa(D(base), tabla_106(b, f, meses))


def calc_tarifa_periodica_es_diaria_por_dias(b, f, tabla, dias):
    """Así arma el SAT las tarifas de 7, 10 y 15 días: límites y cuotas = tarifa diaria × días.
    Por eso sus cuotas NO encadenan al centavo; la prueba correcta es esta, no el encadenamiento."""
    diaria, otra = b.valor("ISR_TARIFA_DIARIA", f), b.valor(tabla, f)
    n = D(dias)
    for (li, ls, c, p), (li2, ls2, c2, p2) in zip(diaria, otra):
        if (ls is None) != (ls2 is None) or (ls is not None and red(ls * n) != ls2) or red(c * n) != c2 or p != p2:
            return f"difiere en el renglón que inicia en {li2}"
    return "ok"


def calc_resico_pf_mensual(b, f, ingreso):
    ingreso = D(ingreso)
    for hasta, tasa in b.valor("RESICO_PF_TABLA", f):
        if ingreso <= hasta:
            return red(ingreso * tasa / 100)
    raise SinValor("Ingreso del mes rebasa la tabla de RESICO PF")


def calc_parametro(b, f, id):
    return b.valor(id, f)


def calc_tipo_cambio_dof_anterior(b, f, fix):
    """CFF 20: el tipo de cambio publicado en el DOF el día anterior a la operación. El DOF publica el FIX determinado el día hábil
    bancario previo, así que es el SEGUNDO FIX determinado antes de la fecha (entre `fix`: fecha_de_determinación -> valor).
    Sin dos FIX previos no hay valor: avisa, no inventa. Equivale a la serie Banxico SF60653 (evidencia: fuentes/evidencia/tc_cff20)."""
    previos = sorted(str(d) for d in fix if str(d) < f)
    if len(previos) < 2:
        raise SinValor(f"hacen falta dos FIX determinados antes de {f}")
    return D(str(fix[previos[-2]]))


def calc_estado_parametro(b, f, id):
    return b.detalle(id, f)["estado"]


def calc_retencion_iva(b, f, subtotal, parametro):
    return red(D(subtotal) * b.valor(parametro, f) / 100)


def calc_tope_deducciones_personales(b, f, ingreso_total):
    por_uma = red(b.valor("DED_PERS_VECES_UMA_ANUAL", f) * b.valor("UMA_ANUAL", f))
    por_pct = red(D(ingreso_total) * b.valor("DED_PERS_PCT_INGRESO", f) / 100)
    return min(por_uma, por_pct)


def calc_exento_veces_uma(b, f, parametro):
    return red(b.valor(parametro, f) * b.valor("UMA_DIARIA", f))


def calc_iva_mes(b, f, trasladado, retenido_a_mi, acreditable, saldo_favor_anterior, saldo_en_devolucion="0.00"):
    """LIVA arts. 5-D y 6: el saldo a favor se aplica en meses siguientes hasta agotarlo (no muere en diciembre).
    Lo que se pidió en devolución ya no se acredita: se resta del saldo disponible."""
    neto = D(trasladado) - D(retenido_a_mi) - D(acreditable)
    saldo = D(saldo_favor_anterior) - D(saldo_en_devolucion)
    if saldo < 0:
        raise ValueError("Se pidió en devolución más de lo que había a favor")
    if neto <= 0:
        return {"a_pagar": "0.00", "saldo_favor_remanente": str(red(saldo)), "saldo_favor_del_mes": str(red(-neto))}
    aplicado = min(neto, saldo)
    return {"a_pagar": str(red(neto - aplicado)), "saldo_favor_remanente": str(red(saldo - aplicado)),
            "saldo_favor_del_mes": "0.00"}


def calc_dias_extra_sexto_digito(b, f, rfc):
    """Decreto DOF 26-dic-2013 art. 5.1: se cuentan solo los dígitos del RFC; el sexto es el último de la fecha."""
    digitos = [c for c in rfc[:10] if c.isdigit()]
    if len(digitos) < 6:
        raise ValueError("RFC sin seis dígitos de fecha")
    tabla = {str(d): n for d, n in b.valor("DIAS_EXTRA_SEXTO_DIGITO", f)}
    return D(tabla[digitos[5]])


def calc_proporcion_iva(b, f, gravadas_16, gravadas_0, exentas, no_objeto, iva_indistinto):
    """LIVA art. 5 fr. V incisos c) y d): (16% + 0%) / (16% + 0% + exentas + no objeto computables), sin lo del art. 5-C."""
    num = D(gravadas_16) + D(gravadas_0)
    den = num + D(exentas) + D(no_objeto)
    if den == 0:
        raise ValueError("Sin actividades en el periodo")
    return red(D(iva_indistinto) * num / den)


def calc_iva_acreditable_destino(b, f, iva_gravadas="0", iva_exentas="0", iva_indistinto="0", iva_inversion_indistinta="0",
                                gravadas_16="0", gravadas_0="0", exentas="0", no_objeto="0"):
    """LIVA 5 fr. V: por destino del gasto. a) sólo gravadas (16 % o 0 %): 100 %; b) sólo exentas o no objeto (4-A): 0 %;
    c) indistinto: proporción del mes (gravadas 16 % + 0 %) / (todas, con las del 4-A); d-3) inversiones indistintas: misma
    proporción del mes (el ajuste del art. 5-A va aparte). Lo del art. 5-C no entra en los valores."""
    num = D(gravadas_16) + D(gravadas_0)
    den = num + D(exentas) + D(no_objeto)
    mixto = D(iva_indistinto) + D(iva_inversion_indistinta)
    if den == 0 and mixto != 0:
        raise SinValor("Hay IVA de uso indistinto pero no hay actos en el mes para calcular la proporción (LIVA 5 fr. V c)")
    prop = num / den if den else D(0)
    acred_mixto = red(mixto * prop)
    total = red(D(iva_gravadas)) + acred_mixto
    no_acred = red(D(iva_exentas)) + (red(mixto) - acred_mixto)
    return {"proporcion": str(red(prop, 4)), "acreditable_gravadas": str(red(D(iva_gravadas))),
            "acreditable_indistinto": str(acred_mixto), "acreditable": str(total), "no_acreditable": str(no_acred)}


def calc_actualizacion(b, f, monto, inpc_reciente, inpc_antiguo):
    """CFF 17-A: factor = INPC del mes anterior al más reciente / INPC del mes anterior al más antiguo; si < 1, es 1."""
    dec = int(b.valor("ACTUALIZACION_FACTOR_DECIMALES", f))
    factor = red(max(D(inpc_reciente) / D(inpc_antiguo), D(1)), dec)
    return {"factor": str(factor), "actualizacion": str(red(D(monto) * factor - D(monto)))}


def _mas_meses(fecha, n):
    y, m = fecha.year + (fecha.month - 1 + n) // 12, (fecha.month - 1 + n) % 12 + 1
    ultimo = (dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)).day
    return dt.date(y, m, min(fecha.day, ultimo))


def calc_recargos(b, f, monto_actualizado, vencimiento, pago):
    """CFF 21: por cada mes o fracción desde el vencimiento, con la tasa de mora vigente en cada mes."""
    v, p = dt.date.fromisoformat(vencimiento), dt.date.fromisoformat(pago)
    if p <= v:
        return {"meses": "0", "tasa_total": "0.00", "recargos": "0.00"}
    meses = (p.year - v.year) * 12 + p.month - v.month + (1 if p.day > v.day else 0)
    tasa = sum(b.valor("RECARGOS_MORA_MENSUAL", (_mas_meses(v, i) + dt.timedelta(days=1)).isoformat()) for i in range(meses))
    return {"meses": str(meses), "tasa_total": str(tasa), "recargos": str(red(D(monto_actualizado) * tasa / 100))}


def calc_ajuste_pesos(b, f, monto):
    """CFF 20: en el pago, de 1 a 50 centavos baja al peso; de 51 a 99 sube."""
    m = D(monto)
    entero, cent = divmod(m, 1)
    return str(entero + (1 if cent > D("0.50") else 0))


def calc_diot_renglon(b, f, **campos):
    """Arma un renglón de la DIOT con el orden oficial; regresa cuántos campos tiene (deben ser 54)."""
    layout = b.valor("DIOT_LAYOUT_2025", f)
    extra = set(campos) - set(layout)
    if extra:
        raise ValueError(f"Campos que no existen en el layout: {extra}")
    renglon = "|".join(str(campos.get(c, "")) for c in layout)
    return str(len(renglon.split("|")))


def tarifa_raw(base, tabla):
    for li, _ls, cuota, pct in reversed(tabla):
        if base >= li:
            return cuota + (base - li) * pct / 100
    return D(0)


def calc_isr_tarifa(b, f, tabla, base):
    """Cualquier tarifa del art. 96/152 por ID: ISR_TARIFA_MENSUAL, _QUINCENAL, _SEMANAL, _DECENAL, _DIARIA, _ANUAL."""
    return red(tarifa_raw(D(base), b.valor(tabla, f)))


def calc_isr_periodo_con_subsidio(b, f, tabla, base, dias):
    """Retención del periodo menos subsidio prorrateado (mensual / 30.4 × días) si el ingreso mensualizado no pasa el límite."""
    isr = red(tarifa_raw(D(base), b.valor(tabla, f)))
    mensualizado = D(base) / D(dias) * D("30.4")
    sub = D("0.00")
    if mensualizado <= b.valor("SUBSIDIO_EMPLEO_LIMITE_INGRESO", f):
        sub = red(b.valor("SUBSIDIO_EMPLEO_MENSUAL", f) / D("30.4") * D(dias))
    return {"isr": str(isr), "subsidio": str(sub), "retencion": str(max(isr - sub, D("0.00")))}


def calc_aguinaldo_monto(b, f, sd, ingreso, fin, dias_aguinaldo=None):
    """LFT 87: proporcional por días naturales desde max(ingreso, 1-ene), contando el día de ingreso."""
    fin_d = dt.date.fromisoformat(fin)
    ini = max(dt.date.fromisoformat(ingreso), dt.date(fin_d.year, 1, 1))
    dias_anio = 366 if (fin_d.year % 4 == 0 and (fin_d.year % 100 != 0 or fin_d.year % 400 == 0)) else 365
    dias_lab = (fin_d - ini).days + 1
    dag = D(dias_aguinaldo) if dias_aguinaldo is not None else b.valor("LFT_AGUINALDO_DIAS", f)
    return red(D(sd) * dag * D(dias_lab) / D(dias_anio)) if dias_lab < dias_anio else red(D(sd) * dag)


def calc_isr_aguinaldo(b, f, sd, aguinaldo):
    """LISR 93-XIV y 96; RLISR 174 (optativo). Sin redondeo intermedio; round2 al final."""
    ag = D(aguinaldo)
    exento = min(ag, b.valor("EXENTO_AGUINALDO_IMPORTE", f))
    grav = ag - exento
    tabla = b.valor("ISR_TARIFA_MENSUAL", f)
    sm = D(sd) * D("30.4")
    if grav == 0:
        return {"exento": str(red(exento)), "gravado": "0.00", "isr_174": "0.00", "isr_ordinario": "0.00"}
    ordinario = red(tarifa_raw(sm + grav, tabla) - tarifa_raw(sm, tabla))
    prop = grav / D(365) * D("30.4")
    tasa = (tarifa_raw(sm + prop, tabla) - tarifa_raw(sm, tabla)) / prop
    return {"exento": str(red(exento)), "gravado": str(red(grav)), "isr_174": str(red(grav * tasa)),
            "isr_ordinario": str(ordinario)}


def calc_isr_606(b, f, ingresos, predial="0.00", ciega=True, retencion_pm="0.00", trimestral=False):
    ing = D(ingresos)
    ded = red(ing * b.valor("ARREND_DEDUCCION_CIEGA_PCT", f) / 100) + D(predial) if ciega else D(predial)
    tabla = b.valor("ISR_TARIFA_TRIMESTRAL_ARRENDAMIENTO" if trimestral else "ISR_TARIFA_MENSUAL", f)
    isr = red(tarifa_raw(max(D(0), ing - ded), tabla))
    return str(max(D("0.00"), isr - D(retencion_pm)))


def calc_resico_pm_provisional(b, f, cobrado, pagado, ptu="0", perdidas="0", pagos_previos="0", retenciones="0"):
    base = max(D(0), D(cobrado) - D(pagado) - D(ptu) - D(perdidas))
    return str(max(D("0.00"), red(base * b.valor("ISR_PM_TASA", f) / 100) - D(pagos_previos) - D(retenciones)))


def calc_pm_coeficiente_provisional(b, f, cu, ingresos, mes, ptu="0", perdidas="0", pagos_previos="0", retenciones="0"):
    """LISR 14: UF = CU × ingresos − PTU/8 × (mes − 4) desde mayo − pérdidas."""
    m = int(mes)
    ptu_mes = red(D(ptu) / 8 * (m - 4)) if m >= 5 else D(0)
    uf = red(D(cu) * D(ingresos)) - ptu_mes - D(perdidas)
    isr = red(max(D(0), uf) * b.valor("ISR_PM_TASA", f) / 100)
    return str(max(D("0.00"), isr - D(pagos_previos) - D(retenciones)))


# Regímenes a los que el estímulo de ISR de frontera NO aplica: RESICO PF (LISR 113-I tercer párrafo; RMF 11.9.23).
FRONTERA_ISR_EXCLUIDOS = {"626_pf": "RESICO de personas físicas: LISR 113-I, tercer párrafo, y RMF 2026 regla 11.9.23"}


def calc_estimulo_frontera_isr(b, f, isr, proporcion_region, regimen=None):
    if regimen in FRONTERA_ISR_EXCLUIDOS:
        return "0.00"
    prop = D(proporcion_region)
    if prop * 100 < b.valor("FRONTERA_ISR_PROPORCION_MIN", f):
        return "0.00"
    return str(red(D(isr) * prop / b.valor("FRONTERA_ISR_DIVISOR", f)))


def calc_iva_frontera(b, f, base, region="norte"):
    """IVA de una operación en la región fronteriza: 8 % mientras el decreto esté vigente (al 31-dic-2026);
    sin decreto vigente, la tasa general con aviso. El régimen no cambia la tasa (RESICO PF sí puede aplicar el de IVA)."""
    pid = {"norte": "IVA_TASA_FRONTERA_NORTE", "sur": "IVA_TASA_FRONTERA_SUR"}[region]
    try:
        tasa, aviso = b.valor(pid, f), ""
    except SinValor:
        tasa = b.valor("IVA_TASA_GENERAL", f)
        aviso = f"Sin decreto de frontera {region} vigente a {f}: se cobra la tasa general. Revisar prórroga en el DOF."
    return {"tasa": str(tasa), "iva": str(red(D(base) * tasa / 100)), "aviso": aviso}


def calc_tope_donativos(b, f, base_anio_anterior):
    return str(red(D(base_anio_anterior) * b.valor("DONATIVOS_DEDUCIBLE_PCT", f) / 100))


def calc_retencion_plataforma(b, f, actividad, base, iva):
    tasas = {a: t for a, t in b.valor("PLATAFORMAS_ISR_TABLA", f)}
    pct_iva = D(100) if actividad == "sin_rfc" else b.valor("PLATAFORMAS_IVA_RET_PCT", f)
    return {"isr": str(red(D(base) * tasas[actividad] / 100)), "iva": str(red(D(iva) * pct_iva / 100))}


def _tasa_titulo_ii(b, f, tipo_bien):
    """Porciento máximo del título II: art. 34 (por bien), 35 (maquinaria por actividad) o 33 (diferidos)."""
    for pid in ("DEPRECIACION_TASAS_ART34", "DEPRECIACION_TASAS_ART35", "DEPRECIACION_TASAS_ART33"):
        tasas = {t: x for t, x in b.valor(pid, f)}
        if tipo_bien in tasas:
            return D(tasas[tipo_bien]), "LISR " + pid[-2:]
    raise SinValor(f"No hay porciento máximo para «{tipo_bien}» en los arts. 33, 34 ni 35")


def _tope_moi(b, f, tipo_bien, moi, avion_sin_concesion=False):
    """LISR 36: autos 175,000; eléctricos o híbridos eléctricos 250,000; aviones sin concesión 8,600,000."""
    if tipo_bien == "automoviles":
        return min(moi, b.valor("AUTO_TOPE_DEDUCCION", f))
    if tipo_bien == "automoviles_electricos_hibridos":
        return min(moi, b.valor("AUTO_TOPE_DEDUCCION_ELECTRICO", f))
    if tipo_bien == "aviones" and str(avion_sin_concesion).lower() in ("true", "si", "sí", "1"):
        return min(moi, b.valor("AVION_TOPE_DEDUCCION", f))
    return moi


def calc_depreciacion(b, f, moi, tipo_bien, meses, factor="1", avion_sin_concesion=False):
    tasa, _art = _tasa_titulo_ii(b, f, tipo_bien)
    moi = _tope_moi(b, f, tipo_bien, D(moi), avion_sin_concesion)
    return str(red(moi * tasa / 100 * D(meses) / 12 * max(D(factor), D(1))))


def calc_tasa_depreciacion(b, f, tipo_bien):
    """Porciento máximo y artículo del título II para una clave de bien, actividad o concepto."""
    tasa, art = _tasa_titulo_ii(b, f, tipo_bien)
    return {"tasa": str(tasa), "articulo": art}


# Claves del art. 209 que en el título II se llaman distinto. Las demás se llaman igual.
_RESICO_PM_A_TITULO_II = {"dados_troqueles_moldes_herramienta": "moldes_troqueles"}


def calc_inversion_resico_pm(b, f, monto, tipo_bien, inicio_uso, terreno="0", inversiones_ejercicio=None, mes=12):
    """LISR 209 (porcientos), 31 (meses completos de uso), 32 (el terreno no se demerita), 36 (tope de autos).
    Deducción acumulada del ejercicio de `f` hasta el mes `mes` (12 = anual; 1..11 = pago provisional, art. 211)."""
    moi = D(monto) - D(terreno)
    if moi <= 0:
        raise SinValor("Sin monto deducible: el terreno no se deduce como inversión (LISR 32), sólo la construcción")
    if D(inversiones_ejercicio if inversiones_ejercicio is not None else monto) > b.valor("RESICO_PM_INVERSIONES_TOPE", f):
        tasa, art = _tasa_titulo_ii(b, f, _RESICO_PM_A_TITULO_II.get(tipo_bien, tipo_bien))
        articulo = f"{art} (inversiones del ejercicio arriba del tope del art. 209)"
    else:
        # el art. 209 B-VI no separa autos eléctricos: van al 25 % de automóviles, con su tope del art. 36
        clave = "automoviles" if tipo_bien == "automoviles_electricos_hibridos" else tipo_bien
        tasas = {t: x for t, x in b.valor("RESICO_PM_INVERSIONES", f)}
        if clave not in tasas:
            raise SinValor(f"El art. 209 no trae porciento para «{tipo_bien}»")
        tasa, articulo = D(tasas[clave]), "LISR 209"
    moi = _tope_moi(b, f, tipo_bien, moi)
    anio, m, d = (int(x) for x in str(inicio_uso).split("-"))
    corte = f if isinstance(f, dt.date) else dt.date.fromisoformat(str(f))
    if anio > corte.year:
        raise SinValor("El bien empieza a usarse después del ejercicio: todavía no se deduce")
    primer_mes = 1 if anio < corte.year else (m if d == 1 else m + 1)  # mes completo de uso (art. 31)
    meses = max(0, int(mes) - primer_mes + 1)
    return {"articulo": articulo, "tasa": str(tasa), "monto_original": str(red(moi)), "meses": str(meses),
            "deduccion": str(red(moi * tasa / 100 * meses / 12))}


def _vacaciones(b, f, anio):
    for hasta, dias in b.valor("LFT_VACACIONES_TABLA", f):
        if D(anio) <= hasta:
            return dias
    return b.valor("LFT_VACACIONES_TABLA", f)[-1][1]


def calc_vacaciones_dias(b, f, anio_servicio):
    return str(_vacaciones(b, f, anio_servicio))


def calc_sbc(b, f, sd, anio_servicio, variables_diarias="0"):
    """LSS 27: SD × factor (4 decimales) + variables; tope 25 UMA."""
    vac = _vacaciones(b, f, anio_servicio)
    factor = red(1 + (b.valor("LFT_AGUINALDO_DIAS", f) + vac * b.valor("LFT_PRIMA_VACACIONAL_PCT", f) / 100) / 365, 4)
    return str(min(red(D(sd) * factor) + D(variables_diarias), b.valor("SBC_TOPE_IMPORTE", f)))


def _ceav_tasa(b, f, sbc):
    uma, sm = b.valor("UMA_DIARIA", f), b.valor("SM_GENERAL_DIARIO", f)
    veces = red(sbc / uma, 2)
    for hasta, tasa in b.valor("IMSS_CEAV_PATRON_TABLA", f):
        if hasta == "SM":
            if sbc <= sm:
                return tasa
            continue
        if hasta is None or veces <= hasta:
            return tasa


def calc_imss_cuotas(b, f, sbc, dias, prima_rt):
    """Cuotas del periodo; cada ramo se redondea por separado. Retiro, CEAV e Infonavit son bimestrales: aquí por días."""
    v = lambda k: b.valor(k, f)
    s = min(D(sbc), v("SBC_TOPE_IMPORTE"))
    d = D(dias)
    uma = v("UMA_DIARIA")
    exc = max(D(0), s - v("IMSS_EYM_EXCEDENTE_UMA") * uma) * d
    base = s * d
    pat = {
        "cuota_fija": red(uma * d * v("IMSS_EYM_CUOTA_FIJA_PATRON") / 100),
        "excedente": red(exc * v("IMSS_EYM_EXCEDENTE_PATRON") / 100),
        "prest_dinero": red(base * v("IMSS_PD_PATRON") / 100),
        "gmp": red(base * v("IMSS_GMP_PATRON") / 100),
        "invalidez_vida": red(base * v("IMSS_IV_PATRON") / 100),
        "guarderias": red(base * v("IMSS_GUARDERIAS_PATRON") / 100),
        "riesgo_trabajo": red(base * D(prima_rt) / 100),
        "retiro": red(base * v("IMSS_RETIRO_PATRON") / 100),
        "ceav": red(base * _ceav_tasa(b, f, s) / 100),
    }
    obr = {
        "excedente": red(exc * v("IMSS_EYM_EXCEDENTE_OBRERO") / 100),
        "prest_dinero": red(base * v("IMSS_PD_OBRERO") / 100),
        "gmp": red(base * v("IMSS_GMP_OBRERO") / 100),
        "invalidez_vida": red(base * v("IMSS_IV_OBRERO") / 100),
        "ceav": red(base * v("IMSS_CEAV_OBRERO") / 100),
    }
    return {"patron": str(sum(pat.values())), "obrero": str(sum(obr.values())),
            "infonavit": str(red(base * v("INFONAVIT_APORTACION_PATRON") / 100)), "ceav_patron": str(pat["ceav"])}


def calc_ptu_tope(b, f, salario_mensual, promedio_3_anios):
    return str(max(red(D(salario_mensual) * b.valor("PTU_TOPE_MESES_SALARIO", f)), red(D(promedio_3_anios))))


def calc_separacion_isr(b, f, sd, total, anios, meses_fraccion=0):
    """LISR 93-XIII y 96 último párrafo: gravado × (ISR del último sueldo mensual / ese sueldo)."""
    anios_ex = int(anios) + (1 if int(meses_fraccion) > 6 else 0)
    exento = min(D(total), b.valor("EXENTO_SEPARACION_IMPORTE_ANUAL", f) * anios_ex)
    grav = D(total) - exento
    sm = D(sd) * D("30.4")
    tasa = tarifa_raw(sm, b.valor("ISR_TARIFA_MENSUAL", f)) / sm
    return {"exento": str(red(exento)), "gravado": str(red(grav)), "isr": str(red(grav * tasa))}


def calc_isn(b, f, entidad, remuneraciones):
    tabla = {e: t for e, t, _c in b.valor("ISN_TASA_TABLA", f)}
    if entidad not in tabla:
        raise SinValor(f"ISN: entidad {entidad} sin tasa cargada")
    return str(red(D(remuneraciones) * tabla[entidad] / 100))


def calc_rep_fecha_limite(b, f, fecha_pago):
    p = dt.date.fromisoformat(fecha_pago)
    y, m = (p.year + 1, 1) if p.month == 12 else (p.year, p.month + 1)
    return dt.date(y, m, int(b.valor("REP_DIA_LIMITE", f))).isoformat()


def calc_reforma_pendiente(b, f, id):
    return b.detalle(id, f).get("reforma_pendiente", {}).get("valor", "ninguna")


def calc_isr_plataformas(b, f, contribuyente, actividad, ingresos, iva_trasladado="0", con_rfc="si",
                         opta_definitivo="no", ingresos_ejercicio_anterior="0"):
    """Retención de la plataforma digital (régimen 625). Personas físicas: LISR 113-A (tasa por actividad), 113-C fr. IV
    (20 % sin RFC) y LIVA 18-J fr. II a) (50 % del IVA; 100 % sin RFC). Personas morales: LIF 2026 art. 25 fr. VI (2.5 %,
    20 % sin RFC), sin retención de IVA. Es pago definitivo solo si la persona física optó (LISR 113-B) y sus ingresos del
    ejercicio anterior no pasaron del tope."""
    base, iva = D(ingresos), D(iva_trasladado)
    if contribuyente == "pf":
        tasas = {a: t for a, t in b.valor("PLATAFORMAS_ISR_PF_TABLA", f)}
        tasa = tasas["sin_rfc"] if con_rfc == "no" else tasas[actividad]
        pct_iva = D(100) if con_rfc == "no" else b.valor("PLATAFORMAS_IVA_RET_PCT", f)
        definitivo = opta_definitivo == "si" and D(ingresos_ejercicio_anterior) <= b.valor("PLATAFORMAS_PD_TOPE_ANUAL", f)
    elif contribuyente == "pm":
        if actividad != "enajenacion_servicios":
            raise ValueError("Para personas morales solo está cargada la enajenación de bienes y servicios (LIF 2026 art. 25 fr. VI)")
        tasas = {a: t for a, t in b.valor("PLATAFORMAS_ISR_PM_TABLA", f)}
        tasa = tasas["sin_rfc"] if con_rfc == "no" else tasas["enajenacion_servicios"]
        pct_iva, definitivo = D(0), False
    else:
        raise ValueError("contribuyente debe ser pf o pm")
    return {"tasa": str(tasa), "isr_retenido": str(red(base * tasa / 100)), "iva_retenido": str(red(iva * pct_iva / 100)),
            "pago_definitivo": "si" if definitivo else "no"}


# ---------- series de datos (INPC, tipo de cambio): se leen por fecha, igual que los parámetros ----------
def dir_series() -> Path:
    """Carpeta con las series (inpc.yaml...): TIMBRA_REGLAS_SERIES, junto al motor (paquete plano), ./series (instalado
    con pip) o ../series (repo clonado)."""
    env = os.environ.get("TIMBRA_REGLAS_SERIES")
    candidatas = ([Path(env)] if env else []) + [AQUI / "series", AQUI.parent / "series", AQUI]
    for c in candidatas:
        if (c / "inpc.yaml").is_file():
            return c
    raise SinValor("No encontré la carpeta de series (inpc.yaml): " + ", ".join(str(c) for c in candidatas))


def _carga_serie(sid, carpeta=None):
    p = Path(carpeta or dir_series()) / f"{sid.lower()}.yaml"
    if not p.is_file():
        raise SinValor(f"{sid}: no hay archivo de serie ({p.name})")
    return yaml.safe_load(p.read_text(encoding="utf-8"))["valores"]


def serie(sid, fecha, carpeta=None):
    """Valor de una serie en una fecha. La llave es el día (AAAA-MM-DD) o, si la serie es mensual, el mes (AAAA-MM).
    Si no hay dato, SinValor: la app avisa y no inventa."""
    v = _carga_serie(sid, carpeta)
    for llave in (fecha, fecha[:7]):
        if llave in v:
            return D(str(v[llave]["valor"]))
    raise SinValor(f"{sid}: no hay valor para {fecha}")


def _mes_anterior(fecha):
    y, m = int(fecha[:4]), int(fecha[5:7])
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def calc_actualizacion_inpc(b, f, monto, desde, hasta):
    """CFF 17-A con el INPC real de la serie: factor = INPC del mes anterior al más reciente del periodo (el del pago) entre
    el INPC del mes anterior al más antiguo (el del vencimiento); si es menor que 1, es 1. Si el índice del mes anterior al
    más reciente aún no se publica, se usa el último publicado."""
    v = _carga_serie("INPC")
    mes_antiguo, mes_reciente = _mes_anterior(desde), _mes_anterior(hasta)
    if mes_antiguo not in v:
        raise SinValor(f"INPC: no hay índice para {mes_antiguo}")
    if mes_reciente not in v:
        ultimo = max(v)
        if mes_reciente < ultimo:
            raise SinValor(f"INPC: no hay índice para {mes_reciente}")
        mes_reciente = ultimo
    antiguo, reciente = D(str(v[mes_antiguo]["valor"])), D(str(v[mes_reciente]["valor"]))
    dec = int(b.valor("ACTUALIZACION_FACTOR_DECIMALES", f))
    factor = red(max(reciente / antiguo, D(1)), dec)
    actualizado = red(D(monto) * factor)
    return {"inpc_antiguo": f"{mes_antiguo} {antiguo}", "inpc_reciente": f"{mes_reciente} {reciente}", "factor": str(factor),
            "actualizacion": str(red(actualizado - D(monto))), "monto_actualizado": str(actualizado)}


def calc_actualizacion_y_recargos(b, f, monto, vencimiento, pago):
    """Pago tardío: actualización con INPC real (CFF 17-A) y recargos sobre el monto actualizado (CFF 21)."""
    act = calc_actualizacion_inpc(b, f, monto, vencimiento, pago)
    rec = calc_recargos(b, f, act["monto_actualizado"], vencimiento, pago)
    return {"factor": act["factor"], "monto_actualizado": act["monto_actualizado"], "meses": rec["meses"],
            "tasa_total": rec["tasa_total"], "recargos": rec["recargos"],
            "total": str(D(act["monto_actualizado"]) + D(rec["recargos"]))}


# ---------- anual de personas morales ----------
def calc_isr_anual_pm(b, f, ingresos_acumulables, deducciones_autorizadas, ptu_pagada="0", perdidas_anteriores="0",
                      pagos_provisionales="0", retenciones="0"):
    """LISR 9: utilidad fiscal = ingresos acumulables menos deducciones y PTU pagada; resultado fiscal = utilidad menos pérdidas
    de ejercicios anteriores (LISR 57); ISR = tasa de personas morales × resultado fiscal; se acreditan los pagos
    provisionales y las retenciones del ejercicio (LISR 14). `perdidas_anteriores` entra ya actualizada y vigente (10 ejercicios)."""
    utilidad = D(ingresos_acumulables) - D(deducciones_autorizadas) - D(ptu_pagada)
    perdidas = D(perdidas_anteriores)
    resultado = max(utilidad - perdidas, D(0))
    isr = red(resultado * b.valor("ISR_PM_TASA", f) / 100)
    acreditable = D(pagos_provisionales) + D(retenciones)
    por_amortizar = max(perdidas - max(utilidad, D(0)), D(0)) + max(-utilidad, D(0))
    return {"utilidad_fiscal": str(red(utilidad)), "resultado_fiscal": str(red(resultado)), "isr": str(isr),
            "a_cargo": str(red(max(isr - acreditable, D(0)))), "saldo_a_favor": str(red(max(acreditable - isr, D(0)))),
            "perdidas_por_amortizar": str(red(por_amortizar))}


def calc_codigo_agrupador(b, f, codigo):
    """Busca un código en el catálogo del código agrupador del SAT (Anexo 24). Si no existe, avisa."""
    cat = {c: (n, nv) for c, n, nv in b.valor("CONTA_CODIGO_AGRUPADOR", f)}
    if codigo not in cat:
        raise SinValor(f"CONTA_CODIGO_AGRUPADOR: el código {codigo} no está en el catálogo")
    return {"codigo": codigo, "nombre": cat[codigo][0], "nivel": cat[codigo][1]}


def calc_agrupador_de_concepto(b, f, concepto, contexto=""):
    """A qué código agrupador del SAT se apunta un concepto de las pólizas tipo (R-150 a R-157)."""
    filas = {(c, ctx): cod for c, ctx, cod, _ in b.valor("CONTA_CONCEPTO_AGRUPADOR", f)}
    cod = filas.get((concepto, contexto)) or filas.get((concepto, ""))
    if not cod:
        raise SinValor(f"CONTA_CONCEPTO_AGRUPADOR: no hay código agrupador para el concepto {concepto}")
    return {"concepto": concepto, **calc_codigo_agrupador(b, f, cod)}


# ---------- pólizas tipo: «evento → cargos y abonos por concepto» (criterio contable, no cifras de ley) ----------
# Los conceptos son nombres estables (clientes, iva_trasladado_no_cobrado...), no números de cuenta: cada app
# los apunta a su propio catálogo, idealmente al código agrupador del SAT. Toda póliza debe cuadrar.
def _poliza(lineas):
    lineas = [(t, c, D(m)) for t, c, m in lineas if D(m) != 0]
    debe = sum(m for t, _, m in lineas if t == "D")
    haber = sum(m for t, _, m in lineas if t == "H")
    if debe != haber:
        raise ValueError(f"La póliza no cuadra: debe {debe} y haber {haber}")
    orden = sorted(lineas, key=lambda x: (x[0] != "D", x[1]))
    return "; ".join(f"{t} {c} {red(m)}" for t, c, m in orden)


def _medio(medio):
    return {"banco": "bancos", "caja": "caja"}[medio]


def calc_poliza_emitido(b, f, gravado="0", tasa0="0", exento="0", iva="0", isr_retenido="0", iva_retenido="0"):
    """CFDI emitido vigente: cargo a clientes por lo que me van a pagar (total menos lo que me retienen), el IVA queda
    como trasladado no cobrado hasta el cobro (LIVA 1-B)."""
    total = D(gravado) + D(tasa0) + D(exento) + D(iva) - D(isr_retenido) - D(iva_retenido)
    return _poliza([("D", "clientes", total), ("D", "isr_retenido_por_clientes", isr_retenido),
                    ("D", "iva_retenido_por_clientes", iva_retenido), ("H", "ingreso_gravado", gravado),
                    ("H", "ingreso_tasa0", tasa0), ("H", "ingreso_exento", exento), ("H", "iva_trasladado_no_cobrado", iva)])


def calc_poliza_nota_credito_emitida(b, f, gravado="0", tasa0="0", exento="0", iva="0", isr_retenido="0", iva_retenido="0"):
    """Nota de crédito emitida: lo inverso del CFDI, con devoluciones y descuentos en lugar de ingreso."""
    total = D(gravado) + D(tasa0) + D(exento) + D(iva) - D(isr_retenido) - D(iva_retenido)
    return _poliza([("D", "devoluciones_y_descuentos", D(gravado) + D(tasa0) + D(exento)), ("D", "iva_trasladado_no_cobrado", iva),
                    ("H", "clientes", total), ("H", "isr_retenido_por_clientes", isr_retenido),
                    ("H", "iva_retenido_por_clientes", iva_retenido)])


def calc_poliza_cobro(b, f, cobrado, iva_trasladado="0", total_cfdi="0", cobrado_cfdi=None, medio="banco"):
    """Cobro: salda al cliente y el IVA pasa de no cobrado a cobrado en la proporción cobrada (LIVA 1-B).
    En divisa, `cobrado` son los pesos del banco y `cobrado_cfdi` los pesos al tipo de cambio del CFDI: la diferencia
    es utilidad o pérdida cambiaria."""
    al_cfdi = D(cobrado if cobrado_cfdi is None else cobrado_cfdi)
    dif = D(cobrado) - al_cfdi
    iva = red(D(iva_trasladado) * al_cfdi / D(total_cfdi)) if D(total_cfdi) else D(0)
    return _poliza([("D", _medio(medio), cobrado), ("D", "perdida_cambiaria", -dif if dif < 0 else 0),
                    ("D", "iva_trasladado_no_cobrado", iva), ("H", "clientes", al_cfdi),
                    ("H", "utilidad_cambiaria", dif if dif > 0 else 0), ("H", "iva_trasladado_cobrado", iva)])


def calc_poliza_recibido(b, f, base, iva="0", isr_retenido="0", iva_retenido="0", destino="gasto", deducible="si"):
    """CFDI recibido: gasto (o inventario), IVA acreditable pendiente de pago y proveedor por lo que realmente debo
    (total menos lo que yo retengo). Un gasto no deducible va completo, con su IVA (LIVA 5)."""
    total = D(base) + D(iva) - D(isr_retenido) - D(iva_retenido)
    if deducible == "no":
        cargos = [("D", "gasto_no_deducible", D(base) + D(iva))]
    else:
        cargos = [("D", {"gasto": "gasto", "inventario": "inventario"}[destino], base), ("D", "iva_acreditable_pendiente", iva)]
    return _poliza(cargos + [("H", "proveedores", total), ("H", "isr_retenido_por_pagar", isr_retenido),
                             ("H", "iva_retenido_por_pagar", iva_retenido)])


def calc_poliza_pago(b, f, pagado, iva="0", total_cfdi="0", medio="banco", iva_retenido="0"):
    """Pago a proveedor: salda la cuenta y el IVA pasa de pendiente a pagado en la proporción pagada (LIVA 5 fr. III)."""
    # el IVA que yo retuve no se acredita con el pago: se acredita en la declaración siguiente al entero (LIVA 5 fr. IV)
    iva_p = red((D(iva) - D(iva_retenido)) * D(pagado) / D(total_cfdi)) if D(total_cfdi) else D(0)
    return _poliza([("D", "proveedores", pagado), ("D", "iva_acreditable_pagado", iva_p), ("H", _medio(medio), pagado),
                    ("H", "iva_acreditable_pendiente", iva_p)])


def calc_poliza_entero_retenciones(b, f, isr_retenido="0", iva_retenido="0", medio="banco"):
    """Entero al SAT de lo que retuve (ISR e IVA): el pasivo se salda contra banco o caja."""
    return _poliza([("D", "isr_retenido_por_pagar", isr_retenido), ("D", "iva_retenido_por_pagar", iva_retenido),
                    ("H", _medio(medio), D(isr_retenido) + D(iva_retenido))])


def calc_poliza_acreditamiento_iva_retenido(b, f, iva_retenido, mes_entero, mes_acreditamiento):
    """LIVA 5 fr. IV: el IVA retenido y enterado se acredita en la declaración mensual SIGUIENTE a la del entero; antes
    de ese mes no se acredita y la calculadora avisa en lugar de calcular."""
    if mes_acreditamiento <= mes_entero:
        raise SinValor(f"El IVA retenido enterado en {mes_entero} se acredita en la declaración siguiente (LIVA 5 fr. IV), no en {mes_acreditamiento}")
    return _poliza([("D", "iva_acreditable_pagado", iva_retenido), ("H", "iva_acreditable_pendiente", iva_retenido)])


def calc_poliza_nomina(b, f, percepciones, isr_retenido="0", imss_obrero="0", imss_patron="0", infonavit_patron="0"):
    """Nómina pagada con provisión: sueldos y cuotas patronales al gasto; ISR retenido, IMSS e Infonavit quedan por pagar.
    `isr_retenido` es el ISR a retener ya neto del subsidio para el empleo."""
    neto = D(percepciones) - D(isr_retenido) - D(imss_obrero)
    return _poliza([("D", "sueldos_y_salarios", percepciones), ("D", "cuotas_patronales", imss_patron),
                    ("D", "aportaciones_infonavit", infonavit_patron), ("H", "bancos", neto),
                    ("H", "isr_retenido_por_pagar", isr_retenido), ("H", "imss_por_pagar", D(imss_obrero) + D(imss_patron)),
                    ("H", "infonavit_por_pagar", infonavit_patron)])


def calc_factura_global(b, f, regimen, periodicidad):
    """RMF 2.7.1.21: periodicidades de la factura global por régimen y cómo se detalla. El plazo de emisión es CFDI_GLOBAL_HORAS_MAX."""
    filas = b.valor("GLOBAL_PERIODICIDAD_POR_REGIMEN", f)
    propias = [x for x in filas if x[0] == regimen]
    validas = propias if any(x[3] == "si" for x in propias) else propias + [x for x in filas if x[0] == "*"]
    fila = next((x for x in validas if x[1] == periodicidad), None)
    return {"permitida": "si" if fila else "no", "detalle": fila[2] if fila else "", "plazo_horas": str(b.valor("CFDI_GLOBAL_HORAS_MAX", f))}


def calc_comprobante_publico_general(b, f, importe, solicita="no"):
    """RMF 2.7.1.21: sin obligación de expedir comprobante por operaciones con el público en general de importe inferior al mínimo, si no lo piden."""
    return "si" if solicita == "si" or D(importe) >= b.valor("GLOBAL_COMPROBANTE_MINIMO", f) else "no"


def calc_monto_en_global(b, f, acumulacion, total_operacion, recibido):
    """RMF 2.7.1.21, pagos parciales o diferidos: devengado = monto total en la global; flujo de efectivo = solo lo efectivamente recibido."""
    return str(red(D(total_operacion) if acumulacion == "devengado" else D(recibido)))


def calc_cancelacion_global_resico(b, f, emision, cancelacion):
    """RMF 3.13.29: RESICO PF puede cancelar su global a más tardar el último día del mes límite del ejercicio siguiente."""
    mes = int(b.valor("RESICO_GLOBAL_CANCELACION_MES", f))
    limite = dt.date(int(emision[:4]) + 1, mes + 1, 1) - dt.timedelta(days=1)
    return {"limite": limite.isoformat(), "resultado": "permitida" if dt.date.fromisoformat(cancelacion) <= limite else "fuera_de_plazo"}


def calc_iva_servicio_medico(b, f, profesion, prestador):
    """LIVA 15 fr. XIV y RLIVA 41: exento solo si es servicio profesional de medicina de un médico, médico veterinario o cirujano dentista
    prestado por persona física, sociedad civil o institución de asistencia privada. Todo lo demás causa IVA salvo otra exención."""
    exento = profesion in b.valor("IVA_EXENTO_PROFESIONES_MEDICAS", f) and prestador in b.valor("IVA_EXENTO_PRESTADORES_MEDICOS", f)
    return {"tratamiento": "exento" if exento else "gravado",
            "fundamento": "LIVA 15 fr. XIV; RLIVA 41" if exento else "fuera de LIVA 15 fr. XIV: causa IVA salvo que otra fracción lo exente"}


def calc_retencion_resico_pf(b, f, monto, receptor):
    """LISR 113-J: la persona moral que paga a un RESICO PF retiene el 1.25 % del pago sin IVA; a una persona física o al público en general no."""
    return str(red(D(monto) * b.valor("RESICO_PF_RETENCION_PM", f) / 100)) if receptor == "persona_moral" else "0.00"


def calc_poliza_cobro_terminal(b, f, bruto, comision, iva_comision="0", con_cfdi_banco="si", iva_trasladado="0", total_cfdi="0"):
    """Cobro con tarjeta: la terminal deposita neto. El ingreso va por el bruto; la comisión es gasto y su IVA es acreditable solo si el banco
    emite CFDI (LIVA 5 fr. II); sin CFDI el IVA de la comisión se queda en el gasto."""
    neto = D(bruto) - D(comision) - D(iva_comision)
    acred = D(iva_comision) if con_cfdi_banco == "si" else D(0)
    gasto = D(comision) + (D(iva_comision) if con_cfdi_banco != "si" else D(0))
    iva_cob = red(D(iva_trasladado) * D(bruto) / D(total_cfdi)) if D(total_cfdi) else D(0)
    return _poliza([("D", "bancos", neto), ("D", "comisiones_bancarias", gasto), ("D", "iva_acreditable_pagado", acred),
                    ("D", "iva_trasladado_no_cobrado", iva_cob), ("H", "clientes", bruto), ("H", "iva_trasladado_cobrado", iva_cob)])


CALC = {k[5:]: v for k, v in globals().items() if k.startswith("calc_")}


# ---------- comandos ----------
def probar(b):
    ok = falla = pendiente = 0
    for r in b.r:
        for c in r.get("casos", []):
            etiqueta = f"{r['id']} · {c['nombre']}"
            try:
                res = CALC[c.get("calculadora", r.get("calculadora"))](b, c["fecha"], **c.get("entradas", {}))
                res = {k: str(v) for k, v in res.items()} if isinstance(res, dict) else str(res)
                bien = "espera_error" not in c and res == c.get("esperado")
            except SinValor as e:
                res, bien = f"SinValor ({e})", c.get("espera_error") == "SinValor"
            if bien:
                ok += 1
                marca = "PASA*    " if c.get("confirmado") is False else "PASA     "
                print(f"  {marca}{etiqueta} → {res}")
            elif c.get("confirmado") is False:
                pendiente += 1
                print(f"  PENDIENTE {etiqueta} → {res} (esperado {c.get('esperado')})")
            else:
                falla += 1
                print(f"  FALLA    {etiqueta} → {res} (esperado {c.get('esperado', c.get('espera_error'))})")
    print(f"\n{ok} pasan · {falla} fallan · {pendiente} pendientes   (* = pasa contra un esperado aún no confirmado)")
    return falla == 0


def vigencias(b, fecha):
    hoy = dt.date.today().isoformat()
    sin, arr = [], []
    for pid, p in b.p.items():
        try:
            if b.detalle(pid, fecha)["estado"] == "arrastrado":
                arr.append(pid)
        except SinValor:
            prop = [v for v in p.get("valores", []) if v.get("estado") in ESTADOS_NO_APLICABLES]
            sin.append(f"{pid}: {p['nombre']}" + (f"  · reforma pendiente ({prop[0]['estado']}): {prop[0]['valor']}" if prop else ""))
    print(f"VENCEN al {fecha} (la app avisa y no calcula):\n  - " + "\n  - ".join(sin or ["nada"]))
    print(f"\nSe ARRASTRAN al {fecha} (se calcula como estimación hasta cargar el valor nuevo):\n  - " + "\n  - ".join(arr or ["nada"]))
    rev = [f"{pid} (desde {p['revisar_antes']})" for pid, p in b.p.items() if p.get("revisar_antes") and p["revisar_antes"] <= hoy]
    print(f"\nPOR REVISAR hoy ({hoy}):\n  - " + "\n  - ".join(rev or ["nada"]))


def a_json(x):
    if isinstance(x, D):
        return str(x)
    if isinstance(x, list):
        return [a_json(i) for i in x]
    if isinstance(x, dict):
        return {k: a_json(v) for k, v in x.items()}
    return x


def exportar(b, desde, hasta):
    """Un bloque por mes (fecha = último día del mes). Es lo que debe regresar GET /api/fiscal/parametros."""
    y, m = map(int, desde.split("-"))
    y2, m2 = map(int, hasta.split("-"))
    out = {"version_motor": VERSION_MOTOR, "meses": {}}
    while (y, m) <= (y2, m2):
        fin = (dt.date(y + m // 12, m % 12 + 1, 1) - dt.timedelta(days=1)).isoformat()
        mes = {}
        for pid in b.p:
            try:
                d = b.detalle(pid, fin)
                mes[pid] = {k: a_json(v) for k, v in d.items() if v is not None}
            except SinValor:
                mes[pid] = {"estado": "sin_valor"}
        out["meses"][f"{y:04d}-{m:02d}"] = mes
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main(args):
    for flujo in (sys.stdout, sys.stderr):  # la consola de Windows (cp1252) no imprime «→»
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    if not args or args[0] == "probar":
        sys.exit(0 if probar(Base()) else 1)
    cmd = args[0]
    if cmd == "valor":
        d = Base().detalle(args[1], args[2])
        print(json.dumps({k: a_json(v) for k, v in d.items()}, ensure_ascii=False, indent=1))
    elif cmd == "impacto":
        params, reglas = Base().impacto(args[1])
        print("Parámetros que cambian solos:", ", ".join(params) or "ninguno")
        print("Reglas a re-probar:\n  " + "\n  ".join(reglas))
    elif cmd == "vigencias":
        vigencias(Base(), args[1])
    elif cmd == "simular":
        cambios, fecha = dict(a.split("=") for a in args[1:-1]), args[-1]
        real, sim = Base(), Base(simular=cambios, propuestas=True)
        print(f"Simulación al {fecha} con {cambios}:")
        for pid in sorted({d for c in cambios for d in real.impacto(c)[0]} | set(cambios)):
            try:
                antes = real.valor(pid, fecha)
            except SinValor:
                antes = "sin valor"
            print(f"  {pid}: {antes} → {sim.valor(pid, fecha)}")
    elif cmd == "exportar":
        exportar(Base(), args[1], args[2] if len(args) > 2 else args[1])
    else:
        print(__doc__)


def cli():
    """Comando `timbra-reglas`: probar | valor | impacto | vigencias | simular | exportar."""
    main(sys.argv[1:])


if __name__ == "__main__":
    cli()
