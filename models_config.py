"""
Centrální konfigurace LLM modelů pro různé agenty.

Tento soubor definuje všechny dostupné modely, které mohou agenti používat.
Každý model má své specifické parametry (temperature, max_tokens, atd.).
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI  # Odkomentovat, pokud budete chtít používat OpenAI
# from langchain_anthropic import ChatAnthropic  # Odkomentovat pro Claude

from tools.edit_candidate_record import edit_candidate_record

# --- DOSTUPNÉ MODELY ---
# Zde definujeme všechny modely, které může aplikace používat

AVAILABLE_MODELS = {
    # Gemini Flash - Rychlý a levný model, ideální pro jednoduché úkoly
    "gemini-flash": ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,  # Deterministické odpovědi
        max_tokens=1000,
    ),
    
    # Gemini Pro - Silnější model pro složitější úkoly
    "gemini-pro": ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
        max_tokens=2000,
    ),
    
    # --- BUDOUCÍ MODELY (zakomentované) ---
    # Odkomentujte a přidejte API klíč do .env, až budete chtít použít
    
    # "gpt-4": ChatOpenAI(
    #     model="gpt-4",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     temperature=0,
    #     max_tokens=1500,
    # ),
    
    # "gpt-4-turbo": ChatOpenAI(
    #     model="gpt-4-turbo-preview",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     temperature=0,
    #     max_tokens=2000,
    # ),
    
    # "claude-3-opus": ChatAnthropic(
    #     model="claude-3-opus-20240229",
    #     api_key=os.getenv("ANTHROPIC_API_KEY"),
    #     temperature=0,
    #     max_tokens=2000,
    # ),
    
    # "claude-3-sonnet": ChatAnthropic(
    #     model="claude-3-sonnet-20240229",
    #     api_key=os.getenv("ANTHROPIC_API_KEY"),
    #     temperature=0,
    #     max_tokens=1500,
    # ),
}


# --- TOVÁRNÍ FUNKCE ---
def get_llm_with_tools(model_name: str):
    """
    Vytvoří a vrátí LLM model s připojenými nástroji (tools).
    
    Args:
        model_name (str): Název modelu z AVAILABLE_MODELS (např. "gemini-flash")
        
    Returns:
        ChatModel: LLM model s bind_tools, připravený k použití
        
    Raises:
        ValueError: Pokud model_name neexistuje v AVAILABLE_MODELS
        
    Příklad použití:
        llm = get_llm_with_tools("gemini-flash")
        response = llm.invoke(messages)
    """
    if model_name not in AVAILABLE_MODELS:
        available = ", ".join(AVAILABLE_MODELS.keys())
        raise ValueError(
            f"❌ Model '{model_name}' není definován v AVAILABLE_MODELS.\n"
            f"Dostupné modely: {available}"
        )
    
    llm = AVAILABLE_MODELS[model_name]
    
    # Připojíme nástroje, které jsou k dispozici všem agentům
    tools = [edit_candidate_record]
    
    return llm.bind_tools(tools)


# --- POMOCNÉ FUNKCE ---
def list_available_models() -> list[str]:
    """Vrátí seznam názvů všech dostupných modelů."""
    return list(AVAILABLE_MODELS.keys())


def get_model_info(model_name: str) -> dict:
    """
    Vrátí informace o konkrétním modelu.
    
    Args:
        model_name: Název modelu
        
    Returns:
        dict: Slovník s informacemi o modelu
    """
    if model_name not in AVAILABLE_MODELS:
        return {"error": f"Model {model_name} neexistuje"}
    
    model = AVAILABLE_MODELS[model_name]
    return {
        "name": model_name,
        "model": getattr(model, "model_name", "N/A"),
        "temperature": getattr(model, "temperature", "N/A"),
        "max_tokens": getattr(model, "max_tokens", "N/A"),
    }
