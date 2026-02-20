import os
from seatable_api import Base
from dotenv import load_dotenv

load_dotenv()

def get_initial_state(identifier: str, channel: str = "whatsapp"):
    """
    Načte počáteční stav kandidáta ze SeaTable.
    identifier: whatsapp_phone (telefonní číslo) nebo external_id
    channel: "whatsapp" – určuje, který sloupec použít pro lookup
    """
    server_url = 'https://cloud.seatable.io'
    api_token = os.getenv("SEATABLE_API_TOKEN")

    base = Base(api_token, server_url)
    base.auth()

    # Pro Telegram: external_id (chat_id), pro WhatsApp: external_id (telefon) nebo whatsapp_phone
    if channel == "whatsapp":
        query = f"select * from Kandidáti where external_id = '{identifier}'"
        rows = base.query(query)
        if not rows:
            # Fallback na sloupec whatsapp_phone, pokud existuje
            query = f"select * from Kandidáti where whatsapp_phone = '{identifier}'"
            rows = base.query(query)
    else:
        query = f"select * from Kandidáti where external_id = '{identifier}'"
        rows = base.query(query)

    if not rows:
        return None

    row = rows[0]
    
    # Sestavíme strukturu přesně pro náš AgentState
    return {
        "row_id": row.get('_id'), # <--- Tady ho získáme
        "status": row.get('status', 'START'),
        "corrected_info": row.get('corrected_info', ''),
        "candidate_data": {
            'external_id': str(row.get('external_id', '')),
            'full_name': row.get('full_name', ''),
            'email': row.get('email', ''),
            'web_city': row.get('web_city', ''),
            'web_position': row.get('web_position', ''),
            'web_availability': row.get('web_availability', ''),
            'cv_contains_last_job': row.get('cv_contains_last_job'),
            'last_position_detail': row.get('last_position_detail', ''),
            'last_salary': row.get('last_salary'),
            'expected_salary': row.get('expected_salary'),
            'chat_summary': row.get('chat_summary', '')
        }
    }