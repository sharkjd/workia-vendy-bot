# 🤖 Konfigurace LLM Modelů pro Agenty

## Přehled změn

Aplikace nyní podporuje použití **různých LLM modelů pro různé agenty**. Každý agent může mít vlastní model optimalizovaný pro svůj úkol.

## 📁 Struktura souborů

### 1. `models_config.py` - Definice dostupných modelů

Zde jsou definovány všechny LLM modely, které může aplikace používat:

- **`AVAILABLE_MODELS`** - Slovník všech dostupných modelů
  - `gemini-flash` - Rychlý Gemini model (aktivní)
  - `gemini-pro` - Silnější Gemini model (aktivní)
  - `gpt-4`, `gpt-4-turbo` - OpenAI modely (zakomentované, připravené k použití)
  - `claude-3-opus`, `claude-3-sonnet` - Anthropic modely (zakomentované)

- **`get_llm_with_tools(model_name)`** - Tovární funkce
  - Vytvoří instanci modelu s připojenými nástroji (tools)
  - Použití: `llm = get_llm_with_tools("gemini-flash")`

### 2. `agent_config.py` - Mapování agentů na modely

Zde přiřadíte, který agent používá který model:

```python
AGENT_MODEL_MAPPING = {
    "start_faze": "gemini-flash",      # Úvodní kontakt
    "verify_data": "gemini-flash",     # Ověření dat
    "verify_cv": "gemini-flash",       # Analýza CV
    "change_process": "gemini-flash",  # Ad-hoc změny
}
```

### 3. Soubory agentů - Aktualizované pro nový systém

Všichni agenti nyní dynamicky načítají své modely:
- `agents/start_faze.py`
- `agents/verify_data.py`
- `agents/verify_cv.py`
- `agents/change_process.py`

## 🚀 Jak změnit model pro agenta?

### Příklad 1: Použít silnější model pro analýzu CV

```python
# V souboru agent_config.py změňte:
AGENT_MODEL_MAPPING = {
    "start_faze": "gemini-flash",
    "verify_data": "gemini-flash",
    "verify_cv": "gemini-pro",        # ← Změna na silnější model
    "change_process": "gemini-flash",
}
```

### Příklad 2: Přidat OpenAI GPT-4

1. **Přidejte API klíč do `.env`:**
   ```
   OPENAI_API_KEY=sk-...
   ```

2. **V `models_config.py` odkomentujte GPT-4:**
   ```python
   from langchain_openai import ChatOpenAI  # ← Odkomentovat
   
   AVAILABLE_MODELS = {
       # ... ostatní modely ...
       "gpt-4": ChatOpenAI(  # ← Odkomentovat celý blok
           model="gpt-4",
           api_key=os.getenv("OPENAI_API_KEY"),
           temperature=0,
           max_tokens=1500,
       ),
   }
   ```

3. **V `agent_config.py` přiřaďte model agentovi:**
   ```python
   AGENT_MODEL_MAPPING = {
       "verify_cv": "gpt-4",  # ← Použije GPT-4 pro analýzu CV
   }
   ```

## 📊 Aktuální konfigurace

**Všichni agenti momentálně používají:** `gemini-2.5-flash`

Tato konfigurace je optimalizovaná pro rychlost a nízké náklady. Pro složitější úkoly můžete kdykoli přepnout na silnější model.

## ⚠️ Důležité poznámky

1. **Před použitím nového providera** (OpenAI, Anthropic) nezapomeňte:
   - Nainstalovat příslušný balíček: `pip install langchain-openai` nebo `pip install langchain-anthropic`
   - Přidat API klíč do `.env`
   - Odkomentovat import a definici v `models_config.py`

2. **Náklady**: Různé modely mají různé ceny. Gemini Flash je nejlevnější, GPT-4 nejdražší.

3. **Debug výpisy**: Pro zobrazení, který agent používá který model, lze do agentů dočasně přidat `print(f"🤖 Agent 'X' používá model: {model_name}")`.

## 🎯 Doporučení podle úkolu

- **Jednoduché dialogy, ověřování** → `gemini-flash` (rychlé, levné)
- **Analýza textu, CV, složitější logika** → `gemini-pro` nebo `gpt-4`
- **Kreativní psaní, komplexní úvahy** → `claude-3-opus` nebo `gpt-4-turbo`

---

**Vytvořeno:** 2026-02-15  
**Verze aplikace:** Vendy-workia v2.0
