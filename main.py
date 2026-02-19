# Hlavní vstupní bod: připojí DB, zkompiluje graf s pamětí a spustí Telegram bota + Webhook server
import os
import asyncio
import threading
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import uvicorn
import config
from graph import graph_builder
import runtime
from telegram_handlers import start, handle_message, handle_voice
from webhook_server import app as fastapi_app
from dotenv import load_dotenv

load_dotenv()

# Port pro webhook server (lze přepsat env proměnnou)
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))


def run_webhook_server():
    """
    Spustí FastAPI webhook server v samostatném vlákně.
    Uvicorn běží s vlastním event loop.
    """
    print(f"🌐 Spouštím Webhook server na portu {WEBHOOK_PORT}...")
    uvicorn.run(
        fastapi_app, 
        host="0.0.0.0", 
        port=WEBHOOK_PORT, 
        log_level="info"
    )


def main():
    print("Připojuji se k Supabase...")
    # Otevřeme "bazén" připojení k databázi (max 20 spojení, autocommit pro checkpointer)
    pool = ConnectionPool(
        conninfo=config.DB_URI,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": None}
    )

    # PostgresSaver ukládá stav konverzací do PostgreSQL, takže každý uživatel má vlastní historii
    checkpointer = PostgresSaver(pool)
    graph = graph_builder.compile(checkpointer=checkpointer)

    runtime.pool = pool
    runtime.graph = graph

    # Spustíme webhook server v samostatném vlákně (daemon=True zajistí ukončení při konci hlavního programu)
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()

    # Vytvoření Telegram aplikace s tokenem z .env
    telegram_app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Registrace handlerů: /start volá start(), ostatní textové zprávy volají handle_message()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    print("=" * 50)
    print("🤖 Vendy běží a má paměť!")
    print(f"📱 Telegram bot: aktivní (long polling)")
    print(f"🌐 Webhook server: http://0.0.0.0:{WEBHOOK_PORT}")
    print(f"   - POST /webhook/start - zahájení konverzace (Telegram)")
    print(f"   - POST /webhook/start/whatsapp - zahájení konverzace (WhatsApp šablona)")
    print(f"   - GET/POST /webhook/whatsapp - WhatsApp webhook")
    print(f"   - GET /health - healthcheck")
    print("=" * 50)
    
    # Blokující běh bota – čeká na nové zprávy (long polling)
    telegram_app.run_polling()


# Spuštění main() jen při přímém volání souboru (ne při importu)
if __name__ == "__main__":
    main()
