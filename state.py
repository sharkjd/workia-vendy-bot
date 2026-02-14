# --- Typy a stav pro LangGraph ---
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

# Stav grafu: seznam zpráv, které se při přidání slučují přes add_messages (historie chatu)
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
