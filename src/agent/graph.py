from langgraph.graph import StateGraph, END
from src.agent.state import AgentState, JobModel
from src.agent.nodes import plan_search, search_jobs, scrape_and_parse


def should_continue(state: AgentState):
    if len(state.get("collected_jobs", [])) >= state.get("target_count", 50):
        return END
    if state.get("iteration_count", 0) >= 10:  # Safety fallback
        return END
    return "plan_search"


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("plan_search", plan_search)
    workflow.add_node("search_jobs", search_jobs)
    workflow.add_node("scrape_and_parse", scrape_and_parse)

    # Mock evaluate step by just appending directly for MVP flow test
    def evaluate(state):
        job = JobModel(
            title="Mock AI Job",
            company="MockCorp",
            location="Remote",
            salary="200/day",
            tech_tags=["LLM"],
            requirements="Python",
            source="MockSite",
            job_url=list(state.get("visited_urls", set()))[-1],
        )
        return {"collected_jobs": state.get("collected_jobs", []) + [job]}

    workflow.add_node("evaluate", evaluate)

    workflow.set_entry_point("plan_search")
    workflow.add_edge("plan_search", "search_jobs")
    workflow.add_edge("search_jobs", "scrape_and_parse")
    workflow.add_edge("scrape_and_parse", "evaluate")

    workflow.add_conditional_edges("evaluate", should_continue)

    return workflow.compile()
