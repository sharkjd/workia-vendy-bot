from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Importy tvých agentů ze samostatných souborů
from agents.start_faze import start_faze_node
from agents.verify_data import verify_data_node
from agents.verify_cv import verify_cv_node
from agents.change_process import change_process_node

from state import AgentState
from model import llm_with_tools
from tools.edit_candidate_record import edit_candidate_record

# --- 1. ROZHODOVACÍ LOGIKA (ROUTERS) ---

def route_by_status(state: AgentState):
    """
    Vstupní brána a rozcestník po akci nástroje. 
    Rozhodne, který agent má dostat slovo podle stavu v DB.
    """
    status = state.get("status", "START")
    
    if status == "START":
        return "start_faze"
    elif status == "VERIFY_DATA":
        return "verify_data"
    elif status == "VERIFY_CV":
        return "verify_cv"
    elif status == "CHANGE_PROCESS" or status == "COMPLETED":
        return "change_process"
    
    return "start_faze"

def should_continue(state: AgentState):
    """
    Hlídka na výstupu z každého agenta.
    Zjišťuje, zda model vygeneroval požadavek na nástroj (tool_calls).
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Kontrola, zda AI chce volat nástroj
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Pokud ne, turn končí a čekáme na vstup uživatele z Telegramu
    return END

# --- 2. KONFIGURACE UZLŮ ---

graph_builder = StateGraph(AgentState)

# Definice nástrojů a vytvoření ToolNode (uzel pro vykonání kódu nástrojů)
tools = [edit_candidate_record]
tool_node = ToolNode(tools)

# Přidání uzlů do grafu
graph_builder.add_node("start_faze", start_faze_node)
graph_builder.add_node("verify_data", verify_data_node)
graph_builder.add_node("verify_cv", verify_cv_node)
graph_builder.add_node("change_process", change_process_node)
graph_builder.add_node("tools", tool_node)

# --- 3. DEFINICE CEST (EDGES) ---

# A. START -> První rozhodnutí kam jít
graph_builder.add_conditional_edges(
    START,
    route_by_status,
    {
        "start_faze": "start_faze",
        "verify_data": "verify_data",
        "verify_cv": "verify_cv",
        "change_process": "change_process"
    }
)

# B. AGENTI -> Rozhodnutí zda volat Tool nebo končit (END)
# Propojíme všechny agenty se stejnou logikou výhybky
for node_name in ["start_faze", "verify_data", "verify_cv", "change_process"]:
    graph_builder.add_conditional_edges(
        node_name,
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

# C. TOOLS -> LOOPBACK (Návrat na rozcestník)
# Zde byla chyba START - nyní se vracíme k rozhodovací funkci route_by_status
graph_builder.add_conditional_edges(
    "tools",
    route_by_status,
    {
        "start_faze": "start_faze",
        "verify_data": "verify_data",
        "verify_cv": "verify_cv",
        "change_process": "change_process"
    }
)

# --- 4. KOMPILACE ---
# graph = graph_builder.compile(checkpointer=checkpointer) # kompiluješ v main.py