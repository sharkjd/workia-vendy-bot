# --- Načtení proměnných z .env a práce s prostředím ---
import os
from dotenv import load_dotenv

# Načte proměnné z .env
load_dotenv()

# PostgreSQL (např. Supabase)
DB_URI = os.getenv("DATABASE_URL")

# WhatsApp Cloud API (Meta)
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME", "hello_world")
WHATSAPP_TEMPLATE_LANG = os.getenv("WHATSAPP_TEMPLATE_LANG", "cs")
