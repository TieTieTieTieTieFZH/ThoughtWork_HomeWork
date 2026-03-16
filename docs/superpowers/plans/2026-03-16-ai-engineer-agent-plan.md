# AI Engineer Job Search Agent Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangGraph-based autonomous agent capable of searching, scraping, and semantically evaluating AI Engineer campus recruitment jobs until 50 valid jobs are collected.

**Architecture:** State machine graph using LangGraph. Nodes for Planning (queries), Searching (getting URLs), Scraping (extracting text), and Evaluating (LLM semantic check). Loop control via conditional edges.

**Tech Stack:** Python 3.10+, `langgraph`, `langchain-openai`, `pydantic`, `pytest` for testing.

---

## Chunk 1: Foundation & State

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write a basic import test**
```python
# tests/test_imports.py
def test_imports():
    import langgraph
    import langchain_openai
    import pydantic
    assert True
```

- [ ] **Step 2: Run test to verify it fails (missing packages)**
Run: `pytest tests/test_imports.py`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Create requirements.txt and install**
```text
# requirements.txt
langgraph
langchain-openai
pydantic
pytest
python-dotenv
```
Run: `pip install -r requirements.txt`

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_imports.py`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git add requirements.txt tests/test_imports.py && git commit -m "chore: setup project dependencies"`

### Task 2: Define Agent State and Data Models

**Files:**
- Create: `src/agent/state.py`
- Create: `tests/agent/test_state.py`

- [ ] **Step 1: Write test for State and JobModel**
```python
# tests/agent/test_state.py
from src.agent.state import JobModel, AgentState

def test_job_model():
    job = JobModel(
        title="AI Engineer", company="TechCorp", location="Beijing",
        salary="20k-30k", tech_tags=["LLM", "NLP"], requirements="Python, PyTorch",
        source="Boss", job_url="http://example.com"
    )
    assert job.title == "AI Engineer"

def test_agent_state():
    state = AgentState(
        target_count=50, collected_jobs=[], visited_urls=set(),
        search_queries=[], current_site_index=0, iteration_count=0
    )
    assert state["target_count"] == 50
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/agent/test_state.py`
Expected: FAIL (ModuleNotFoundError for src.agent.state)

- [ ] **Step 3: Implement State Models**
```python
# src/agent/state.py
from typing import TypedDict, Annotated
from pydantic import BaseModel, Field

class JobModel(BaseModel):
    title: str
    company: str
    location: str
    salary: str
    tech_tags: list[str]
    requirements: str
    source: str
    job_url: str

class AgentState(TypedDict):
    target_count: int
    collected_jobs: list[JobModel]
    visited_urls: set[str]
    search_queries: list[str]
    current_site_index: int
    iteration_count: int
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/agent/test_state.py`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git add src/agent/state.py tests/agent/test_state.py && git commit -m "feat: define agent state and job models"`

---

## Chunk 2: Nodes Implementation

### Task 3: Implement Planner Node

**Files:**
- Create: `src/agent/nodes.py`
- Create: `tests/agent/test_nodes.py`

- [ ] **Step 1: Write test for Planner Node**
```python
# tests/agent/test_nodes.py
from src.agent.state import AgentState
from src.agent.nodes import plan_search

def test_plan_search():
    state: AgentState = {"iteration_count": 0, "search_queries": [], "current_site_index": 0}
    new_state = plan_search(state)
    assert new_state["iteration_count"] == 1
    assert len(new_state["search_queries"]) == 1
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/agent/test_nodes.py::test_plan_search`
Expected: FAIL

- [ ] **Step 3: Implement Planner Node**
```python
# src/agent/nodes.py
from src.agent.state import AgentState

def plan_search(state: AgentState) -> dict:
    queries = ["AI Engineer 校园招聘", "大模型算法实习生", "NLP 算法工程师 校招"]
    idx = state.get("iteration_count", 0) % len(queries)
    new_query = queries[idx]
    
    return {
        "iteration_count": state.get("iteration_count", 0) + 1,
        "search_queries": state.get("search_queries", []) + [new_query]
    }
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/agent/test_nodes.py::test_plan_search`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git add src/agent/nodes.py tests/agent/test_nodes.py && git commit -m "feat: implement planner node"`

### Task 4: Implement Mock Search & Scrape Nodes

*Note: For the MVP, we will mock the actual network requests to ensure the graph logic works flawlessly first.*

**Files:**
- Modify: `src/agent/nodes.py`
- Modify: `tests/agent/test_nodes.py`

- [ ] **Step 1: Write tests for mock nodes**
```python
# tests/agent/test_nodes.py (append)
from src.agent.nodes import search_jobs, scrape_and_parse

def test_search_jobs():
    state = {"search_queries": ["test query"], "visited_urls": set()}
    new_state = search_jobs(state)
    assert "mock_url" in new_state["visited_urls"]

def test_scrape_and_parse():
    state = {"visited_urls": {"mock_url"}}
    jobs = scrape_and_parse(state)
    assert jobs[0].title == "Mock AI Job"
```

- [ ] **Step 2: Run test to fail**
Run: `pytest tests/agent/test_nodes.py`
Expected: FAIL

- [ ] **Step 3: Implement mock nodes**
```python
# src/agent/nodes.py (append)
from src.agent.state import JobModel

def search_jobs(state: AgentState) -> dict:
    new_urls = {f"mock_url_{state.get('iteration_count', 0)}"}
    return {
        "visited_urls": state.get("visited_urls", set()).union(new_urls)
    }

def scrape_and_parse(state: AgentState) -> list[JobModel]:
    return [
        JobModel(
            title="Mock AI Job", company="MockCorp", location="Remote",
            salary="200/day", tech_tags=["LLM"], requirements="Python",
            source="MockSite", job_url=list(state.get("visited_urls", set()))[-1]
        )
    ]
```

- [ ] **Step 4: Run test to pass**
Run: `pytest tests/agent/test_nodes.py`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git commit -am "feat: add mock search and scrape nodes"`

---

## Chunk 3: Graph Assembly

### Task 5: Build LangGraph Workflow

**Files:**
- Create: `src/agent/graph.py`
- Create: `tests/agent/test_graph.py`

- [ ] **Step 1: Write graph logic test**
```python
# tests/agent/test_graph.py
from src.agent.graph import build_graph

def test_graph_compiles():
    graph = build_graph()
    assert graph is not None
```

- [ ] **Step 2: Run test to fail**
Run: `pytest tests/agent/test_graph.py`
Expected: FAIL

- [ ] **Step 3: Implement Graph**
```python
# src/agent/graph.py
from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import plan_search, search_jobs, scrape_and_parse

def should_continue(state: AgentState):
    if len(state.get("collected_jobs", [])) >= state.get("target_count", 50):
        return END
    if state.get("iteration_count", 0) >= 10: # Safety fallback
        return END
    return "plan_search"

def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("plan_search", plan_search)
    workflow.add_node("search_jobs", search_jobs)
    workflow.add_node("scrape_and_parse", scrape_and_parse)
    
    workflow.set_entry_point("plan_search")
    workflow.add_edge("plan_search", "search_jobs")
    workflow.add_edge("search_jobs", "scrape_and_parse")
    
    # Mock evaluate step by just appending directly for MVP flow test
    def evaluate(state):
        jobs = scrape_and_parse(state)
        return {"collected_jobs": state.get("collected_jobs", []) + jobs}
    
    workflow.add_node("evaluate", evaluate)
    workflow.add_edge("scrape_and_parse", "evaluate")
    
    workflow.add_conditional_edges("evaluate", should_continue)
    
    return workflow.compile()
```

- [ ] **Step 4: Run test to pass**
Run: `pytest tests/agent/test_graph.py`
Expected: PASS

- [ ] **Step 5: Commit**
Run: `git add src/agent/graph.py tests/agent/test_graph.py && git commit -m "feat: assemble langgraph workflow"`

### Task 6: Main Entry Point

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Create Main Script**
```python
# src/main.py
from src.agent.graph import build_graph
import json

def run_agent():
    graph = build_graph()
    initial_state = {
        "target_count": 5, # Low target for quick MVP run
        "collected_jobs": [],
        "visited_urls": set(),
        "search_queries": [],
        "current_site_index": 0,
        "iteration_count": 0
    }
    
    final_state = graph.invoke(initial_state)
    
    print(f"Finished! Collected {len(final_state['collected_jobs'])} jobs.")
    
    # Output to JSON
    jobs_dict = [job.model_dump() for job in final_state['collected_jobs']]
    with open('jobs_output.json', 'w', encoding='utf-8') as f:
        json.dump(jobs_dict, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_agent()
```

- [ ] **Step 2: Run Main**
Run: `python src/main.py`
Expected: Outputs JSON file with 5 mock jobs.

- [ ] **Step 3: Commit**
Run: `git add src/main.py && git commit -m "feat: create main execution script"`
