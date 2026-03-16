from src.agent.state import AgentState, JobModel
from src.agent.tools import unified_search_tool


def plan_search(state: AgentState) -> dict:
    queries = ["AI Engineer 校园招聘", "大模型算法实习生", "NLP 算法工程师 校招"]
    idx = state.get("iteration_count", 0) % len(queries)
    new_query = queries[idx]

    return {
        "iteration_count": state.get("iteration_count", 0) + 1,
        "search_queries": state.get("search_queries", []) + [new_query],
    }


def search_jobs(state: AgentState) -> dict:
    query = state.get("search_queries", ["AI Engineer"])[-1]
    results = unified_search_tool(query)
    new_urls = {res["url"] for res in results}
    return {"visited_urls": state.get("visited_urls", set()).union(new_urls)}


def scrape_and_parse(state: AgentState) -> dict:
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
    # The state update for collected_jobs happens in the evaluate node in our graph
    # but scrape_and_parse itself should return something that can be used or just update its part.
    # In LangGraph, node returns update the state keys.
    return {
        "visited_urls": state.get("visited_urls")
    }  # Just passing through for now as it's a mock
