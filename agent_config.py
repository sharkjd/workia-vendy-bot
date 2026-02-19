"""
Konfigurace modelů pro jednotlivé agenty.

Tento soubor definuje, který agent používá který LLM model.
Změnou hodnot zde můžete snadno přepínat modely pro různé části aplikace.
"""

# --- MAPOVÁNÍ AGENTŮ NA MODELY ---
# Klíč = název agenta (odpovídá názvu node v grafu)
# Hodnota = název modelu z models_config.AVAILABLE_MODELS

AGENT_MODEL_MAPPING = {
    # START_FAZE - Úvodní kontakt s kandidátem
    # Úkol: Pozdrav a získání souhlasu
    # Model: Gemini Flash (rychlý, levný, dostatečný pro jednoduchý dialog)
    "start_faze": "gemini-flash",
    
    # VERIFY_DATA - Ověření základních údajů
    # Úkol: Kontrola města, pozice, dostupnosti
    # Model: Gemini Flash (jednoduché ověřování dat)
    "verify_data": "gemini-flash",
    
    # VERIFY_CV - Analýza CV a mzdových očekávání
    # Úkol: Kontrola aktuálnosti CV, poslední pozice, mzdy
    # Model: Gemini Flash (můžete změnit na "gemini-pro" pro složitější analýzu)
    "verify_cv": "gemini-flash",
    
    # CHANGE_PROCESS - Ad-hoc změny a dotazy
    # Úkol: Umožnit kandidátovi upravit jakákoli data kdykoliv
    # Model: Gemini Flash (rychlé reakce na požadavky změn)
    "change_process": "gemini-flash",
}

# --- VÝCHOZÍ MODEL ---
# Použije se, pokud agent není explicitně definován v AGENT_MODEL_MAPPING
DEFAULT_MODEL = "gemini-flash"


# --- POMOCNÉ FUNKCE ---
def get_model_for_agent(agent_name: str) -> str:
    """
    Vrátí název modelu pro daného agenta.
    
    Args:
        agent_name (str): Název agenta (např. "start_faze")
        
    Returns:
        str: Název modelu (např. "gemini-flash")
        
    Příklad:
        model_name = get_model_for_agent("verify_cv")
        # Vrátí: "gemini-flash"
    """
    return AGENT_MODEL_MAPPING.get(agent_name, DEFAULT_MODEL)


# --- UKÁZKY BUDOUCÍCH KONFIGURACÍ ---
# Odkomentujte a upravte podle potřeby

# Příklad 1: Použití silnějšího modelu pro analýzu CV
# AGENT_MODEL_MAPPING = {
#     "start_faze": "gemini-flash",
#     "verify_data": "gemini-flash",
#     "verify_cv": "gemini-pro",        # Silnější model pro CV
#     "change_process": "gemini-flash",
# }

# Příklad 2: Použití GPT-4 pro všechny složitější úkoly
# AGENT_MODEL_MAPPING = {
#     "start_faze": "gemini-flash",
#     "verify_data": "gpt-4",
#     "verify_cv": "gpt-4",
#     "change_process": "gemini-flash",
# }

# Příklad 3: Mix různých modelů
# AGENT_MODEL_MAPPING = {
#     "start_faze": "gemini-flash",      # Rychlý úvod
#     "verify_data": "claude-3-sonnet",  # Claude pro ověřování
#     "verify_cv": "gpt-4",              # GPT-4 pro analýzu CV
#     "change_process": "gemini-flash",  # Rychlé změny
# }
