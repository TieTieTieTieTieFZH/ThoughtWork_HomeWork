from langgraph.graph import StateGraph, END
from src.agent.state import AgentState, JobModel
from src.agent.nodes import plan_search, search_jobs, scrape_and_parse
from loguru import logger


def should_continue(state: AgentState):
    logger.info(f"第{state.get('iteration_count', 0)}轮思考已结束")
    if len(state.get("collected_jobs", [])) >= state.get("target_count", 50):
        return END
    if state.get("iteration_count", 0) >= 5:  # Safety fallback
        return END
    return "plan_search"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("plan_search", plan_search)
    workflow.add_node("search_jobs", search_jobs)
    workflow.add_node("scrape_and_parse", scrape_and_parse)

    # Simplified node setup - scrape_and_parse now handles collection
    workflow.set_entry_point("plan_search")
    workflow.add_edge("plan_search", "search_jobs")
    workflow.add_edge("search_jobs", "scrape_and_parse")

    workflow.add_conditional_edges("scrape_and_parse", should_continue)

    return workflow.compile()
