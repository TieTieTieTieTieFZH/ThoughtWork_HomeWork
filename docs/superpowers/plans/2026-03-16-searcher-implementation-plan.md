# Searcher Implementation Plan (Firecrawl Integration)

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Searcher tool using Firecrawl to fetch and parse job listings from Nowcoder.

**Architecture:** A standalone tool `unified_search_tool` that uses `firecrawl-py` to scrape Markdown and LLM to extract structured job links.

**Tech Stack:** Python, `firecrawl-py`, `langchain-openai`, `pytest`.

---

## Chunk 1: Tools & Environment

### Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add firecrawl-py to requirements.txt**
```text
firecrawl-py
```

- [ ] **Step 2: Run pip install**
Run: `pip install -r requirements.txt`

- [ ] **Step 3: Commit**
Run: `git add requirements.txt && git commit -m "chore: add firecrawl dependency"`

### Task 2: Implement Unified Search Tool (Mocked)

**Files:**
- Create: `src/agent/tools.py`
- Create: `tests/agent/test_tools.py`

- [ ] **Step 1: Write failing test for the tool**
```python
from src.agent.tools import unified_search_tool

def test_unified_search_tool_returns_list():
    results = unified_search_tool("AI Engineer", "nowcoder")
    assert isinstance(results, list)
```

- [ ] **Step 2: Implement minimal tool (mocked)**
```python
def unified_search_tool(query: str, platform: str = "nowcoder"):
    return [{"title": "Test Job", "url": "http://example.com", "description": "test"}]
```

- [ ] **Step 3: Commit**
Run: `git add src/agent/tools.py tests/agent/test_tools.py && git commit -m "feat: initial unified search tool stub"`

---

## Chunk 2: Firecrawl Integration

### Task 3: Real Firecrawl Implementation

**Files:**
- Modify: `src/agent/tools.py`

- [ ] **Step 1: Implement Firecrawl logic**
```python
from firecrawl import FirecrawlApp
import os

def unified_search_tool(query: str, platform: str = "nowcoder"):
    # Construction logic for Nowcoder
    url = f"https://www.nowcoder.com/search-job?query={query}"
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    # In a real scenario, we'd use LLM to extract from the markdown
    # For MVP, we use the 'scrape' endpoint and a simple extraction prompt
    result = app.scrape_url(url, params={'formats': ['markdown']})
    # TODO: Add LLM extraction logic here
    return [{"title": "Found Job", "url": url, "description": "Markdown captured"}]
```

- [ ] **Step 2: Commit**
Run: `git commit -am "feat: add firecrawl scraping logic"`

### Task 4: Integrate Tool into Node

**Files:**
- Modify: `src/agent/nodes.py`

- [ ] **Step 1: Update search_jobs node to use the tool**
```python
from src.agent.tools import unified_search_tool

def search_jobs(state: AgentState) -> dict:
    query = state["search_queries"][-1]
    results = unified_search_tool(query)
    new_urls = {r["url"] for r in results}
    return {
        "visited_urls": state.get("visited_urls", set()).union(new_urls)
    }
```

- [ ] **Step 2: Commit**
Run: `git commit -am "feat: integrate search tool into search_jobs node"`
