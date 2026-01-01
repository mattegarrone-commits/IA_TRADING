import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.bot import InstitutionalBot
import time
import os

# Configuración de Página
st.set_page_config(
    page_title="IA Trading Institucional",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Personalizados
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stButton>button {
        width: 100%;
        background-color: #00D26A;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #00b359;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #41424C;
        text-align: center;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .status-bullish { background-color: #00D26A; color: black; }
    .status-bearish { background-color: #FF4B4B; color: white; }
    .status-neutral { background-color: #FFA500; color: black; }
    </style>
""", unsafe_allow_html=True)

# Título y Header
st.title("🏦 IA Trading Institucional | SMC Core")
st.markdown("Sistema autónomo de análisis cuantitativo y gestión de riesgo institucional.")

# Sidebar - Configuración
st.sidebar.header("⚙️ Panel de Control")

# Selección de Pares (Los mismos que en main.py)
PAIRS = [
    "EURUSD=X", "JPY=X", "GBPUSD=X", "CAD=X", "CHF=X"
]
PAIR_NAMES = {
    "EURUSD=X": "EURUSD", "JPY=X": "USDJPY", "GBPUSD=X": "GBPUSD", 
    "AUDUSD=X": "AUDUSD", "NZDUSD=X": "NZDUSD", "CHF=X": "USDCHF", "CAD=X": "USDCAD",
    "EURGBP=X": "EURGBP", "EURJPY=X": "EURJPY", "EURCHF=X": "EURCHF", 
    "EURCAD=X": "EURCAD", "EURAUD=X": "EURAUD", "EURNZD=X": "EURNZD",
    "GBPJPY=X": "GBPJPY", "GBPCHF=X": "GBPCHF", "GBPCAD=X": "GBPCAD", 
    "GBPAUD=X": "GBPAUD", "GBPNZD=X": "GBPNZD",
    "AUDJPY=X": "AUDJPY", "AUDCHF=X": "AUDCHF", "AUDCAD=X": "AUDCAD", "AUDNZD=X": "AUDNZD",
    "CADJPY=X": "CADJPY", "CADCHF=X": "CADCHF",
    "NZDJPY=X": "NZDJPY", "NZDCAD=X": "NZDCAD", "NZDCHF=X": "NZDCHF", "CHFJPY=X": "CHFJPY",
    "USDSGD=X": "USDSGD", "USDSEK=X": "USDSEK", "USDNOK=X": "USDNOK", "USDZAR=X": "USDZAR"
}

# Crear lista legible para el selectbox
readable_pairs = [PAIR_NAMES.get(p, p) for p in PAIRS]
selected_pair_name = st.sidebar.selectbox("Seleccionar Activo", readable_pairs)

# Encontrar el ticker real basado en el nombre seleccionado
selected_ticker = next((k for k, v in PAIR_NAMES.items() if v == selected_pair_name), selected_pair_name)

# Botón de Análisis
if st.sidebar.button("🔍 EJECUTAR ANÁLISIS"):
    with st.spinner(f"Analizando Estructura Institucional de {selected_pair_name}..."):
        # Instanciar Bot
        bot = InstitutionalBot()
        
        # Ejecutar análisis (ahora devuelve datos estructurados)
        # Nota: No necesitamos escribir archivo físico aquí, usamos la respuesta directa
        result = bot.run_analysis(pair=selected_ticker)
        
        # --- DISPLAY RESULTADOS ---
        
        # 1. Métricas Principales (KPIs)
        col1, col2, col3, col4 = st.columns(4)
        
        market_ctx = result.get("market_context", {})
        smc_lvls = result.get("smc_levels", {})
        
        with col1:
            st.metric("Precio Actual", f"{market_ctx.get('current_price', 0):.5f}")
        
        with col2:
            bias = market_ctx.get('bias', 'NEUTRAL')
            color = "off"
            if bias == "BULLISH": color = "normal" 
            st.metric("Sesgo Direccional", bias)
            
        with col3:
            dist_supply = smc_lvls.get('dist_supply_pips', 0)
            st.metric("Dist. Oferta (Pips)", f"{dist_supply:.1f}")
            
        with col4:
            dist_demand = smc_lvls.get('dist_demand_pips', 0)
            st.metric("Dist. Demanda (Pips)", f"{dist_demand:.1f}")

        # 2. Señal de Trading (Si existe)
        signal = result.get("signal")
        
        st.divider()
        
        if signal:
            st.success("🎯 **OPORTUNIDAD DE ALTA PROBABILIDAD DETECTADA**")
            
            s_col1, s_col2 = st.columns([1, 2])
            
            with s_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h2 style="color: {'#00D26A' if signal['type'] == 'BUY' else '#FF4B4B'};">{signal['type']}</h2>
                    <p>Probabilidad: <b>{signal['prob']}%</b></p>
                    <p>RR: <b>1:{signal['rr']:.2f}</b></p>
                </div>
                """, unsafe_allow_html=True)
                
            with s_col2:
                st.markdown("### Parámetros de Orden")
                st.markdown(f"- **Entrada:** `{signal['entry']:.5f}`")
                st.markdown(f"- **Stop Loss:** `{signal['sl']:.5f}`")
                st.markdown(f"- **Take Profit:** `{signal['tp']:.5f}`")
                st.info(f"**Tesis Institucional:** {signal['reason']}")
                
        else:
            st.warning("⚠️ **NO HAY OPERACIÓN CON VENTAJA MATEMÁTICA**")
            st.markdown(f"""
            **Análisis de Filtrado:**
            - El mercado no presenta una confluencia clara de *Estructura + Zona + Sesión*.
            - Sesión Actual: `{market_ctx.get('session', 'N/A')}`
            - La IA permanece en espera (Cash is a position).
            """)

        # 3. Visualización de Estructura (Gráfico Simple con Plotly)
        # Nota: Para un gráfico completo necesitaríamos devolver el DF entero.
        # Por ahora mostramos los niveles clave en un gráfico de "termómetro" o medidor simple.
        
        st.divider()
        st.subheader("📍 Mapa de Liquidez SMC")
        
        current = market_ctx.get('current_price', 0)
        supply = smc_lvls.get('supply_zone', 0)
        demand = smc_lvls.get('demand_zone', 0)
        
        if supply > 0 and demand > 0:
            fig = go.Figure()

            # Zona Oferta
            fig.add_trace(go.Scatter(
                x=[0, 1], y=[supply, supply], mode="lines", 
                name="Zona Oferta (Ventas)", line=dict(color="red", width=4, dash="dash")
            ))
            
            # Precio Actual
            fig.add_trace(go.Scatter(
                x=[0.5], y=[current], mode="markers+text", 
                name="Precio Actual", marker=dict(color="white", size=12),
                text=[f"Precio: {current:.5f}"], textposition="middle right"
            ))

            # Zona Demanda
            fig.add_trace(go.Scatter(
                x=[0, 1], y=[demand, demand], mode="lines", 
                name="Zona Demanda (Compras)", line=dict(color="green", width=4, dash="dash")
            ))

            fig.update_layout(
                title=f"Rango Operativo Vigente: {selected_pair_name}",
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(title="Precio", showgrid=True, gridcolor="#41424C"),
                paper_bgcolor="#0E1117",
                plot_bgcolor="#0E1117",
                font=dict(color="white"),
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Selecciona un par en el menú lateral y pulsa 'EJECUTAR ANÁLISIS' para comenzar.")
    
    # Dashboard Resumen (Placeholder para cuando no hay análisis activo)
    st.markdown("### 📊 Estado del Sistema")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Modo:** Institucional (H1)")
    with c2:
        st.markdown(f"**Activos Rasteados:** {len(PAIRS)}")
    with c3:
        st.markdown("**Gestión de Riesgo:** Activa (1%)")
