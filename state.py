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


def add_messages_with_limit(existing: list, new: list, limit: int = 10) -> list:
    combined = add_messages(existing, new)
    
    if len(combined) <= limit:
        return combined

    # 1. Uděláme základní ořez
    trimmed = combined[-limit:]

    # 2. Gemini nesnáší, když historie začíná ToolMessage (osiřelý výsledek)
    # nebo AIMessage, která má v sobě tool_calls (osiřely příkaz).
    # Budeme zahazovat zprávy zepředu, dokud nenarazíme na HumanMessage.
    while trimmed and (trimmed[0].type == "tool" or (trimmed[0].type == "ai" and trimmed[0].tool_calls)):
        trimmed.pop(0)
        
    # 3. Poslední pojistka: Pokud jsme vyhodili všechno, vrať aspoň poslední zprávu
    if not trimmed:
        return combined[-1:]

    return trimmed
    """
    Vlastní reduktor pro zprávy s omezením počtu.
    
    Proč to potřebujeme?
    ---------------------
    Výchozí `add_messages` z LangGraphu pouze přidává zprávy donekonečna.
    To způsobuje rostoucí spotřebu tokenů (=peněz) a možné překročení 
    kontextového okna modelu.
    
    Jak to funguje?
    ---------------
    1. Zavoláme původní `add_messages` pro správné sloučení zpráv
       (LangGraph tím řeší duplicity, tool calls apod.)
    2. Ořežeme seznam na posledních `limit` zpráv
    
    Parametry:
    ----------
    existing : list - Stávající zprávy ve state
    new : list      - Nové zprávy k přidání  
    limit : int     - Maximální počet zpráv k uchování (výchozí: 10)
    """
    combined = add_messages(existing, new)
    if len(combined) > limit:
        return combined[-limit:]
    return combined

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
    # Historie zpráv - omezeno na 10 posledních (reduktor add_messages_with_limit)
    # Díky tomu agent nepřekročí kontextové okno a šetříme tokeny
    messages: Annotated[list, lambda existing, new: add_messages_with_limit(existing, new, limit=10)]
    
    # Řízení fáze (START, VERIFY_DATA, VERIFY_CV, atd.)
    status: str
    row_id: str  # <--- Sem si uložíme SeaTable ID řádku
    # Kompletní profil kandidáta načtený ze SeaTable
    candidate_data: CandidateData
    
    # Historie všech provedených oprav (používá reduktor append_info)
    # Odpovídá sloupci 'corrected_info' v SeaTable 
    corrected_info: str