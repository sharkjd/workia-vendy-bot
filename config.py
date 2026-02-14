# --- Načtení proměnných z .env a práce s prostředím ---
import os
from dotenv import load_dotenv

# Načte proměnné z .env (TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, DATABASE_URL)
load_dotenv()
# URI připojení k PostgreSQL (např. Supabase)
DB_URI = os.getenv("DATABASE_URL")
