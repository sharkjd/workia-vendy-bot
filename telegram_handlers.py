# --- Telegram Bot API ---
from telegram import Update
from telegram.ext import ContextTypes

import runtime
from tools.sea_database import get_initial_state 

# Reakce na příkaz /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ahoj! Jsem Vendy z Workia. 🤖")

# Reakce na zprávy
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = str(update.message.chat_id)
    
    config = {"configurable": {"thread_id": user_id}}

    # Kontrola stavu v paměti (checkpoint v Postgresu)
    current = runtime.graph.get_state(config)

    if current.values is None or not current.values:
        print(f"🔍 Inicializace: Tahám data ze SeaTable pro ID {user_id}...")
        initial_db_data = get_initial_state(user_id)
        
        if initial_db_data:
            inputs = {
                "messages": [("user", user_text)],
                "row_id": initial_db_data["row_id"],
                "status": initial_db_data["status"],
                "candidate_data": initial_db_data["candidate_data"],
                "corrected_info": initial_db_data["corrected_info"],
            }
        else:
            await update.message.reply_text("Nemohu tě najít v databázi.")
            return
    else:
        # Pokračování konverzace (stav už máme v DB)
        inputs = {"messages": [("user", user_text)]}

    # Spuštění grafu (Vendy přemýšlí a případně volá tools)
    result = runtime.graph.invoke(inputs, config=config)

    # --- OPRAVENÉ ODSAZENÍ A ZPRACOVÁNÍ ODPOVĚDI ---
    last_msg = result["messages"][-1]
    
    # Gemini 2.5 často vrací obsah jako list objektů místo čistého stringu
    if isinstance(last_msg.content, list):
        # Bezpečně vytáhneme textové části, pokud existují
        parts = []
        for item in last_msg.content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        bot_reply = " ".join(parts)
    else:
        bot_reply = last_msg.content

    # Debug výpis do terminálu
    print(f"DEBUG: Status po průběhu grafu: {result.get('status')}")

    # Kontrola prázdné zprávy s bezpečným převedením na string před .strip()
    if not bot_reply or not str(bot_reply).strip():
        bot_reply = "Omlouvám se, ale zrovna mi to v té mé digitální hlavě trochu drhne. Zkusíš to znovu?"
        print("❌ ERROR: Bot vygeneroval prázdnou zprávu!")

    # Odeslání odpovědi uživateli na Telegram
    await update.message.reply_text(bot_reply, parse_mode='HTML')