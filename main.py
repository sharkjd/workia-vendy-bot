# Hlavní vstupní bod: připojí DB, zkompiluje graf s pamětí a spustí Webhook server (WhatsApp)
import os
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
import uvicorn
import config
from graph import graph_builder
import runtime
from webhook_server import app as fastapi_app
from dotenv import load_dotenv

load_dotenv()

# Port pro webhook server (lze přepsat env proměnnou)
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))


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

    print("=" * 50)
    print("🤖 Vendy běží a má paměť!")
    print(f"🌐 Webhook server: http://0.0.0.0:{WEBHOOK_PORT}")
    print(f"   - POST /webhook/start/whatsapp - zahájení konverzace (WhatsApp šablona)")
    print(f"   - GET/POST /webhook/whatsapp - WhatsApp webhook")
    print(f"   - GET /health - healthcheck")
    print("=" * 50)

    # Blokující běh webhook serveru
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=WEBHOOK_PORT,
        log_level="info"
    )


# Spuštění main() jen při přímém volání souboru (ne při importu)
if __name__ == "__main__":
    main()
