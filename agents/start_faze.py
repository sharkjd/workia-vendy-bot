from langchain_core.messages import SystemMessage
from models_config import get_llm_with_tools
from agent_config import get_model_for_agent
from . import prompts

def start_faze_node(state):
    """
    Agent responsible for the initial contact phase.
    Goal: Greet the candidate and obtain consent to proceed.
    """
    row_id = state.get("row_id")

    # 1. Získání ID ze stavu
    real_row_id = state.get("row_id")
    
    # --- DEBUG SEKCE ---
    print("\n" + "="*50)
    print(f"🔍 DEBUG PROMPT INICIALIZACE")
    print(f"Vytahuji ze State row_id: {real_row_id}")
    # -------------------

    # 2. Formátování promptu
    try:
        formatted_instructions = prompts.START_PROMPT.format(
            persona=prompts.BASE_VENDY_PERSONA,
            row_id=real_row_id
        )
        # Zkontrolujeme, jestli v textu nezůstaly závorky {row_id}
        if "{row_id}" in formatted_instructions:
            print("❌ CHYBA: Prompt stále obsahuje neformátované {row_id}!")
        else:
            print("✅ Prompt úspěšně naformátován.")
    except Exception as e:
        print(f"❌ CHYBA při formátování promptu: {e}")
        formatted_instructions = prompts.START_PROMPT # Fallback

    print("="*50 + "\n")
    instructions = prompts.START_PROMPT.format(persona=prompts.BASE_VENDY_PERSONA, row_id=row_id)
    
    # Dynamicky načteme model pro tohoto agenta z konfigurace
    model_name = get_model_for_agent("start_faze")
    llm = get_llm_with_tools(model_name)
    print(f"🤖 Agent 'start_faze' používá model: {model_name}")
    
    # We pass instructions as SystemMessage to set the behavior for this turn
    response = llm.invoke([SystemMessage(content=instructions)] + state["messages"])
    if response.tool_calls:
        print(f"DEBUG: Gemini volá tool: {response.tool_calls}")
    else:
        print(f"DEBUG: Gemini nevolá tool. Odpověď: {response.content}")
    return {"messages": [response]}