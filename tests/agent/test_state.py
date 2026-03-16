from src.agent.state import JobModel, AgentState


def test_job_model():
    job = JobModel(
        title="AI Engineer",
        company="TechCorp",
        location="Beijing",
        salary="20k-30k",
        tech_tags=["LLM", "NLP"],
        requirements="Python, PyTorch",
        source="Boss",
        job_url="http://example.com",
    )
    assert job.title == "AI Engineer"


def test_agent_state():
    state = AgentState(
        target_count=50,
        collected_jobs=[],
        visited_urls=set(),
        search_queries=[],
        current_site_index=0,
        iteration_count=0,
    )
    assert state["target_count"] == 50
