import os
from seatable_api import Base
from dotenv import load_dotenv

# Načtení proměnných z .env
load_dotenv()

def test_connection():
    server_url = 'https://cloud.seatable.io'
    api_token = os.getenv("SEATABLE_API_TOKEN")
    
    # ID pro testování (z tvého CSV)
    test_id = "5648432919" 

    if not api_token:
        print("❌ CHYBA: SEATABLE_API_TOKEN nenalezen v .env!")
        return

    print(f"--- 🔌 Připojuji se k SeaTable ---")
    try:
        base = Base(api_token, server_url)
        base.auth()

        # Query na tabulku 'Kandidáti'
        query = f"select * from Kandidáti where external_id = '{test_id}'"
        rows = base.query(query)

        if rows:
            row = rows[0]
            print(f"✅ ÚSPĚCH! Kompletní data pro: {row.get('full_name')}")
            print("=" * 40)
            
            # Výpis všech sloupců podle tvé struktury
            print(f"🆔 External ID:        {row.get('external_id')}")
            print(f"📅 Poslední interakce: {row.get('last_interaction')}")
            print(f"👤 Celé jméno:         {row.get('full_name')}")
            print(f"📧 Email:              {row.get('email')}")
            print(f"📍 Město (Web):        {row.get('web_city')}")
            print(f"💼 Pozice (Web):       {row.get('web_position')}")
            print(f"⏱️ Dostupnost (Web):   {row.get('web_availability')}")
            print(f"🚦 Status:             {row.get('status')}")
            print(f"📝 Opravy (History):   {row.get('corrected_info')}")
            print(f"📄 CV obsahuje práci:  {row.get('cv_contains_last_job')}")
            print(f"🏭 Poslední práce:     {row.get('last_position_detail')}")
            print(f"💰 Poslední plat:      {row.get('last_salary')}")
            print(f"🎯 Očekávaný plat:     {row.get('expected_salary')}")
            print(f"🤖 Shrnutí chatu:      {row.get('chat_summary')}")
            
            print("=" * 40)
            return row
        else:
            print(f"❌ Kandidát s ID {test_id} nebyl v tabulce nalezen.")
            return None
            
    except Exception as e:
        print(f"❌ Nastala chyba: {e}")

if __name__ == "__main__":
    test_connection()