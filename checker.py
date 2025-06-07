import time
from db import get_active_alerts, mark_as_triggered
import yfinance as yf
import asyncio

def get_price(symbol):
    data = yf.Ticker(symbol).history(period="1d")
    return data["Close"].iloc[-1]

async def start_checker(bot):
    while True:
        try:
            alerts = get_active_alerts()
            for id_, chat_id, symbol, target, direction, note in alerts:
                price = get_price(symbol)
                print(f"[Preisprüfung] {symbol}: {price:.2f} (Ziel: {target}, Richtung: {direction})")
                if (direction == "unter" and price <= target) or (direction == "über" and price >= target):
                    message = f"🔔 {symbol} {direction} {target} erreicht ({price:.2f}) → {note}"
                    await bot.send_message(chat_id=chat_id, text=message)
                    mark_as_triggered(id_)
            print("[Preisprüfung abgeschlossen] Alle Alarme überprüft.")
        except Exception as e:
            print(f"[Fehler bei Preisprüfung] {e}")
        await asyncio.sleep(60)  # Warte 60 Sekunden vor der nächsten Prüfung
