from langchain_core.messages import SystemMessage
from models_config import get_llm_with_tools
from agent_config import get_model_for_agent
from . import prompts

def start_faze_node(state):
    """
    Agent responsible for the initial contact phase.
    Goal: Greet the candidate and obtain consent to proceed.
    """
    row_id = state.get("row_id")
    instructions = prompts.START_PROMPT.format(
        persona=prompts.BASE_VENDY_PERSONA,
        row_id=row_id
    )

    model_name = get_model_for_agent("start_faze")
    llm = get_llm_with_tools(model_name)
    response = llm.invoke([SystemMessage(content=instructions)] + state["messages"])
    return {"messages": [response]}