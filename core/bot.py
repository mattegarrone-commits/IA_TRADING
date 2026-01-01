from data_loader import get_forex_data
from analysis.smc import SMCAnalyzer
from core.risk import RiskManager
from core.journal import TradeJournal
import pandas as pd
import os
from datetime import datetime

class InstitutionalBot:
    def __init__(self):
        self.smc = SMCAnalyzer()
        self.risk = RiskManager()
        self.journal = TradeJournal()

    def run_analysis(self, pair="EURUSD=X", timeframe="1h", output_file=None):
        """
        Ejecuta el análisis. Si output_file se proporciona, escribe el resultado en ese archivo.
        Devuelve un diccionario con los datos estructurados para su uso en interfaces (Streamlit).
        Timeframe puede ser: "1m", "5m", "15m", "1h".
        """
        result_data = {
            "pair": pair,
            "timeframe": timeframe,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "market_context": {},
            "smc_levels": {},
            "signal": None,
            "df": None
        }

        output_lines = []
        
        def log(msg):
            print(msg)
            output_lines.append(msg)

        log(f"============================================================")
        log(f"   REPORTE INSTITUCIONAL ({timeframe}): {pair}")
        log(f"   FECHA: {result_data['timestamp']}")
        log(f"============================================================")
        
        # 1. Cargar Datos (Ajustar periodo según timeframe para maximizar datos sin romper límites de Yahoo)
        # Límites Yahoo: 1m=7d, 5m/15m=60d, 1h=730d
        period = "730d"
        if timeframe == "1m":
            period = "5d" # Seguro dentro de 7d
        elif timeframe in ["5m", "15m"]:
            period = "59d" # Seguro dentro de 60d
        
        df = get_forex_data(pair, interval=timeframe, period=period)
        if df.empty:
            log(f"[ERROR] No se pudieron cargar datos para {pair} ({timeframe})")
            self._write_output(output_file, output_lines)
            return result_data

        # 2. Análisis Técnico SMC
        df = self.smc.analyze(df)
        
        # Guardar DF para gráficos (últimas 200 velas para rendimiento)
        result_data["df"] = df.tail(200)

        
        # 3. Contexto de Mercado Detallado
        last_row = df.iloc[-1]
        current_price = last_row['Close']
        bias = self.smc.get_market_bias(df)
        
        # Obtener niveles clave
        last_pivot_high = last_row.get('last_pivot_high', 0)
        last_pivot_low = last_row.get('last_pivot_low', 0)
        
        # Estado de Sesión
        session_status = []
        if last_row['is_london']: session_status.append("LONDRES")
        if last_row['is_ny']: session_status.append("NUEVA YORK")
        if not session_status: session_status.append("ASIA / CIERRE (Baja Liquidez)")
        
        result_data["market_context"] = {
            "current_price": current_price,
            "bias": bias,
            "session": ' + '.join(session_status)
        }

        log(f"\n[1] CONTEXTO DE MERCADO")
        log(f"    Precio Actual:       {current_price:.5f}")
        log(f"    Tendencia Dominante: {bias}")
        log(f"    Sesión Activa:       {' + '.join(session_status)}")
        
        log(f"\n[2] NIVELES ESTRUCTURALES (SMC)")
        log(f"    Último High Validado (Oferta):   {last_pivot_high:.5f}")
        log(f"    Último Low Validado (Demanda):   {last_pivot_low:.5f}")
        
        # Calcular distancias a niveles clave
        dist_high = abs(current_price - last_pivot_high) * 10000
        dist_low = abs(current_price - last_pivot_low) * 10000
        
        result_data["smc_levels"] = {
            "supply_zone": last_pivot_high,
            "demand_zone": last_pivot_low,
            "dist_supply_pips": dist_high,
            "dist_demand_pips": dist_low
        }

        log(f"    Distancia a Oferta:  {dist_high:.1f} pips")
        log(f"    Distancia a Demanda: {dist_low:.1f} pips")

        # 4. Búsqueda de Setup
        log(f"\n[3] ANÁLISIS DE OPORTUNIDAD")
        setup = self._find_setup(df, bias)

        if setup:
            signal_data = self._execute_signal(setup, pair, log)
            result_data["signal"] = signal_data
        else:
            log("    >> NO HAY OPERACIÓN CON VENTAJA MATEMÁTICA")
            log("    Razón: No se cumplen condiciones de confluencia (Estructura + Zona + Sesión).")
            if not (last_row['is_london'] or last_row['is_ny']):
                log("    Nota: Mercado fuera de horario institucional operativo.")

        log(f"\n============================================================")
        self._write_output(output_file, output_lines)
        
        return result_data


    def _write_output(self, filepath, lines):
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
            except Exception as e:
                print(f"Error escribiendo reporte en {filepath}: {e}")

    def _find_setup(self, df, bias):
        last_row = df.iloc[-1]
        
        # Estrategias:
        # 1. SMC Reversal (Order Block / Estructura)
        # 2. FVG Entry (Rebalanceo)
        # 3. EMA Trend Follow (Retroceso a media móvil)
        
        # Filtro de Sesión RELAJADO: Si estamos fuera de sesión, exigimos más calidad, 
        # pero NO bloqueamos si la estructura es perfecta.
        is_in_session = last_row['is_london'] or last_row['is_ny']
        
        setup = None

        # --- ESTRATEGIA 1: SMC REVERSAL (Zonas de Oferta/Demanda) ---
        if bias == "BULLISH":
            last_pivot_low = df['last_pivot_low'].iloc[-1]
            if not pd.isna(last_pivot_low):
                dist_pips = (last_row['Close'] - last_pivot_low) * 10000
                # Tolerancia ampliada a 30 pips para pares volátiles
                if 0 < dist_pips < 30: 
                    sl = last_pivot_low - 0.0005
                    tp = last_row['Close'] + (last_row['Close'] - sl) * 2.5
                    setup = {
                        'type': 'BUY',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 85 if is_in_session else 75,
                        'reason': "SMC: Retesteo de Zona de Demanda (Order Block)"
                    }

        elif bias == "BEARISH":
            last_pivot_high = df['last_pivot_high'].iloc[-1]
            if not pd.isna(last_pivot_high):
                dist_pips = (last_pivot_high - last_row['Close']) * 10000
                if 0 < dist_pips < 30:
                    sl = last_pivot_high + 0.0005
                    tp = last_row['Close'] - (sl - last_row['Close']) * 2.5
                    setup = {
                        'type': 'SELL',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 85 if is_in_session else 75,
                        'reason': "SMC: Retesteo de Zona de Oferta (Order Block)"
                    }

        if setup: return setup

        # --- ESTRATEGIA 2: FVG ENTRY (Rebalanceo) ---
        # Si el precio está dentro de un FVG contrario al movimiento reciente pero a favor de tendencia mayor
        if bias == "BULLISH" and last_row.get('fvg_bullish'):
            # Estamos en FVG alcista
            fvg_bottom = last_row['fvg_bottom']
            sl = fvg_bottom - 0.0003
            tp = last_row['Close'] + (last_row['Close'] - sl) * 2.5
            setup = {
                'type': 'BUY',
                'entry': last_row['Close'],
                'sl': sl,
                'tp': tp,
                'prob': 80 if is_in_session else 70,
                'reason': "FVG: Rebalanceo de Imbalance Alcista"
            }
        
        elif bias == "BEARISH" and last_row.get('fvg_bearish'):
            # Estamos en FVG bajista
            fvg_top = last_row['fvg_top']
            sl = fvg_top + 0.0003
            tp = last_row['Close'] - (sl - last_row['Close']) * 2.5
            setup = {
                'type': 'SELL',
                'entry': last_row['Close'],
                'sl': sl,
                'tp': tp,
                'prob': 80 if is_in_session else 70,
                'reason': "FVG: Rebalanceo de Imbalance Bajista"
            }

        # No retornar aún: calcularemos duración estimada más abajo si hay setup

        # --- ESTRATEGIA 3: EMA TREND FOLLOW (Retroceso Dinámico) ---
        # Si precio toca EMA 50 en tendencia
        ema_50 = last_row.get('EMA_50')
        if ema_50:
            dist_ema = abs(last_row['Close'] - ema_50) * 10000
            
            if dist_ema < 15: # Cerca de la EMA
                if bias == "BULLISH" and last_row['Close'] > ema_50:
                    sl = ema_50 - 0.0010 # SL debajo de EMA
                    tp = last_row['Close'] + (last_row['Close'] - sl) * 2
                    setup = {
                        'type': 'BUY',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 75 if is_in_session else 65,
                        'reason': "Trend: Rebote Dinámico en EMA 50"
                    }
                elif bias == "BEARISH" and last_row['Close'] < ema_50:
                    sl = ema_50 + 0.0010
                    tp = last_row['Close'] - (sl - last_row['Close']) * 2
                    setup = {
                        'type': 'SELL',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 75 if is_in_session else 65,
                        'reason': "Trend: Rechazo Dinámico en EMA 50"
                    }

        # Filtro final de calidad: RSI no debe estar sobrecomprado/sobrevendido en contra
        if setup:
            rsi = last_row.get('RSI', 50)
            if setup['type'] == 'BUY' and rsi > 70: return None # No comprar en sobrecompra extrema
            if setup['type'] == 'SELL' and rsi < 30: return None # No vender en sobreventa extrema

        # --- ESTRATEGIA 4: RANGE SCALP (Mercados Laterales / Asia) ---
        if not setup and bias == "RANGING":
            rsi = last_row.get('RSI', 50)
            last_pivot_high = df['last_pivot_high'].iloc[-1]
            last_pivot_low = df['last_pivot_low'].iloc[-1]
            
            # Venta en Techo de Rango (RSI > 50 es suficiente en rango lateral)
            if not pd.isna(last_pivot_high) and rsi > 50: 
                dist_pips = (last_pivot_high - last_row['Close']) * 10000
                if 0 < dist_pips < 30: # Ampliado a 30 pips
                    sl = last_pivot_high + 0.0005
                    tp = last_row['Close'] - (sl - last_row['Close']) * 2 # RR 1:2
                    setup = {
                        'type': 'SELL',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 70, 
                        'reason': "Rango: Rechazo en Resistencia (Scalping)"
                    }
            
            # Compra en Piso de Rango (RSI < 50 es suficiente)
            if not setup and not pd.isna(last_pivot_low) and rsi < 50:
                dist_pips = (last_row['Close'] - last_pivot_low) * 10000
                if 0 < dist_pips < 30:
                    sl = last_pivot_low - 0.0005
                    tp = last_row['Close'] + (last_row['Close'] - sl) * 2
                    setup = {
                        'type': 'BUY',
                        'entry': last_row['Close'],
                        'sl': sl,
                        'tp': tp,
                        'prob': 70,
                        'reason': "Rango: Rebote en Soporte (Scalping)"
                    }

        # Calcular duración estimada 1–5 velas con fallback robusto
        if setup:
            atr = last_row.get('ATR', None)
            if atr is None or pd.isna(atr) or atr <= 0:
                recent = df.tail(20)
                atr = (recent['High'] - recent['Low']).mean()
            if atr is None or pd.isna(atr) or atr <= 0:
                recent = df.tail(20)
                atr = abs(recent['Close'].diff()).mean()
            if atr is None or pd.isna(atr) or atr <= 0:
                atr = abs(setup['entry'] - setup['sl']) * 0.4
            dist_tp = abs(setup['tp'] - setup['entry'])
            bars_est = dist_tp / max(1e-9, 0.7 * atr)
            duration = int(round(bars_est))
            if duration < 1: duration = 1
            if duration > 5: duration = 5
            setup['duration'] = duration

        return setup

    def _execute_signal(self, setup, pair, log_func):
        risk_per_share = abs(setup['entry'] - setup['sl'])
        reward_per_share = abs(setup['tp'] - setup['entry'])
        rr_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0
        
        valid, msg = self.risk.validate_trade(setup['prob'], rr_ratio)
        
        if not valid:
            log_func(f"    >> Setup descartado por Riesgo: {msg}")
            log_func("    NO HAY OPERACIÓN CON VENTAJA MATEMÁTICA")
            return None

        log_func("\n    >>> ¡OPORTUNIDAD INSTITUCIONAL DETECTADA! <<<")
        log_func(f"    Operación:          {setup['type']}")
        log_func(f"    Par:                {pair}")
        log_func(f"    Entrada exacta:     {setup['entry']:.5f}")
        log_func(f"    Stop Loss:          {setup['sl']:.5f}")
        log_func(f"    Take Profit:        {setup['tp']:.5f}")
        log_func(f"    Ratio Riesgo/Ben:   1:{rr_ratio:.2f}")
        log_func(f"    Probabilidad est.:  {setup['prob']}%")
        log_func(f"    Justificación:      {setup['reason']}")
        
        self.journal.log_trade(setup)
        
        # Devolver datos estructurados de la señal
        return {
            "type": setup['type'],
            "entry": setup['entry'],
            "sl": setup['sl'],
            "tp": setup['tp'],
            "rr": rr_ratio,
            "prob": setup['prob'],
            "reason": setup['reason'],
            "duration": setup.get('duration', 0)
        }
