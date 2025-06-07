from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from db import add_alert, get_all_alarms, delete_alert, clear_user_alarms
from checker import start_checker
import yfinance as yf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

def get_price(symbol):
    data = yf.Ticker(symbol).history(period="1d")
    return data["Close"].iloc[-1]

async def post_init(application):
    application.job_queue.run_repeating(checker_job, interval=120, first=5)

async def checker_job(context: ContextTypes.DEFAULT_TYPE):
    await start_checker(context.bot)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Preisalarm-Bot aktiv. Sende z. B.:\n`AAPL 160 nachkaufen`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.strip().split()
        symbol = parts[0].upper()
        target = float(parts[1])
        note = " ".join(parts[2:])
        price = get_price(symbol)
        direction = "unter" if target < price else "über"
        add_alert(update.effective_chat.id, symbol, target, direction, note)
        await update.message.reply_text(f"✅ Preisalarm gespeichert: {symbol} {direction} {target} → {note}")
    except Exception as e:
        await update.message.reply_text(f"❗ Fehler: {e}\nBitte im Format `SYMBOL KURSZIEL NOTIZ` senden.")

async def list_alarms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    alarms = get_all_alarms(user_id)

    if not alarms:
        await update.message.reply_text("🔕 Du hast aktuell keine gespeicherten Preisalarme.")
        return

    text = "📋 Deine aktuellen Preisalarme:\n\n"
    for alarm in alarms:
        symbol = alarm["symbol"]
        target_price = alarm["target"]
        note = alarm["note"]
        text += f"• {symbol} bei {target_price:.2f} € — 📝 {note}\n"

    await update.message.reply_text(text)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    alarms = get_all_alarms(user_id)

    if not alarms:
        await update.message.reply_text("❌ Keine Preisalarme gefunden.")
        return

    keyboard = []
    for alarm in alarms:
        button_text = f"{alarm['symbol']} bei {alarm['target']:.2f} — {alarm['note']}"
        callback_data = f"delete:{alarm['id']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🗑 Wähle einen Alarm zum Löschen:", reply_markup=reply_markup)

async def clear_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    clear_user_alarms(chat_id)
    await update.message.reply_text("🗑 Alle Alarme wurden gelöscht.")

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("delete:"):
        alert_id = int(query.data.split(":")[1])
        delete_alert(alert_id)
        await query.edit_message_text("✅ Alarm wurde gelöscht.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 <b>Preisalarm Bot Hilfe</b>\n\n"
        "<b>Verfügbare Befehle:</b>\n"
        "/start – Zeigt die Startnachricht an\n"
        "/help – Zeigt diese Hilfeseite an\n"
        "/alarms – Listet alle deine gespeicherten Preisalarme auf\n"
        "/delete – Lösche einen gespeicherten Preisalarm\n"
        "/cleardata – Löscht alle deine Preisalarme\n"
        "/lookup SYMBOL – Zeigt den aktuellen Kurs eines Symbols an (z.B. /lookup AAPL)\n\n"
        "<b>Preisalarm setzen:</b>\n"
        "Sende eine Nachricht im Format:\n"
        "<code>SYMBOL KURSZIEL NOTIZ</code>\n"
        "Beispiel: <code>AAPL 160 nachkaufen</code>\n\n"
        "<b>Hinweise:</b>\n"
        "– SYMBOL ist das Börsenkürzel (z.B. AAPL, MSFT, TSLA)\n"
        "– KURSZIEL ist der Preis, bei dem du benachrichtigt werden möchtest\n"
        "– NOTIZ ist optional und kann z.B. den Grund oder eine Erinnerung enthalten\n"
        "– Preise werden, wenn möglich, in EUR angezeigt.\n"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Bitte gib ein Symbol an, z.B. `/lookup AAPL`")
        return
    symbol = context.args[0].upper()
    try:
        price = get_price(symbol)
        await update.message.reply_text(f"💹 Aktueller Preis für {symbol}: {price:.2f}")
    except Exception as e:
        await update.message.reply_text(f"❗ Fehler beim Nachschlagen von {symbol}: {e}")

# 🟢 Startpunkt
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("alarms", list_alarms))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("cleardata", clear_database))
    app.add_handler(CommandHandler("lookup", lookup))  # <--- Added lookup command
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_delete_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


    print("🤖 Bot läuft...")
    app.run_polling()
