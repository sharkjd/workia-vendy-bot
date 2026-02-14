# --- Stavový graf a redukce zpráv ---
from langgraph.graph import StateGraph, START, END
from agents.start_faze import chatbot_node

from state import AgentState
from model import llm



# Sestavení grafu: jeden uzel "chatbot", vstup → chatbot → konec
graph_builder = StateGraph(AgentState)
graph_builder.add_node("chatbot", chatbot_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
