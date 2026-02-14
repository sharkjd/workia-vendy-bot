from langchain_core.messages import SystemMessage
from model import llm_with_tools
from . import prompts

def verify_cv_node(state):
    """
    Agent responsible for Phase B & C: CV verification and Salary expectations.
    Goal: Check if the CV is current and prepare a final summary.
    """
    candidate = state.get("candidate_data", {})
    row_id = state.get("row_id") # Nezapomeň, že row_id je v kořeni state, ne v candidate_data

    # Všechna tato pole musí odpovídat proměnným, které máš v prompts.VERIFY_CV_PROMPT
    instructions = prompts.VERIFY_CV_PROMPT.format(
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
    
    response = llm_with_tools.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}