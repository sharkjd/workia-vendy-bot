# --- Stavový graf a redukce zpráv ---
from langgraph.graph import StateGraph, START, END

from state import AgentState
from model import llm

# Uzel grafu: vezme aktuální zprávy, pošle je do LLM a vrátí odpověď jako novou zprávu
def chatbot_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# Sestavení grafu: jeden uzel "chatbot", vstup → chatbot → konec
graph_builder = StateGraph(AgentState)
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
