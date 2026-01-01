import json
import os
from datetime import datetime

class TradeJournal:
    def __init__(self, filepath="trade_journal.json"):
        self.filepath = filepath
        self.trades = self._load_journal()

    def _load_journal(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except:
            return []

    def log_trade(self, trade_data):
        """
        Registra un trade propuesto o ejecutado.
        trade_data: dict con entry, sl, tp, reason, etc.
        """
        trade_data['timestamp'] = datetime.now().isoformat()
        self.trades.append(trade_data)
        self._save_journal()

    def _save_journal(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.trades, f, indent=4)

    def get_stats(self):
        """Retorna estadísticas básicas de aprendizaje"""
        total = len(self.trades)
        if total == 0:
            return "Sin trades registrados."
        
        # Aquí se implementaría el análisis de "wins/losses" reales si tuvieramos feedback de ejecución.
        return f"Trades Analizados: {total}"
