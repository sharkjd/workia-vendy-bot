# Hlavní vstupní bod: připojí DB, zkompiluje graf s pamětí a spustí Telegram bota
import os
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import MessageHandler, filters
import config
from graph import graph_builder
import runtime
from telegram_handlers import start, handle_message
from dotenv import load_dotenv
from telegram_handlers import start, handle_message, handle_voice

load_dotenv()

def main():
    print("Připojuji se k Supabase...")
    # Otevřeme "bazén" připojení k databázi (max 20 spojení, autocommit pro checkpointer)
    pool = ConnectionPool(
        conninfo=config.DB_URI,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": None}
    )

    # NOVÉ: Předáme připojení Checkpointeru a ten následně do grafu
    # PostgresSaver ukládá stav konverzací do PostgreSQL, takže každý uživatel má vlastní historii
    checkpointer = PostgresSaver(pool)
    graph = graph_builder.compile(checkpointer=checkpointer)

    runtime.pool = pool
    runtime.graph = graph

    # Vytvoření Telegram aplikace s tokenem z .env
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Registrace handlerů: /start volá start(), ostatní textové zprávy volají handle_message()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice)) # <--- TENTO ŘÁDEK
    print("Vendy běží a má paměť! Zkus si s ní povídat na Telegramu.")
    
    # Blokující běh bota – čeká na nové zprávy (long polling)
    app.run_polling()


# Spuštění main() jen při přímém volání souboru (ne při importu)
if __name__ == "__main__":
    main()
