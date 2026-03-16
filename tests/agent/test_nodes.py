from src.agent.state import AgentState, JobModel
from src.agent.nodes import plan_search, search_jobs, scrape_and_parse


def test_plan_search():
    state: AgentState = {
        "iteration_count": 0,
        "search_queries": [],
        "current_site_index": 0,
    }
    new_state = plan_search(state)
    assert new_state["iteration_count"] == 1
    assert len(new_state["search_queries"]) == 1


def test_search_jobs():
    state = {"search_queries": ["test query"], "visited_urls": set()}
    new_state = search_jobs(state)
    assert any("mock_url" in url for url in new_state["visited_urls"])


def test_scrape_and_parse():
    state = {"visited_urls": {"mock_url_1"}}
    # scrape_and_parse now returns a dict for LangGraph state update
    res = scrape_and_parse(state)
    assert "visited_urls" in res
