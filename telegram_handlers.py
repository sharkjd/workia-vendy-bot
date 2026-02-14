# --- Telegram Bot API ---
from telegram import Update
from telegram.ext import ContextTypes

import runtime

# Reakce na příkaz /start: pošle uživateli uvítací zprávu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ahoj! Jsem Vendy a odteď si pamatuju, co mi píšeš! 🐘")

# Reakce na každou textovou zprávu (kromě příkazů): předá ji do grafu a odpověď pošle zpět
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # Vytáhneme si unikátní ID uživatele z Telegramu
    user_id = str(update.message.chat_id)
    print(f"DEBUG: Uživatel {user_id} poslal zprávu: {user_text}")
    # Vstup do grafu: jedna nová uživatelská zpráva (historie se načte z DB podle thread_id)
    inputs = {"messages": [("user", user_text)]}

    # NOVÉ: Konfigurace s Thread ID
    # Tímto říkáme LangGraphu, do jaké "složky" v databázi se má podívat
    config = {"configurable": {"thread_id": user_id}}

    # Spustíme graf a předáme mu i ten config
    result = runtime.graph.invoke(inputs, config=config)

    # Poslední zpráva v result je odpověď modelu; její text pošleme uživateli
    bot_reply = result["messages"][-1].content
    await update.message.reply_text(bot_reply)
