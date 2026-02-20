import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

# Načtení proměnných z .env
load_dotenv()
DB_URI = os.getenv("DATABASE_URL")

def main():
    # ZDE DOPLŇ WhatsApp telefon nebo thread_id (identifikátor konverzace)
    THREAD_ID = "5749949374" 


    print(f"Připojuji se k databázi pro čtení ID: {THREAD_ID}...")
    
    pool = ConnectionPool(
        conninfo=DB_URI,
        max_size=5,
        kwargs={"autocommit": True, "prepare_threshold": None}
    )

    with pool:
        # Vytvoříme instanci Checkpointeru (bez nutnosti spouštět celý graf)
        checkpointer = PostgresSaver(pool)
        
        # Řekneme mu, jaké vlákno nás zajímá
        config = {"configurable": {"thread_id": THREAD_ID}}
        
        # get_tuple() vytáhne z databáze ten serializovaný balíček a rozbalí ho
        checkpoint_tuple = checkpointer.get_tuple(config)
        
        if checkpoint_tuple is None:
            print(f"❌ Pro ID {THREAD_ID} nebyla nalezena žádná historie.")
            return

        # Vytáhneme zprávy ze stavu grafu (State)
        state = checkpoint_tuple.checkpoint.get("channel_values", {})
        messages = state.get("messages", [])
        
        print("\n=== HISTORIE KONVERZACE ===")
        for msg in messages:
            # msg.type nám řekne, jestli je to 'human' (člověk) nebo 'ai' (Vendy)
            sender = "Uživatel" if msg.type == "human" else "Vendy 🤖"
            print(f"{sender}: {msg.content}")
        print("===========================\n")

if __name__ == "__main__":
    main()