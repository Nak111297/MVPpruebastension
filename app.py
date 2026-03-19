import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stress Testing — G&T Continental",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paleta ────────────────────────────────────────────────────────────────────
AZUL    = "#1B3A6B"
AZUL2   = "#2E5FAC"
NARANJA = "#E8871A"
VERDE   = "#27AE60"
ROJO    = "#C0392B"
AMARILLO = "#F39C12"

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1B3A6B; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stRadio label { color: white !important; }
[data-testid="stSidebar"] .stSlider label { color: white !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #AACBF0 !important; }
.kpi-box { background: white; border-radius: 8px; padding: 16px 20px;
           border-top: 4px solid #2E5FAC; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.kpi-title { font-size: 11px; color: #888; text-transform: uppercase;
             font-weight: bold; margin-bottom: 4px; }
.kpi-value { font-size: 28px; font-weight: bold; margin: 0; }
.kpi-sub { font-size: 11px; color: #666; margin-top: 2px; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Datos de arquetipos ───────────────────────────────────────────────────────
ARQUETIPOS = {
    "conservador_mayor":  {"nombre": "Conservador +55", "poblacion": 8000,  "sensibilidad_rumor": 0.85, "umbral_panico": 0.30, "canal": "agencia",   "monto": 45000, "latencia": 0},
    "empresario_credito": {"nombre": "Empresario",      "poblacion": 1500,  "sensibilidad_rumor": 0.35, "umbral_panico": 0.60, "canal": "ejecutivo", "monto": 200000,"latencia": 0},
    "millennial_digital": {"nombre": "Millennial",      "poblacion": 12000, "sensibilidad_rumor": 0.65, "umbral_panico": 0.20, "canal": "app",       "monto": 15000, "latencia": 0},
    "cliente_rural":      {"nombre": "Rural",           "poblacion": 6000,  "sensibilidad_rumor": 0.40, "umbral_panico": 0.70, "canal": "agencia",   "monto": 7500,  "latencia": 2},
    "empleado_agencia":   {"nombre": "Empleado",        "poblacion": 450,   "sensibilidad_rumor": 0.25, "umbral_panico": 0.80, "canal": "interno",   "monto": 0,     "latencia": 0},
}

SEGMENTOS_CREDITO = {
    "consumo_asalariado": {"nombre": "Consumo Asalariado", "cartera": 180e6,  "pd_base": 0.04, "s_des": 0.8, "s_inf": 0.3, "lgd": 0.65, "latencia": 2},
    "consumo_informal":   {"nombre": "Consumo Informal",   "cartera": 95e6,   "pd_base": 0.09, "s_des": 0.6, "s_inf": 0.8, "lgd": 0.70, "latencia": 1},
    "pyme":               {"nombre": "PYME",               "cartera": 420e6,  "pd_base": 0.06, "s_des": 0.5, "s_inf": 0.6, "lgd": 0.45, "latencia": 3},
    "hipotecario":        {"nombre": "Hipotecario",        "cartera": 890e6,  "pd_base": 0.02, "s_des": 0.4, "s_inf": 0.15,"lgd": 0.25, "latencia": 4},
    "empresarial":        {"nombre": "Empresarial",        "cartera": 1200e6, "pd_base": 0.03, "s_des": 0.35,"s_inf": 0.4, "lgd": 0.35, "latencia": 3},
}

COLORES_CRED = ["#2E5FAC","#C0392B","#E8871A","#27AE60","#8E44AD"]

SEGMENTOS_FX = {
    "deudor_usd_gtq":  {"nombre": "Deudor USD/GTQ",  "cartera": 380e6,  "umbral": 0.10, "sens": 0.90, "lgd": 0.55},
    "importador_pyme": {"nombre": "PYME Importadora", "cartera": 520e6,  "umbral": 0.08, "sens": 0.75, "lgd": 0.42},
    "exportador":      {"nombre": "Exportador",       "cartera": 280e6,  "umbral": 0.25, "sens": -0.30,"lgd": 0.30},
}

# ── Motores ───────────────────────────────────────────────────────────────────
def sim_liquidez(intensidad, hora_int=None):
    horas, acum, canales, intensidades, lcr_vals = [], [], [], [], []
    a = 0
    intens = intensidad
    acum_por_arq = {k: 0 for k in ARQUETIPOS}

    for h in range(1, 9):
        if hora_int and h == hora_int:
            intens = max(1.0, intens - 3.5)

        total = ag = ap = cl = 0
        for k, arq in ARQUETIPOS.items():
            if h <= arq["latencia"]:
                continue
            pob = arq["poblacion"]
            prob = (intens / 10) * arq["sensibilidad_rumor"]
            pct = acum_por_arq[k] / pob
            if pct > arq["umbral_panico"]:
                prob = min(0.92, prob * 1.5)
            n = int(pob * prob * 0.5)
            monto = n * arq["monto"]
            total += monto
            acum_por_arq[k] += n
            if arq["canal"] == "agencia": ag += n
            elif arq["canal"] == "app":   ap += n
            else:                          cl += n

        intens = min(10, intens + 0.55)
        a += total
        horas.append(h)
        acum.append(a / 1e6)
        canales.append({"agencia": ag, "app": ap, "call_center": cl})
        intensidades.append(round(intens, 1))
        lcr_vals.append(max(0.5, 1.45 - (a / 1e6 / 1500) * 0.8))

    return {"horas": horas, "acum": acum, "canales": canales, "intens": intensidades, "lcr": lcr_vals}


def sim_credito(dd, di, mes_int=None):
    meses = list(range(1, 13))
    pd_seg = {k: [] for k in SEGMENTOS_CREDITO}
    pe_acum = []
    a = 0
    for mes in meses:
        f = min(1.0, mes / 4)
        pe = 0
        for k, seg in SEGMENTOS_CREDITO.items():
            if mes < seg["latencia"]:
                pd = seg["pd_base"]
            else:
                pd = min(0.95, seg["pd_base"] + f * (dd * seg["s_des"] + di * seg["s_inf"]))
            if mes_int and mes >= mes_int:
                pd = max(seg["pd_base"], pd * 0.62)
            pd_seg[k].append(round(pd * 100, 2))
            pe += seg["cartera"] * pd * seg["lgd"]
        a += pe
        pe_acum.append(a / 1e6)
    return {"meses": meses, "pd": pd_seg, "pe": pe_acum}


def sim_fx(dep, velocidad, rumor, mes_int=None):
    meses = list(range(1, 13))
    dep_curva, retiros, perdidas = [], [], []
    ar = ap = 0
    for mes in meses:
        d = dep * min(1.0, mes / 3) if velocidad == "Shock" else dep * (mes / 12)
        if mes_int and mes >= mes_int:
            d *= 0.55
        dep_curva.append(round(d * 100, 1))

        prob_r = 0.25 if (rumor and mes <= 2) else 0
        if d > 0.05:
            prob_r = min(0.75, prob_r + (d - 0.05) * 3.25)
        ar += 1_200e6 * prob_r
        retiros.append(ar / 1e6)

        pe = 0
        for seg in SEGMENTOS_FX.values():
            if d > seg["umbral"]:
                f = min(1.0, (d - seg["umbral"]) / seg["umbral"])
                pd_ad = max(0, abs(seg["sens"]) * f * 0.15 * (1 if seg["sens"] > 0 else -1))
                pe += seg["cartera"] * pd_ad * seg["lgd"]
        ap += pe
        perdidas.append(ap / 1e6)

    return {"meses": meses, "dep": dep_curva, "retiros": retiros, "perdidas": perdidas}


# ── Helper KPI ────────────────────────────────────────────────────────────────
def kpi(col, titulo, valor, sub, color=AZUL2):
    col.markdown(f"""
    <div class="kpi-box" style="border-top-color:{color}">
        <div class="kpi-title">{titulo}</div>
        <div class="kpi-value" style="color:{color}">{valor}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏦 G&T Continental")
    st.markdown("**Stress Testing**")
    st.markdown("Simulación de Comportamiento")
    st.markdown("---")
    modulo = st.radio("Módulo", ["💧 Liquidez", "📉 Crédito", "💱 Tipo de Cambio"])
    st.markdown("---")

    if "Liquidez" in modulo:
        st.markdown("### Parámetros")
        intensidad = st.slider("Intensidad del rumor", 1.0, 10.0, 4.0, 0.5,
                               help="1 = rumor controlado | 10 = pánico total")
        hora_int_raw = st.radio("Intervención oficial", ["Sin intervención", "Hora 2", "Hora 4", "Hora 6"])
        hora_int = {"Sin intervención": None, "Hora 2": 2, "Hora 4": 4, "Hora 6": 6}[hora_int_raw]

    elif "Crédito" in modulo:
        st.markdown("### Shock macroeconómico")
        dd = st.slider("Incremento desempleo (pp)", 0.0, 15.0, 5.0, 0.5)
        di = st.slider("Incremento inflación (pp)", 0.0, 20.0, 6.0, 0.5)
        mes_int_raw = st.radio("Refinanciamiento masivo", ["Sin medidas", "Mes 3", "Mes 6"])
        mes_int = {"Sin medidas": None, "Mes 3": 3, "Mes 6": 6}[mes_int_raw]

    else:
        st.markdown("### Shock cambiario")
        dep_pct = st.slider("Depreciación total (%)", 2, 30, 10, 1)
        velocidad = st.radio("Velocidad", ["Gradual", "Shock"])
        rumor = st.toggle("Rumor de control de cambios", value=False)
        mes_int_fx_raw = st.radio("Intervención Banguat", ["Sin intervención", "Mes 2", "Mes 4"])
        mes_int_fx = {"Sin intervención": None, "Mes 2": 2, "Mes 4": 4}[mes_int_fx_raw]

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px; color:#AACBF0;'>
    ● Motor LLM local (Ollama)<br>
    Sin datos fuera del banco<br><br>
    <em>CONFIDENCIAL — USO INTERNO</em><br>
    VP de Riesgos
    </div>""", unsafe_allow_html=True)


# ── Contenido principal ───────────────────────────────────────────────────────
if "Liquidez" in modulo:
    st.title("💧 Liquidez — Corrida de Depósitos")
    st.caption("Simulación de comportamiento diferenciado por segmento ante rumor bancario")

    d = sim_liquidez(intensidad, hora_int)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Retiros acumulados", f"Q{d['acum'][-1]:.0f}M", "en 8 horas", ROJO)
    kpi(c2, "LCR mínimo proyectado", f"{min(d['lcr']):.2f}", f"Límite regulatorio: 1.0", ROJO if min(d['lcr']) < 1.0 else AMARILLO if min(d['lcr']) < 1.2 else VERDE)
    kpi(c3, "Intensidad pico rumor", f"{max(d['intens']):.1f}/10", "escala 0–10", NARANJA)
    kpi(c4, "Intervención", hora_int_raw, "comunicado oficial", AZUL2)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=d["horas"], y=d["acum"], name="Retiros acum. (QM)",
                                 fill="tozeroy", fillcolor="rgba(192,57,43,0.1)",
                                 line=dict(color=ROJO, width=3), mode="lines+markers"), secondary_y=False)
        fig.add_trace(go.Scatter(x=d["horas"], y=d["lcr"], name="LCR",
                                 line=dict(color=AZUL2, width=2, dash="dot"), mode="lines+markers"), secondary_y=True)
        fig.add_hline(y=1.0, line_dash="dash", line_color=ROJO, line_width=1,
                      annotation_text="LCR mínimo (1.0)", secondary_y=True)
        if hora_int:
            fig.add_vline(x=hora_int, line_dash="dash", line_color=VERDE, line_width=2,
                          annotation_text="⚡ Intervención")
        fig.update_layout(title="Retiros acumulados y LCR proyectado", height=350,
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", y=-0.2), margin=dict(t=40, b=60))
        fig.update_yaxes(title_text="Q millones", secondary_y=False)
        fig.update_yaxes(title_text="LCR", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        for canal, color, label in [("agencia", ROJO, "Agencias"), ("app", AZUL2, "App/Digital"), ("call_center", NARANJA, "Call Center")]:
            fig2.add_trace(go.Scatter(
                x=d["horas"], y=[c[canal] for c in d["canales"]],
                name=label, stackgroup="uno", fill="tonexty",
                line=dict(color=color), mode="lines",
            ))
        fig2.update_layout(title="Presión por canal operativo", height=350,
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=-0.2), margin=dict(t=40, b=60))
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ver detalle por arquetipo"):
        st.markdown("""
        | Arquetipo | Sensibilidad rumor | Canal preferido | Umbral pánico |
        |---|---|---|---|
        | Depositante conservador +55 | 85% | Agencia física | 30% del grupo |
        | Empresario con crédito activo | 35% | Ejecutivo de cuenta | 60% del grupo |
        | Millennial digital | 65% | App / Transferencia | 20% del grupo |
        | Cliente rural | 40% | Agencia física | 70% del grupo |
        | Empleado de agencia | 25% | Comunicación interna | 80% del grupo |
        """)

elif "Crédito" in modulo:
    st.title("📉 Deterioro de Portafolio de Crédito")
    st.caption("Impacto de shock macroeconómico sobre PD y pérdida esperada por segmento")

    d = sim_credito(dd / 100, di / 100, mes_int)

    pe_final = d["pe"][-1]
    cartera_total = sum(s["cartera"] for s in SEGMENTOS_CREDITO.values()) / 1e6
    ratio_mora = pe_final / cartera_total * 100
    pd_max_seg = max(SEGMENTOS_CREDITO, key=lambda k: max(d["pd"][k]))
    pd_max_val = max(d["pd"][pd_max_seg])

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Pérdida esperada acumulada", f"Q{pe_final:.0f}M", "mes 12", ROJO)
    kpi(c2, "Ratio de mora estimado", f"{ratio_mora:.1f}%", "sobre cartera total", NARANJA)
    kpi(c3, "PD máxima alcanzada", f"{pd_max_val:.1f}%", SEGMENTOS_CREDITO[pd_max_seg]["nombre"], AMARILLO)
    kpi(c4, "Medida de contención", mes_int_raw, "refinanciamiento masivo", AZUL2)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        for (k, seg), color in zip(SEGMENTOS_CREDITO.items(), COLORES_CRED):
            fig.add_trace(go.Scatter(x=d["meses"], y=d["pd"][k], name=seg["nombre"],
                                     line=dict(color=color, width=2), mode="lines+markers",
                                     marker=dict(size=5)))
        if mes_int:
            fig.add_vline(x=mes_int, line_dash="dash", line_color=VERDE,
                          annotation_text="⚡ Refinanciamiento")
        fig.update_layout(title="Probabilidad de Default por segmento (%)", height=350,
                          plot_bgcolor="white", paper_bgcolor="white",
                          legend=dict(orientation="h", y=-0.28, font=dict(size=10)),
                          margin=dict(t=40, b=80), xaxis_title="Mes")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=d["meses"], y=d["pe"],
                                  fill="tozeroy", fillcolor="rgba(192,57,43,0.1)",
                                  line=dict(color=ROJO, width=3), name="Pérdida esperada acum. (QM)"))
        if mes_int:
            fig2.add_vline(x=mes_int, line_dash="dash", line_color=VERDE,
                           annotation_text="⚡ Refinanciamiento")
        fig2.update_layout(title="Pérdida esperada acumulada (Q millones)", height=350,
                           plot_bgcolor="white", paper_bgcolor="white",
                           margin=dict(t=40, b=40), xaxis_title="Mes")
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ver parámetros por segmento"):
        st.markdown("""
        | Segmento | Cartera (QM) | PD base | Sensib. desempleo | Sensib. inflación | LGD |
        |---|---|---|---|---|---|
        | Consumo asalariado | Q180M | 4% | Alta | Moderada | 65% |
        | Consumo informal | Q95M | 9% | Moderada | Alta | 70% |
        | PYME | Q420M | 6% | Moderada | Moderada | 45% |
        | Hipotecario | Q890M | 2% | Moderada | Baja | 25% |
        | Empresarial | Q1,200M | 3% | Baja | Moderada | 35% |
        """)

else:
    st.title("💱 Shock de Tipo de Cambio")
    st.caption("Impacto de depreciación del quetzal sobre deudores en USD y depósitos dolarizados")

    d = sim_fx(dep_pct / 100, velocidad, rumor, mes_int_fx)

    dep_max = max(d["dep"])
    retiros_final = d["retiros"][-1]
    perdida_final = d["perdidas"][-1]

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Depreciación pico", f"{dep_max:.1f}%", "quetzal vs dólar", NARANJA)
    kpi(c2, "Retiros depósitos USD", f"${retiros_final:.0f}M", "acumulados mes 12", ROJO)
    kpi(c3, "Pérdida crédito FX", f"Q{perdida_final:.0f}M", "acumulada mes 12", AMARILLO)
    kpi(c4, "Intervención Banguat", mes_int_fx_raw, "contención cambiaria", AZUL2)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["meses"], y=d["dep"],
                                 fill="tozeroy", fillcolor="rgba(232,135,26,0.12)",
                                 line=dict(color=NARANJA, width=3), name="Depreciación (%)"))
        fig.add_hline(y=8, line_dash="dot", line_color=AMARILLO, annotation_text="Umbral deudores USD (8%)")
        fig.add_hline(y=5, line_dash="dot", line_color=ROJO,    annotation_text="Umbral depósitos USD (5%)")
        if mes_int_fx:
            fig.add_vline(x=mes_int_fx, line_dash="dash", line_color=VERDE,
                          annotation_text="⚡ Banguat")
        fig.update_layout(title="Curva de depreciación del quetzal (%)", height=350,
                          plot_bgcolor="white", paper_bgcolor="white",
                          margin=dict(t=40, b=40), xaxis_title="Mes",
                          yaxis=dict(ticksuffix="%"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=d["meses"], y=d["retiros"], name="Retiros depósitos USD (MM)",
                                  fill="tozeroy", fillcolor="rgba(192,57,43,0.1)",
                                  line=dict(color=ROJO, width=2)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=d["meses"], y=d["perdidas"], name="Pérdida crédito FX (QM)",
                                  line=dict(color=NARANJA, width=2, dash="dot")), secondary_y=True)
        if mes_int_fx:
            fig2.add_vline(x=mes_int_fx, line_dash="dash", line_color=VERDE)
        fig2.update_layout(title="Impacto acumulado: retiros y deterioro crediticio", height=350,
                           plot_bgcolor="white", paper_bgcolor="white",
                           legend=dict(orientation="h", y=-0.2), margin=dict(t=40, b=60))
        fig2.update_yaxes(title_text="USD millones", secondary_y=False)
        fig2.update_yaxes(title_text="Q millones", secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ver segmentos FX"):
        st.markdown("""
        | Segmento | Cartera | Umbral crítico | Sensibilidad FX | LGD |
        |---|---|---|---|---|
        | Deudor USD con ingresos GTQ | $380M | 10% depreciación | Alta | 55% |
        | PYME importadora | $520M | 8% depreciación | Alta | 42% |
        | Exportador (deuda GTQ) | Q280M | 25% depreciación | Negativa (se beneficia) | 30% |
        """)
