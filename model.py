# --- LLM od Google (Gemini) ---
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.edit_candidate_record import edit_candidate_record  # Importujeme tvůj tool

# Inicializace základního modelu
# Přepnuto na gemini-1.5-flash pro vyšší limity a stabilitu toolů
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,  # Pro agenty s tooly je lepší nižší teplota (přesnost)
    max_tokens=1000,
)

# Definice seznamu nástrojů, které má Vendy k dispozici
tools = [edit_candidate_record]

# NOVÉ: Vytvoření instance modelu, která má o toolech povědomí
# Tento objekt budeš importovat do svých agentů (nodes)
llm_with_tools = llm.bind_tools(tools)