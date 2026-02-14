# agents/verify_data.py
from langchain_core.messages import SystemMessage
from model import llm_with_tools
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

    response = llm_with_tools.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}