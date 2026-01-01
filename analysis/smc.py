import pandas as pd
import numpy as np

class SMCAnalyzer:
    """
    Analizador de Smart Money Concepts (SMC).
    Detecta estructura de mercado, BOS, CHoCH y liquidez.
    """
    def __init__(self, swing_length=5):
        self.swing_length = swing_length

    def analyze(self, df):
        if df.empty:
            return df
        
        df = df.copy()
        
        # 1. Identificar Pivots (Fractales)
        df = self._identify_pivots(df)
        
        # 2. Identificar Estructura (BOS / CHoCH) + Indicadores
        df = self._identify_structure(df)
        
        # 3. Identificar Liquidez
        df = self._identify_liquidity(df)
        
        # 4. Detectar FVGs
        df = self.detect_fvgs(df)
        
        return df

    def _identify_pivots(self, df):
        """
        Detecta Highs y Lows locales usando una ventana deslizante.
        """
        # Un high local es mayor que sus vecinos
        df['is_pivot_high'] = False
        df['is_pivot_low'] = False
        
        # Usamos rolling window para eficiencia, aunque lo ideal es comparar i-n ... i ... i+n
        # Para simplificar y vectorizar:
        # Un punto es high si es el máximo en una ventana centrada
        window = 2 * self.swing_length + 1
        
        # Shift para centrar la ventana en el punto actual
        # Max/Min en ventana
        rolling_max = df['High'].rolling(window=window, center=True).max()
        rolling_min = df['Low'].rolling(window=window, center=True).min()
        
        df.loc[df['High'] == rolling_max, 'is_pivot_high'] = True
        df.loc[df['Low'] == rolling_min, 'is_pivot_low'] = True
        
        return df

    def _identify_structure(self, df):
        """
        Determina BOS y CHoCH.
        """
        # Calcular EMAs primero para uso general
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        df['EMA_200'] = df['Close'].ewm(span=200).mean()
        
        # Calcular ATR (14) para estimación de duración
        df['tr0'] = abs(df['High'] - df['Low'])
        df['tr1'] = abs(df['High'] - df['Close'].shift())
        df['tr2'] = abs(df['Low'] - df['Close'].shift())
        df['TR'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        df['ATR'] = df['ATR'].ffill().bfill()

        # Calcular RSI (14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Marcamos niveles clave en cada fila (forward fill de pivots)
        df['last_pivot_high'] = df['High'].where(df['is_pivot_high']).ffill()
        df['last_pivot_low'] = df['Low'].where(df['is_pivot_low']).ffill()
        
        # Tendencia basada en EMA rápida para contexto general
        conditions = [
            (df['Close'] > df['EMA_50']) & (df['EMA_50'] > df['EMA_200']),
            (df['Close'] < df['EMA_50']) & (df['EMA_50'] < df['EMA_200'])
        ]
        choices = ['BULLISH', 'BEARISH']
        df['trend'] = np.select(conditions, choices, default='RANGING')
        
        return df

    def _identify_liquidity(self, df):
        """
        Detecta Equal Highs (EQH) y Equal Lows (EQL).
        Rango de tolerancia pequeño.
        """
        # Simplificado: Marcar zonas de liquidez como máximos/mínimos de N periodos
        # que no han sido tomados aún (aproximación)
        df['has_liquidity_above'] = False # Placeholder para lógica futura
        df['has_liquidity_below'] = False
        return df

    def detect_fvgs(self, df):
        """
        Detecta Fair Value Gaps (Imbalances).
        FVG Alcista: Low de vela [i-2] > High de vela [i] (Gap entre 1 y 3)
        FVG Bajista: High de vela [i-2] < Low de vela [i]
        """
        df['fvg_bullish'] = False
        df['fvg_bearish'] = False
        df['fvg_top'] = np.nan
        df['fvg_bottom'] = np.nan
        
        # Vectorizado
        # Vela i (actual) vs Vela i-2
        # Shift 2 para comparar con hace 2 velas
        
        # FVG Alcista (Gap creado por vela i-1 siendo muy fuerte)
        # Low de vela i (la actual tras el movimiento) NO: FVG se define tras cierre de vela i-1.
        # Estrictamente: FVG se confirma en vela i.
        # Gap está entre High de vela i-2 y Low de vela i.
        
        # High de vela i-2
        prev_high = df['High'].shift(2)
        # Low de vela i
        curr_low = df['Low']
        
        # Low de vela i-2
        prev_low = df['Low'].shift(2)
        # High de vela i
        curr_high = df['High']
        
        # Bullish Imbalance: Low(i) > High(i-2)
        bullish_cond = curr_low > prev_high
        df.loc[bullish_cond, 'fvg_bullish'] = True
        df.loc[bullish_cond, 'fvg_bottom'] = prev_high
        df.loc[bullish_cond, 'fvg_top'] = curr_low
        
        # Bearish Imbalance: High(i) < Low(i-2)
        bearish_cond = curr_high < prev_low
        df.loc[bearish_cond, 'fvg_bearish'] = True
        df.loc[bearish_cond, 'fvg_top'] = prev_low
        df.loc[bearish_cond, 'fvg_bottom'] = curr_high
        
        return df

    def get_market_bias(self, df):
        """Retorna el sesgo direccional general basado en la última vela analizada"""
        if df.empty:
            return "NEUTRAL"
        return df['trend'].iloc[-1]
