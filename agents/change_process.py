from langchain_core.messages import SystemMessage
from model import llm_with_tools
from . import prompts

def change_process_node(state):
    """
    Agent responsible for on-demand changes and database queries.
    Goal: Allow the candidate to modify any part of their profile.
    """
    candidate = state["candidate_data"]
    
    # Full context of the candidate's database row
    candidate_context = "\n".join([f"{k}: {v}" for k, v in candidate.items()])
    
    instructions = (
        prompts.CHANGE_PROCESS_PROMPT.format(
            persona=prompts.BASE_VENDY_PERSONA,
            email=candidate.get('email', 'unknown')
        ) + 
        f"\n\n### CURRENT DATABASE RECORD:\n{candidate_context}"
    )
    
    response = llm_with_tools.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}