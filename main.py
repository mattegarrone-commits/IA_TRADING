import os
import sys
import time
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit.web import cli as stcli
from core.bot import InstitutionalBot

# --- UTILS ---
def get_candle_countdown(timeframe):
    """Calcula el tiempo restante para el cierre de vela y la hora de apertura de la siguiente."""
    now = datetime.utcnow()
    
    if timeframe == '1m':
        interval_seconds = 60
    elif timeframe == '5m':
        interval_seconds = 5 * 60
    elif timeframe == '15m':
        interval_seconds = 15 * 60
    elif timeframe == '1h':
        interval_seconds = 60 * 60
    else:
        return "N/A", "N/A"

    # Calcular segundos pasados desde el inicio del intervalo
    total_seconds = now.hour * 3600 + now.minute * 60 + now.second
    seconds_past = total_seconds % interval_seconds
    seconds_left = interval_seconds - seconds_past
    
    next_open_dt = now + timedelta(seconds=seconds_left)
    
    minutes = int(seconds_left // 60)
    seconds = int(seconds_left % 60)
    
    countdown_str = f"{minutes}m {seconds}s"
    next_open_str = next_open_dt.strftime("%H:%M UTC")
    
    return countdown_str, next_open_str

def timeframe_seconds(tf):
    if tf == '1m': return 60
    if tf == '5m': return 5 * 60
    if tf == '15m': return 15 * 60
    if tf == '1h': return 60 * 60
    return 0

def format_total_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m >= 60:
        h = m // 60
        rem_m = m % 60
        return f"{h}h {rem_m}m"
    return f"{m}m {s}s"

# --- CONFIGURACIÓN DE PARES ---
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

# --- FUNCIÓN DE GRAFICADO ---
def create_chart(pair_name, df, signal=None, smc_levels=None):
    if df is None or df.empty:
        return None
        
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], 
                name=pair_name)])

    # Add SMC Levels
    if smc_levels:
        supply = smc_levels.get('supply_zone')
        demand = smc_levels.get('demand_zone')
        if supply:
            fig.add_hline(y=supply, line_dash="dash", line_color="rgba(255, 0, 0, 0.5)", annotation_text="Supply")
        if demand:
            fig.add_hline(y=demand, line_dash="dash", line_color="rgba(0, 255, 0, 0.5)", annotation_text="Demand")

    # Add Signal Levels
    if signal:
        fig.add_hline(y=signal['entry'], line_color="#1E90FF", line_width=2, annotation_text="ENTRY")
        fig.add_hline(y=signal['sl'], line_color="#FF4B4B", line_width=2, annotation_text="SL")
        fig.add_hline(y=signal['tp'], line_color="#00D26A", line_width=2, annotation_text="TP")

    fig.update_layout(
        title=dict(text=f"{pair_name}", font=dict(size=14)), 
        xaxis_rangeslider_visible=False, 
        height=300, # Altura reducida para móvil
        margin=dict(l=10, r=10, t=30, b=10),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10)
    )
    return fig

# --- FUNCIÓN PRINCIPAL DE INTERFAZ ---
def main_gui():
    st.set_page_config(
        page_title="IA Trading Mobile",
        page_icon="📱",
        layout="centered", # Layout centrado es mejor para móviles
        initial_sidebar_state="collapsed"
    )

    # Estilos CSS Mobile-First
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            background-color: #00D26A;
            color: white;
            font-weight: bold;
            border-radius: 12px;
            padding: 15px;
            font-size: 18px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .stButton>button:hover {
            background-color: #00b359;
            transform: translateY(-2px);
        }
        .card-container {
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #333;
            background-color: #161B22;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .card-success {
            border-left: 5px solid #00D26A;
        }
        .metric-label { font-size: 0.75em; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .metric-value { font-size: 1.2em; font-weight: bold; color: #FFF; }
        .signal-header {
            font-size: 1.3em;
            font-weight: 900;
            margin-bottom: 15px;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            text-transform: uppercase;
        }
        .signal-buy { background: linear-gradient(90deg, rgba(0,210,106,0.1) 0%, rgba(0,210,106,0.2) 100%); color: #00D26A; border: 1px solid #00D26A; }
        .signal-sell { background: linear-gradient(90deg, rgba(255,75,75,0.1) 0%, rgba(255,75,75,0.2) 100%); color: #FF4B4B; border: 1px solid #FF4B4B; }
        
        /* Ajustes para móviles */
        div.block-container { padding-top: 2rem; padding-bottom: 5rem; }
        h1 { font-size: 1.8rem !important; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📱 IA Trading Mobile")
    st.caption(f"Bot Institucional • {len(PAIRS)} Pares • SMC Core")

    # Selección de Timeframe (Botones grandes)
    selected_timeframe = "1h" # Default
    
    col_btns = st.columns(2)
    with col_btns[0]:
        if st.button("M1 ⚡", key="btn_m1"): selected_timeframe = "1m"
        if st.button("M15 🕒", key="btn_m15"): selected_timeframe = "15m"
    with col_btns[1]:
        if st.button("M5 🚀", key="btn_m5"): selected_timeframe = "5m"
        if st.button("H1 🏛️", key="btn_h1"): selected_timeframe = "1h"

    # Lógica de Botones (Persistencia simple)
    run_scan = False
    if st.session_state.get("btn_m1"): selected_timeframe = "1m"; run_scan = True
    elif st.session_state.get("btn_m5"): selected_timeframe = "5m"; run_scan = True
    elif st.session_state.get("btn_m15"): selected_timeframe = "15m"; run_scan = True
    elif st.session_state.get("btn_h1"): selected_timeframe = "1h"; run_scan = True

    if run_scan:
        # Calcular Countdown
        countdown, next_open = get_candle_countdown(selected_timeframe)

        st.success(f"Escaneando Mercado ({selected_timeframe})...")
        
        # Info rápida
        c1, c2 = st.columns(2)
        c1.metric("Cierre Vela", countdown)
        c2.metric("Hora UTC", datetime.utcnow().strftime("%H:%M"))

        bot = InstitutionalBot()
        output_dir = f"Pares_{selected_timeframe}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        progress_bar = st.progress(0)
        
        # Limpiar resultados anteriores
        st.session_state['scan_results'] = []
        
        for i, ticker in enumerate(PAIRS):
            pair_name = PAIR_NAMES.get(ticker, ticker.replace("=X", ""))
            progress_bar.progress((i + 1) / len(PAIRS))
            
            report_path = os.path.join(output_dir, f"{pair_name}.txt")
            try:
                result = bot.run_analysis(pair=ticker, timeframe=selected_timeframe, output_file=report_path)
                st.session_state['scan_results'].append({
                    'pair_name': pair_name,
                    'ticker': ticker,
                    'result': result
                })
            except Exception as e:
                continue

        progress_bar.empty()

    # --- RENDERIZADO DE RESULTADOS ---
    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        
        opps_found = 0
        
        # Iterar resultados (Layout Vertical para Mobile)
        for item in st.session_state['scan_results']:
            pair_name = item['pair_name']
            result = item['result']
            ticker = item['ticker']

            signal = result.get("signal")
            market_ctx = result.get("market_context", {})
            smc_levels = result.get("smc_levels", {})
            df_hist = result.get("df")
            
            # Solo mostrar si hay señal o si el usuario quiere ver todo (por ahora mostramos todo colapsado si no hay señal)
            
            if signal:
                # Ensure RR is present and accurate
                if 'rr' not in signal:
                    risk = abs(signal['entry'] - signal['sl'])
                    reward = abs(signal['tp'] - signal['entry'])
                    signal['rr'] = reward / risk if risk > 0 else 0

                opps_found += 1
                card_class = "card-success"
                signal_type = signal['type']
                signal_color = "signal-buy" if signal_type == "BUY" else "signal-sell"
                
                html_content = f"""
                <div class="card-container {card_class}">
                    <div class="signal-header {signal_color}">
                        {pair_name} • {signal_type}
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-bottom: 10px;">
                        <div style="text-align:center;">
                            <div class="metric-label">Probabilidad</div>
                            <div class="metric-value">{signal['prob']}%</div>
                        </div>
                        <div style="text-align:center;">
                            <div class="metric-label">R:B</div>
                            <div class="metric-value">1:{signal['rr']:.2f}</div>
                        </div>
                    </div>
                    <hr style="border-color: #333; margin: 5px 0;">
                    <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap: 5px; text-align:center; margin-top:10px;">
                        <div>
                            <div class="metric-label" style="color:#1E90FF">Entrada</div>
                            <div style="color:#FFF; font-weight:bold;">{signal['entry']:.5f}</div>
                        </div>
                        <div>
                            <div class="metric-label" style="color:#FF4B4B">Stop</div>
                            <div style="color:#FFF; font-weight:bold;">{signal['sl']:.5f}</div>
                        </div>
                        <div>
                            <div class="metric-label" style="color:#00D26A">Take</div>
                            <div style="color:#FFF; font-weight:bold;">{signal['tp']:.5f}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; font-size: 0.8em; color: #888; text-align: center;">
                        <i>{signal['reason']}</i>
                    </div>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)
                
                # Gráfico
                fig = create_chart(pair_name, df_hist, signal, smc_levels)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{pair_name}", config={'displayModeBar': False})
            
            else:
                # Versión compacta para "Sin Señal"
                with st.expander(f"{pair_name} - {market_ctx.get('bias', 'NEUTRAL')}"):
                     st.write(f"Sesión: {market_ctx.get('session', 'N/A')}")
                     fig = create_chart(pair_name, df_hist, None, smc_levels)
                     if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{pair_name}_neut", config={'displayModeBar': False})

        if opps_found == 0 and run_scan:
            st.info("No se encontraron oportunidades de alta probabilidad.")

# --- ENTRY POINT ---
if __name__ == '__main__':
    if st.runtime.exists():
        main_gui()
    else:
        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
