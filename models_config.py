"""
Centrální konfigurace LLM modelů pro různé agenty.

Tento soubor definuje všechny dostupné modely, které mohou agenti používat.
Každý model má své specifické parametry (temperature, max_tokens, atd.).
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
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
    
    # GPT-4o - OpenAI model pro kvalitní odpovědi
    "gpt-4o": ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=2000,
    ),
    
    # GPT-5 mini - Vyvážený model (výkon, náklady, latence)
    "gpt-5-mini": ChatOpenAI(
        model="gpt-5-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=2000,
    ),
    
    # Vertex AI Gemini Flash - ChatGoogleGenerativeAI s project = Vertex backend
    "vertex-gemini-flash": ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("VERTEX_AI_LOCATION", "europe-west1"),
        temperature=0,
        max_tokens=1000,
    ),
    
    # Vertex AI Gemini Pro - ChatGoogleGenerativeAI s project = Vertex backend
    "vertex-gemini-pro": ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("VERTEX_AI_LOCATION", "europe-west1"),
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
