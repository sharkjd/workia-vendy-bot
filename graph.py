from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Importy tvých agentů
from agents.start_faze import start_faze_node
from agents.verify_data import verify_data_node
from agents.verify_cv import verify_cv_node
from agents.change_process import change_process_node

from state import AgentState
from tools.edit_candidate_record import edit_candidate_record
from tools.sea_database import get_initial_state

# --- 1. ROZHODOVACÍ LOGIKA (ROUTERS) ---

def route_by_status(state: AgentState):
    """
    Rozcestník: Rozhodne, který agent má mluvit na základě statusu ve State.
    Protože předtím proběhl SYNC, status je vždy aktuální ze SeaTable.
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
    Výhybka: Pokud AI vygenerovala požadavek na Tool, jde se do 'tools'.
    Pokud jen odpověděla textem, končí turn (END).
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return END

# --- 2. UZLY (NODES) ---

def sync_state_node(state: AgentState):
    """
    Tvoje "Čtečka reality": Načte data ze SeaTable a přepíše State.
    """
    # Získáme ID z candidate_data (které tam vložíme v handlerech WhatsApp)
    user_id = state.get("candidate_data", {}).get("external_id")
    
    if not user_id:
        print("❌ SYNC ERROR: Chybí external_id ve state!")
        return state

    fresh_db_data = get_initial_state(user_id, channel="whatsapp")
    
    if not fresh_db_data:
        print(f"❌ SYNC ERROR: Nepodařilo se načíst data pro ID {user_id}")
        return state

    print(f"🔄 SYNC: Načten status '{fresh_db_data['status']}' pro řádek {fresh_db_data['row_id']}")

    return {
        "row_id": fresh_db_data["row_id"],
        "status": fresh_db_data["status"],
        "candidate_data": fresh_db_data["candidate_data"],
        "corrected_info": fresh_db_data["corrected_info"]
    }

# --- 3. KONFIGURACE GRAFU ---

graph_builder = StateGraph(AgentState)

# Přidání uzlů
graph_builder.add_node("sync_state", sync_state_node)
graph_builder.add_node("start_faze", start_faze_node)
graph_builder.add_node("verify_data", verify_data_node)
graph_builder.add_node("verify_cv", verify_cv_node)
graph_builder.add_node("change_process", change_process_node)

# Tool uzel
tools = [edit_candidate_record]
graph_builder.add_node("tools", ToolNode(tools))

# --- 4. DEFINICE CEST (EDGES) ---

# A. START -> Vždy nejdřív SYNC (přelízneme State daty z DB)
graph_builder.add_edge(START, "sync_state")

# B. SYNC -> Rozcestník k agentům
graph_builder.add_conditional_edges(
    "sync_state",
    route_by_status,
    {
        "start_faze": "start_faze",
        "verify_data": "verify_data",
        "verify_cv": "verify_cv",
        "change_process": "change_process"
    }
)

# C. AGENTI -> Rozhodnutí: Tool (smyčka) nebo END (Telegram)
for node_name in ["start_faze", "verify_data", "verify_cv", "change_process"]:
    graph_builder.add_conditional_edges(
        node_name,
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )

# D. TOOLS -> Návrat do SYNC (Klíčová smyčka pro plynulý přechod mezi fázemi)
# Po každém zápisu se vrátíme k "čtečce reality", která posune status a spustí dalšího agenta
graph_builder.add_edge("tools", "sync_state")

# Export pro main.py