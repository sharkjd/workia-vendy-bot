from langchain_core.messages import SystemMessage
from model import llm
from . import prompts

def verify_cv_node(state):
    """
    Agent responsible for Phase B & C: CV verification and Salary expectations.
    Goal: Check if the CV is current and prepare a final summary.
    """
    candidate = state["candidate_data"]
    
    # Formatting the candidate profile for the agent's summary task
    full_summary = (
        f"- Name: {candidate.get('full_name', 'N/A')}\n"
        f"- Email: {candidate.get('email', 'N/A')}\n"
        f"- Location: {candidate.get('web_city', 'N/A')}\n"
        f"- Availability: {candidate.get('web_availability', 'N/A')}\n"
        f"- Position: {candidate.get('web_position', 'N/A')}\n"
        f"- Last job: {candidate.get('last_position_detail', 'N/A')}\n"
        f"- Last salary: {candidate.get('last_salary', 'N/A')}\n"
        f"- Expected salary: {candidate.get('expected_salary', 'N/A')}"
    )

    instructions = (
        prompts.VERIFY_CV_PROMPT.format(persona=prompts.BASE_VENDY_PERSONA) + 
        f"\n\n### CANDIDATE DATA FOR SUMMARY:\n{full_summary}"
    )
    
    response = llm.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}