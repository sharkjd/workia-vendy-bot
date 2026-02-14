import os
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

# Načtení proměnných z .env
load_dotenv()
DB_URI = os.getenv("DATABASE_URL")

def main():
    print("\n=== 🧹 NÁSTROJ PRO MAZÁNÍ PAMĚTI VENDY ===")
    print("1. Smazat historii pro JEDNOHO konkrétního uživatele (Telegram ID)")
    print("2. Smazat ÚPLNĚ VŠECHNO (kompletní reset databáze)")
    
    volba = input("\nVyber možnost (zadej 1 nebo 2): ")

    if volba not in ["1", "2"]:
        print("Neplatná volba. Končím.")
        return

    print("Připojuji se k databázi...")
    # Připojíme se k databázi (stejně jako u čtení, prepare_threshold=None je důležité)
    pool = ConnectionPool(
        conninfo=DB_URI,
        max_size=5,
        kwargs={"autocommit": True, "prepare_threshold": None}
    )

    try:
        # Získáme konkrétní připojení pro vykonání SQL příkazů
        with pool.connection() as conn:
            if volba == "1":
                thread_id = input("Zadej Telegram ID ke smazání: ")
                # LangGraph ukládá data primárně do těchto tří tabulek, smažeme je všude
                conn.execute("DELETE FROM checkpoints WHERE thread_id = %s", (thread_id,))
                conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id = %s", (thread_id,))
                conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = %s", (thread_id,))
                print(f"✅ Historie pro uživatele {thread_id} byla úspěšně smazána!")
            
            elif volba == "2":
                potvrzeni = input("⚠️ OPRAVDU chceš smazat úplně celou paměť všech uživatelů? (napiš 'ano'): ")
                if potvrzeni.lower() == "ano":
                    # Příkaz TRUNCATE bleskově vyprázdní celé tabulky
                    conn.execute("TRUNCATE TABLE checkpoints, checkpoint_blobs, checkpoint_writes;")
                    print("✅ DATABÁZE BYLA KOMPLETNĚ VYMAZÁNA. Vendy má teď čistý štít.")
                else:
                    print("Mazání zrušeno.")
    except Exception as e:
         print(f"❌ Nastala chyba při mazání: {e}")

if __name__ == "__main__":
    main()