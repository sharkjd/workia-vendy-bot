import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# Načtení proměnných z .env
load_dotenv()

# Získání URL databáze
DB_URI = os.getenv("DATABASE_URL")

def main():
    print("Zahajuji test připojení k Postgres (Supabase)...")
    
    if not DB_URI:
        print("CHYBA: Nenalezeno DATABASE_URL v .env souboru!")
        return

    try:
        # Vytvoření "bazénu" připojení (Connection Pool)
        with ConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs={"autocommit": True, "prepare_threshold": 0} 
            # prepare_threshold=0 je důležité pro Supabase Transaction Pooler (PgBouncer)
        ) as pool:
            
            # Inicializace LangGraph Checkpointeru
            checkpointer = PostgresSaver(pool)
            
            print("Připojeno! Pokouším se vytvořit potřebné tabulky...")
            # Příkaz setup() zkontroluje databázi a vytvoří tabulky, pokud chybí
            checkpointer.setup()
            
            print("🎉 ÚSPĚCH! Databáze je perfektně propojená a tabulky jsou připravené.")
            
    except Exception as e:
        print(f"❌ NĚCO SE POKAŽILO:\n{e}")

if __name__ == "__main__":
    main()