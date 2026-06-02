# ChargeGrid Intelligence - Dashboard de Monitoramento
# Grupo 05 - Turma 1CCPY - FIAP - EV Challenge 2026 - GoodWe

# Jair Fereira Dos Santos Neto RM 569682
# Matheus da Costa Goncalves RM 570756
# Yan Luiz Neves Lemos RM 571717
# Arthur dos Santos Bezerra RM 569721
# Carlos Henrique Fratezi RM 571792

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from simulator import (
    simular_dia,
    calcular_kpis,
    LIMITE_DEMANDA_KW,
    CAPACIDADE_BATERIA,
    NUM_CARREGADORES,
)

st.set_page_config(
    page_title="ChargeGrid Intelligence",
    page_icon="⚡",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    [data-testid="stMetricLabel"] { color: #8b949e !important; }
    [data-testid="stMetricValue"] { color: #58a6ff !important; }
    h1, h2, h3 { color: #e6edf3 !important; }
    .stButton>button {
        background: #238636 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

if "df" not in st.session_state:
    df, carregadores = simular_dia()
    st.session_state.df           = df
    st.session_state.carregadores = carregadores

df           = st.session_state.df
carregadores = st.session_state.carregadores

col_titulo, col_status = st.columns([3, 1])

with col_titulo:
    st.markdown("# ⚡ ChargeGrid Intelligence")
    st.markdown("**Gestão Energética para Eletropostos** · EV Challenge 2026 · FIAP + GoodWe · Turma 1CCPY")

with col_status:
    idx = st.slider("Horário", 0, len(df) - 1, len(df) - 1, label_visibility="collapsed")
    linha_atual = df.iloc[idx]

    if linha_atual["peak_shaving"]:
        st.markdown(
            f"<div style='background:#1c1a16;border:1px solid #d97706;border-radius:8px;"
            f"padding:8px 14px;color:#fbbf24;font-weight:600;font-size:13px;margin-top:8px'>"
            f"⚠️ PEAK SHAVING ATIVO — {linha_atual['horario']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='background:#0d1f0d;border:1px solid #238636;border-radius:8px;"
            f"padding:8px 14px;color:#3fb950;font-weight:600;font-size:13px;margin-top:8px'>"
            f"✅ SISTEMA NORMAL — {linha_atual['horario']}</div>",
            unsafe_allow_html=True,
        )

st.divider()

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Nova Simulação"):
        df, carregadores = simular_dia(seed=np.random.randint(0, 99999))
        st.session_state.df           = df
        st.session_state.carregadores = carregadores
        st.rerun()
with col_info:
    st.caption(f"📍 Simulando: **{linha_atual['horario']}** — arraste o slider acima pra mudar o horário")

st.subheader("📊 Dados em Tempo Real")

m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.metric("☀️ Solar Gerado",  f"{linha_atual['solar_kw']:.0f} kW")
with m2:
    st.metric("🔋 Bateria",       f"{linha_atual['bateria_pct']:.0f}%",
              delta=f"{linha_atual['bateria_kwh']:.1f} kWh")
with m3:
    rotulo_rede = "Horário Pico 🔴" if linha_atual["horario_pico"] else "Fora de Pico 🟢"
    st.metric("🔌 Consumo Rede",  f"{linha_atual['rede_kw']:.0f} kW", delta=rotulo_rede)
with m4:
    st.metric("🚗 Carregadores",  f"{linha_atual['ev_kw']:.0f} kW",
              delta=f"Demanda: {linha_atual['demanda_kw']:.0f}/{LIMITE_DEMANDA_KW:.0f} kW")
with m5:
    st.metric("♻️ Autoconsumo",   f"{linha_atual['autoconsumo_pct']:.0f}%")
with m6:
    co2_acumulado = float(df.iloc[: idx + 1]["co2_evitado_kg"].sum())
    st.metric("🌱 CO₂ Evitado",   f"{co2_acumulado:.2f} kg")

st.divider()

col_graficos, col_lateral = st.columns([3, 1])

with col_graficos:

    st.subheader("⚡ Fluxo de Energia ao Longo do Dia")

    dados_ate_agora = df.iloc[: idx + 1]

    fig1 = go.Figure()

    fig1.add_hline(
        y=LIMITE_DEMANDA_KW,
        line_dash="dash", line_color="#ef4444",
        annotation_text="Limite contratado (80 kW)",
        annotation_position="top right",
        annotation_font_color="#ef4444",
    )
    fig1.add_hline(
        y=LIMITE_DEMANDA_KW * 0.90,
        line_dash="dot", line_color="#f97316",
        annotation_text="Gatilho peak shaving (72 kW)",
        annotation_position="bottom right",
        annotation_font_color="#f97316",
    )

    fig1.add_trace(go.Scatter(
        x=dados_ate_agora["horario"], y=dados_ate_agora["solar_usado_kw"],
        name="☀️ Solar", mode="lines", fill="tozeroy",
        line=dict(color="#fbbf24", width=1.5),
        fillcolor="rgba(251,191,36,0.25)",
    ))
    fig1.add_trace(go.Scatter(
        x=dados_ate_agora["horario"], y=dados_ate_agora["bateria_contrib"],
        name="🔋 Bateria", mode="lines", fill="tozeroy",
        line=dict(color="#818cf8", width=1.5),
        fillcolor="rgba(129,140,248,0.25)",
    ))
    fig1.add_trace(go.Scatter(
        x=dados_ate_agora["horario"], y=dados_ate_agora["rede_kw"],
        name="🔌 Rede", mode="lines", fill="tozeroy",
        line=dict(color="#60a5fa", width=1.5),
        fillcolor="rgba(96,165,250,0.15)",
    ))
    fig1.add_trace(go.Scatter(
        x=dados_ate_agora["horario"], y=dados_ate_agora["demanda_kw"],
        name="📊 Demanda Total", mode="lines",
        line=dict(color="#e5e7eb", width=2, dash="dot"),
    ))

    momentos_ps = dados_ate_agora[dados_ate_agora["peak_shaving"]]
    if not momentos_ps.empty:
        fig1.add_trace(go.Scatter(
            x=momentos_ps["horario"], y=momentos_ps["demanda_kw"],
            name="⚠️ Peak Shaving", mode="markers",
            marker=dict(color="#f97316", size=8, symbol="triangle-up"),
        ))

    fig1.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=True, gridcolor="#21262d", title="Horário"),
        yaxis=dict(showgrid=True, gridcolor="#21262d", title="Potência (kW)", range=[0, 135]),
        margin=dict(l=55, r=20, t=50, b=45),
        height=350,
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🔋 Estado de Carga da Bateria")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=dados_ate_agora["horario"], y=dados_ate_agora["bateria_pct"],
        name="Carga (%)", mode="lines", fill="tozeroy",
        line=dict(color="#818cf8", width=2),
        fillcolor="rgba(129,140,248,0.20)",
    ))
    fig2.add_hline(y=10, line_dash="dash", line_color="#ef4444",
                   annotation_text="Mínimo 10%", annotation_font_color="#ef4444")
    fig2.add_hline(y=90, line_dash="dash", line_color="#22c55e",
                   annotation_text="Máximo 90%", annotation_font_color="#22c55e")

    todos_horarios = list(df["horario"])
    inicio_pico = next((h for h in todos_horarios if h >= "17:00"), None)
    fim_pico    = next((h for h in reversed(todos_horarios) if h < "21:00"), None)
    if inicio_pico and fim_pico:
        fig2.add_vrect(
            x0=inicio_pico, x1=fim_pico,
            fillcolor="rgba(249,115,22,0.07)", line_width=0,
            annotation_text="Horário de ponta (bateria descarrega aqui)",
            annotation_font_color="#f97316",
            annotation_position="top left",
        )

    fig2.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", size=12),
        xaxis=dict(showgrid=True, gridcolor="#21262d", title="Horário"),
        yaxis=dict(showgrid=True, gridcolor="#21262d", title="Carga (%)", range=[0, 110]),
        margin=dict(l=55, r=20, t=20, b=45),
        height=220,
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)


with col_lateral:

    st.subheader("🚗 Carregadores")

    for c in carregadores:
        potencia_atual  = linha_atual["ev_kw"] / NUM_CARREGADORES
        utilizacao_real = round(potencia_atual / 22.0 * 100)
        cor = "#22c55e" if utilizacao_real >= 90 else "#f97316" if utilizacao_real >= 60 else "#ef4444"

        st.markdown(f"""
        <div style='background:#161b22;border:1px solid #30363d;border-radius:8px;
                    padding:12px;margin-bottom:8px'>
            <div style='font-weight:600;color:#e6edf3'>{c['id']}</div>
            <div style='font-size:11px;color:#8b949e;margin-bottom:6px'>{c['veiculo']}</div>
            <div style='background:#21262d;border-radius:3px;height:6px'>
                <div style='background:{cor};width:{utilizacao_real}%;height:6px;border-radius:3px'></div>
            </div>
            <div style='display:flex;justify-content:space-between;font-size:11px;margin-top:5px'>
                <span style='color:{cor};font-weight:600'>{potencia_atual:.1f} kW</span>
                <span style='color:#8b949e'>{c['kwh_sessao']:.1f} kWh</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("⚡ Origem da Energia")

    valores = [
        max(0.0, float(linha_atual["solar_usado_kw"])),
        max(0.0, float(linha_atual["bateria_contrib"])),
        max(0.0, float(linha_atual["rede_kw"])),
    ]

    if sum(valores) > 0:
        fig3 = go.Figure(go.Pie(
            labels=["☀️ Solar", "🔋 Bateria", "🔌 Rede"],
            values=valores,
            marker=dict(colors=["#fbbf24", "#818cf8", "#60a5fa"]),
            hole=0.5,
            textinfo="percent",
            textfont=dict(size=11),
        ))
        fig3.update_layout(
            plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9", size=11),
            showlegend=True,
            legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
        )
        st.plotly_chart(fig3, use_container_width=True)


st.divider()
st.subheader("📈 Resultados Acumulados do Dia")

kpis = calcular_kpis(df)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric("⚡ EVs carregados",    f"{kpis['ev_kwh']:.1f} kWh")
    st.metric("☀️ Solar aproveitado", f"{kpis['solar_kwh']:.1f} kWh")
with k2:
    st.metric("🌱 CO₂ evitado",       f"{kpis['co2_kg']:.2f} kg")
    st.metric("♻️ Autoconsumo solar", f"{kpis['autoconsumo_pct']:.1f}%")
with k3:
    st.metric(
        "⚠️ Intervenções de peak shaving",
        str(kpis["interv_ps"]),
        delta=f"R$ {kpis['multa_evitada_r']:.0f} em multas evitadas"
              if kpis["interv_ps"] > 0 else "Nenhuma ultrapassagem",
    )
    st.metric("📊 Demanda máxima", f"{kpis['demanda_max_kw']:.1f} / {LIMITE_DEMANDA_KW:.0f} kW")
with k4:
    st.metric("💰 Receita de recarga", f"R$ {kpis['receita_r']:.2f}")
    st.metric("🔌 Consumo da rede",    f"{kpis['rede_kwh']:.1f} kWh")


st.divider()
st.subheader("🤖 Assistente ChargeGrid IA")
st.caption("Pergunte sobre o sistema em português — Pilar IV do ChargeGrid (IA simulada para PoC)")

pergunta = st.text_input(
    "Sua pergunta:",
    placeholder="Ex: Por que minha conta veio alta?   |   Qual o status dos carregadores?",
    label_visibility="collapsed",
)

respostas = {
    "conta": lambda k: (
        f"Analisando os dados de hoje: foram {k['interv_ps']} intervenção(ões) de peak shaving. "
        f"Consumo da rede: {k['rede_kwh']:.1f} kWh. Autoconsumo solar: {k['autoconsumo_pct']:.1f}%. "
        "Dica: programe recargas no período noturno para aproveitar a tarifa mais barata (R$ 0,42/kWh)."
    ),
    "carregador": lambda k: (
        f"Temos {NUM_CARREGADORES} carregadores HCA G2 ativos (22 kW cada). "
        f"Total carregado no dia: {k['ev_kwh']:.1f} kWh. "
        f"Peak shaving ativado {k['interv_ps']} vez(es) — zero multas de ultrapassagem."
    ),
    "solar": lambda k: (
        f"Geração solar aproveitada: {k['solar_kwh']:.1f} kWh. "
        f"Autoconsumo: {k['autoconsumo_pct']:.1f}% (meta do sistema: 85%). "
        f"CO₂ evitado: {k['co2_kg']:.2f} kg."
    ),
    "bateria": lambda k: (
        f"A bateria (50 kWh) carregou com excedente solar ao longo da manhã "
        f"e descarregou {k['bateria_kwh']:.1f} kWh durante o horário de ponta (17-21h), "
        "evitando usar energia cara da rede."
    ),
    "multa": lambda k: (
        f"Nenhuma multa hoje! O sistema ativou o peak shaving {k['interv_ps']} vez(es) "
        f"e manteve a demanda abaixo de {LIMITE_DEMANDA_KW:.0f} kW o tempo todo. "
        f"Estimativa de multa evitada: R$ {k['multa_evitada_r']:.2f}."
    ),
    "co2": lambda k: (
        f"Hoje foram evitados {k['co2_kg']:.2f} kg de CO₂ "
        "usando energia solar e bateria no lugar da rede elétrica. "
        f"Projeção mensal: ~{k['co2_kg'] * 30:.1f} kg."
    ),
    "pico": lambda k: (
        f"No horário de ponta (17h-21h, R$ 0,85/kWh) a bateria "
        f"forneceu {k['bateria_kwh']:.1f} kWh, reduzindo o uso da rede cara. "
        f"Peak shaving ativado {k['interv_ps']} vez(es)."
    ),
}

if pergunta:
    kpis = calcular_kpis(df)
    resposta = (
        f"Não entendi '{pergunta}'. "
        "Tente perguntar sobre: conta de luz, carregadores, solar, bateria, multa, CO₂ ou horário de pico."
    )
    for palavra_chave, fn in respostas.items():
        if palavra_chave in pergunta.lower():
            resposta = fn(kpis)
            break

    st.info(f"💬 **ChargeGrid IA:** {resposta}")


st.divider()
st.markdown("""
<div style='text-align:center;color:#484f58;font-size:12px;padding:8px 0'>
    ChargeGrid Intelligence · EV Challenge 2026 · FIAP + GoodWe · Turma 1CCPY — Grupo 05<br>
    Jair Fereira Dos Santos Neto RM 569682 &nbsp;|&nbsp;
    Matheus da Costa Goncalves RM 570756 &nbsp;|&nbsp;
    Yan Luiz Neves Lemos RM 571717 &nbsp;|&nbsp;
    Arthur dos Santos Bezerra RM 569721 &nbsp;|&nbsp;
    Carlos Henrique Fratezi RM 571792
</div>
""", unsafe_allow_html=True)
