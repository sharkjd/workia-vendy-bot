import os
from seatable_api import Base
from langchain_core.tools import tool
from dotenv import load_dotenv

# Načteme proměnné prostředí (API token)
load_dotenv()

def get_seatable_base():
    """
    Pomocná funkce pro vytvoření a autentizaci připojení k SeaTable.
    """
    server_url = 'https://cloud.seatable.io'
    api_token = os.getenv("SEATABLE_API_TOKEN")
    
    if not api_token:
        raise ValueError("SEATABLE_API_TOKEN není nastaven v .env souboru")
        
    base = Base(api_token, server_url)
    base.auth()
    return base

@tool
def edit_candidate_record(row_id: str, updates: dict):
    """
    Updates the candidate's record in SeaTable. 
    'updates' is a dictionary where keys are column names and values are new data.
    
    Allowed columns for 'updates' dictionary:
    - 'status': Use to change phase ('VERIFY_DATA', 'VERIFY_CV', 'COMPLETED').
    - 'web_city', 'web_position', 'web_availability': Use for data corrections.
    - 'last_position_detail', 'last_salary', 'expected_salary': Use for professional details.
    - 'chat_summary': Use to save the final conversation summary.
    
    Example input: row_id="xxx", updates={"status": "VERIFY_DATA", "web_city": "Praha"}
    """
    try:
        base = get_seatable_base()
        # Název tabulky musí přesně odpovídat tvému SeaTable (předpokládám 'Kandidáti')
        base.update_row('Kandidáti', row_id, updates)
        return f"Successfully updated fields: {list(updates.keys())} for row {row_id}"
    except Exception as e:
        return f"Error updating SeaTable: {str(e)}"