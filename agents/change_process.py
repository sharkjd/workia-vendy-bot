from langchain_core.messages import SystemMessage
from model import llm_with_tools
from . import prompts

def change_process_node(state):
    """
    Agent zodpovědný za ad-hoc změny a dotazy na data.
    Cíl: Umožnit kandidátovi upravit jakoukoli část profilu kdykoliv.
    """
    candidate = state.get("candidate_data", {})
    row_id = state.get("row_id")
    
    # 1. Naplníme prompt všemi proměnnými, aby Vendy mohla o datech i mluvit
    # Musíme pokrýt vše, co jsme si definovali v CHANGE_PROCESS_PROMPT
    instructions = prompts.CHANGE_PROCESS_PROMPT.format(
        persona=prompts.BASE_VENDY_PERSONA,
        row_id=row_id,
        full_name=candidate.get("full_name", "N/A"),
        email=candidate.get("email", "N/A"),
        web_city=candidate.get("web_city", "N/A"),
        web_position=candidate.get("web_position", "N/A"),
        web_availability=candidate.get("web_availability", "N/A"),
        last_position_detail=candidate.get("last_position_detail", "N/A"),
        last_salary=candidate.get("last_salary", "N/A"),
        expected_salary=candidate.get("expected_salary", "N/A")
    )
    
    # 2. Ošetření historie zpráv (Guardrail proti 400 INVALID_ARGUMENT)
    # Vezmeme posledních 10 zpráv a zajistíme, že začínáme zprávou od člověka
    messages = state["messages"]
    recent_messages = messages[-10:]
    
    while recent_messages and recent_messages[0].type not in ["human", "system"]:
        recent_messages.pop(0)
        
    # Pokud by po vyčištění nic nezbylo, vezmeme aspoň úplně poslední zprávu
    if not recent_messages:
        recent_messages = messages[-1:]

    # 3. Volání modelu
    response = llm_with_tools.invoke([SystemMessage(content=instructions)] + recent_messages)
    
    return {"messages": [response]}