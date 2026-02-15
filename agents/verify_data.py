# agents/verify_data.py
from langchain_core.messages import SystemMessage
from models_config import get_llm_with_tools
from agent_config import get_model_for_agent
from . import prompts


def verify_data_node(state):
    """Agent pro fázi VERIFY_DATA: ověření údajů kandidáta (město, pozice, dostupnost)."""
    candidate = state.get("candidate_data", {})
    row_id = state.get("row_id")

    instructions = prompts.VERIFY_DATA_PROMPT.format(
        persona=prompts.BASE_VENDY_PERSONA,
        row_id=row_id,
        web_city=candidate.get("web_city", "N/A"),
        web_position=candidate.get("web_position", "N/A"),
        web_availability=candidate.get("web_availability", "N/A"),
    )

    # Dynamicky načteme model pro tohoto agenta z konfigurace
    model_name = get_model_for_agent("verify_data")
    llm = get_llm_with_tools(model_name)
    print(f"🤖 Agent 'verify_data' používá model: {model_name}")

    response = llm.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}