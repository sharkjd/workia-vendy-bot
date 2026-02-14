from typing import Annotated, NotRequired, TypedDict, Optional, Union
from langgraph.graph.message import add_messages

# 1. REDUKTOR: Funkce pro nabalování změn do historie (corrected_info)
# Tato funkce zajistí, že se nové úpravy připisují na konec a staré se nemažou.
def append_info(old_text: Optional[str], new_text: Optional[str]) -> str:
    if not old_text:
        return new_text or ""
    if not new_text:
        return old_text
    return f"{old_text}\n{new_text}"

# 2. STRUKTURA KANDIDÁTA: Přesné mapování sloupců ze SeaTable
class CandidateData(TypedDict):
    external_id: str           # Telegram ID (sloupec 'external_id')
    full_name: str             # Jméno kandidáta ('full_name')
    email: NotRequired[str]                 # Email ('email')
    web_city: NotRequired[str]              # Město ('web_city')
    web_position: NotRequired[str]          # Hledaná pozice ('web_position')
    web_availability: NotRequired[str]      # Kdy může nastoupit ('web_availability')
    cv_contains_last_job: NotRequired[Optional[bool]]  # Info o CV ('cv_contains_last_job')
    last_position_detail: NotRequired[str]  # Poslední práce ('last_position_detail')
    last_salary: NotRequired[Optional[Union[int, str]]]     # Poslední mzda ('last_salary')
    expected_salary: NotRequired[Optional[Union[int, str]]] # Očekávaná mzda ('expected_salary')
    chat_summary: NotRequired[str]          # Finální shrnutí pro HR ('chat_summary') 

# 3. HLAVNÍ STAV GRAFU (AgentState)
class AgentState(TypedDict):
    # Historie zpráv (automaticky spravováno LangGraphem)
    messages: Annotated[list, add_messages]
    
    # Řízení fáze (START, VERIFY_DATA, VERIFY_CV, atd.)
    status: str
    row_id: str  # <--- Sem si uložíme SeaTable ID řádku
    # Kompletní profil kandidáta načtený ze SeaTable
    candidate_data: CandidateData
    
    # Historie všech provedených oprav (používá reduktor append_info)
    # Odpovídá sloupci 'corrected_info' v SeaTable 
    corrected_info: str