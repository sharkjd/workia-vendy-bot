# --- Telegram Bot API ---
import uuid
import os
from telegram import Update
from telegram.ext import ContextTypes

# Ostatní tvoje moduly
import runtime
from tools.voice_processor import transcribe_voice
from tools.sea_database import get_initial_state

# Reakce na příkaz /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ahoj! Jsem Vendy z Workia. 🤖")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Informujeme uživatele, že posloucháme (dobré pro UX)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 2. Stažení hlasového souboru
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    
    # Vytvoříme dočasný název souboru
    temp_filename = f"voice_{uuid.uuid4()}.ogg"
    await file.download_to_drive(temp_filename)

    # 3. UNIVERZÁLNÍ PŘEPIS (Whisper)
    # Tuhle část pak jen zkopíruješ pro WhatsApp handler
    text_from_voice = await transcribe_voice(temp_filename)

    if text_from_voice and len(text_from_voice.strip()) > 1:
        # 4. Předáme přepsaný text do handle_message přes parametr overridden_text,
        # protože objekt Message z python-telegram-bot je immutable (nelze na něm nastavovat atributy).
        print(f"🎤 Hlasový přepis: {text_from_voice}")
        await handle_message(update, context, overridden_text=text_from_voice)
    else:
        await update.message.reply_text(
            "Omlouvám se, ale nepodařilo se mi hlasovou zprávu srozumitelně přepsat. 😔"
        )

# Reakce na zprávy
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, overridden_text=None):
    # Pokud máme přepsaný text (z hlasovky), použijeme ho, jinak klasiku ze zprávy
    user_text = overridden_text if overridden_text else update.message.text
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