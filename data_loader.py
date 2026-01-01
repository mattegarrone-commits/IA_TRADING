import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz

def get_forex_data(pair="EURUSD=X", interval="15m", period="5d"):
    """
    Descarga datos de Forex intradía.
    Intervalos válidos: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Periodo máximo para 1m es 7 días. Para 15m es 60 días.
    """
    print(f"Descargando datos para {pair} ({interval})...")
    try:
        data = yf.download(pair, period=period, interval=interval, progress=False, auto_adjust=True)
        if data.empty:
            print("No se encontraron datos. Verifique el ticker (ej: EURUSD=X).")
            return pd.DataFrame()
        
        # Aplanar MultiIndex si existe (común en versiones recientes de yfinance)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Filtrar por sesiones si es necesario
        data = add_session_info(data)
        
        return data
    except Exception as e:
        print(f"Error descargando datos: {e}")
        return pd.DataFrame()

def add_session_info(df):
    """
    Añade columnas booleanas para sesiones de Londres y Nueva York.
    Horarios aproximados (UTC):
    Londres: 08:00 - 17:00
    Nueva York: 13:00 - 22:00
    """
    if df.empty:
        return df

    # Asegurar que el índice es datetime y tiene zona horaria
    if df.index.tz is None:
        # Asumimos que yfinance devuelve UTC
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')

    # Definir horarios (simplificado, ajustar según horario de verano/invierno real si se requiere precisión extrema)
    # Londres (aprox 7am/8am UTC start)
    df['is_london'] = (df.index.hour >= 8) & (df.index.hour < 17)
    
    # NY (aprox 13pm/14pm UTC start)
    df['is_ny'] = (df.index.hour >= 13) & (df.index.hour < 22)
    
    # Killzones (Solapamiento de alta volatilidad Londres/NY: 13:00 - 17:00 UTC)
    df['is_killzone'] = df['is_london'] & df['is_ny']
    
    return df
