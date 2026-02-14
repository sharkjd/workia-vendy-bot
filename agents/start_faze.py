from state import AgentState
from model import llm
# Uzel grafu: vezme aktuální zprávy, pošle je do LLM a vrátí odpověď jako novou zprávu
def chatbot_node(state: AgentState) -> AgentState:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}