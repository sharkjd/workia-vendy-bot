# --- LLM od Google (Gemini) ---
import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace modelu Gemini; používá se pro generování odpovědí
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
    max_tokens=1000,
)
