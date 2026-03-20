# Async Job Enrichment Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Asynchronously batch-enrich job listings with LLM-extracted `tech_tags` and `requirements` using Firecrawl after the main LangGraph execution completes.

**Architecture:** A sequential processing pipeline appended to `main.py`. It takes the final `collected_jobs` list from the graph state, chunks it into sizes of 10, concurrently uses `asyncio` to scrape markdown via Firecrawl, formats a bulk prompt, and uses an LLM to generate a JSON array of parsed tags/requirements mapped back to the jobs.

**Tech Stack:** Python, `asyncio`, Firecrawl, LangChain (LLM bindings), Pydantic.

---

## Chunk 1: Tool & Parser Updates

### Task 1: Add Firecrawl detail fetcher tool

**Files:**
- Modify: `src/agent/tools.py`

- [ ] **Step 1: Write the asynchronous fetching tool**
```python
import asyncio
from loguru import logger
from firecrawl import FirecrawlApp
import os

async def fetch_job_detail_async(url: str, app: FirecrawlApp) -> dict:
    """Asynchronously fetches markdown from a job URL."""
    try:
        # Run synchronous Firecrawl SDK call in a thread pool to unblock async loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: app.scrape(url, formats=["markdown"], wait_for=2000, mobile=False)
        )
        # Handle dict or object response based on Firecrawl SDK version
        markdown_content = ""
        if hasattr(result, "markdown") and result.markdown:
            markdown_content = result.markdown
        elif isinstance(result, dict) and result.get("markdown"):
             markdown_content = result["markdown"]
        else:
             markdown_content = "Failed to extract markdown."
             
        return {"url": url, "markdown": markdown_content}
    except Exception as e:
        logger.error(f"Failed to fetch detail for {url}: {e}")
        return {"url": url, "markdown": f"Error: {e}"}
```

- [ ] **Step 2: Commit changes**
```bash
git add src/agent/tools.py
git commit -m "feat: add async firecrawl job detail fetcher"
```

### Task 2: Create LLM extraction parser

**Files:**
- Modify: `src/agent/parser.py`
- Modify: `src/agent/state.py` (ensure Pydantic structure is ready)

- [ ] **Step 1: Define Pydantic schema for LLM output in state**
(No action needed if `JobModel` already exists with `tech_tags` and `requirements`, just verifying).

- [ ] **Step 2: Write batch extraction logic**
```python
import json
from langchain_core.prompts import PromptTemplate
from src.agent.state import JobModel
from loguru import logger

def batch_extract_details(llm, markdowns_dict: list[dict]) -> dict:
    """
    Takes a list of dicts [{"url": url, "markdown": text}] and asks LLM 
    to extract tech_tags and requirements. Returns a mapping of {url: {"tech_tags": [], "requirements": ""}}.
    """
    prompt = PromptTemplate.from_template("""
    You are an expert HR data extractor. 
    Below are several job descriptions in markdown format, identified by their URLs.
    
    For EACH job, extract:
    1. tech_tags: A list of 1-5 core technical keywords (e.g., ["LLM", "CV", "NLP", "PyTorch", "推荐系统"]).
    2. requirements: A very brief 1-2 sentence summary of the core job requirements/skills needed.
    
    JOB DESCRIPTIONS:
    {job_data}
    
    Output a strictly valid JSON object where keys are the job URLs, and values are objects containing 'tech_tags' and 'requirements'.
    Example:
    {{
        "https://url1...": {{"tech_tags": ["LLM", "Python"], "requirements": "Requires 3+ years experience with LLMs and distributed training."}},
        "https://url2...": {{"tech_tags": ["CV", "C++"], "requirements": "Strong background in computer vision and object detection."}}
    }}
    """)
    
    # Format the input data to save token space
    job_text = ""
    for item in markdowns_dict:
        # truncate markdown to avoid blowing up context window (first 2500 chars usually contains requirements)
        content = item['markdown'][:2500] 
        job_text += f"\n--- URL: {item['url']} ---\n{content}\n"
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"job_data": job_text})
        # Extract JSON from response (handling potential markdown formatting in response)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        parsed_data = json.loads(content)
        return parsed_data
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        return {}
```

- [ ] **Step 3: Commit changes**
```bash
git add src/agent/parser.py
git commit -m "feat: add batch llm extraction logic for job details"
```

---

## Chunk 2: Integration

### Task 3: Orchestrate the async pipeline in main.py

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: Write the enrichment runner function**
```python
import asyncio
from firecrawl import FirecrawlApp
import os
from src.agent.tools import fetch_job_detail_async
from src.agent.parser import batch_extract_details
from loguru import logger
from tqdm import tqdm

async def enrich_jobs_async(jobs, llm, batch_size=5):
    """Processes jobs in batches concurrently."""
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    enriched_jobs = []
    
    # Process in chunks to avoid rate limits and massive context windows
    for i in tqdm(range(0, len(jobs), batch_size), desc="Enriching jobs"):
        batch = jobs[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}...")
        
        # 1. Fetch markdowns concurrently
        tasks = [fetch_job_detail_async(job.job_url, app) for job in batch]
        markdown_results = await asyncio.gather(*tasks)
        
        # 2. Batch extract via LLM
        extracted_data = batch_extract_details(llm, markdown_results)
        
        # 3. Merge data back to Pydantic models
        for job in batch:
            url = job.job_url
            if url in extracted_data:
                job.tech_tags = extracted_data[url].get("tech_tags", [])
                job.requirements = extracted_data[url].get("requirements", "")
            enriched_jobs.append(job)
            
        # Optional: small sleep between batches to avoid 429 rate limit
        await asyncio.sleep(2)
        
    return enriched_jobs
```

- [ ] **Step 2: Hook up in main block**
Find the block where `graph.invoke` finishes and the json is saved. Modify it:
```python
    # ... graph execution ...
    final_state = app.invoke(initial_state)

    logger.info(f"Final state: {final_state['collected_jobs']}")

    # --- NEW ENRICHMENT STEP ---
    logger.info("Starting detail enrichment process...")
    # Initialize LLM (same one used for graph or a cheaper/faster one if desired)
    from src.agent.nodes import llm 
    enriched_jobs = asyncio.run(enrich_jobs_async(final_state["collected_jobs"], llm, batch_size=5))
    
    # Prepare data for JSON saving
    jobs_dict = [job.model_dump() for job in enriched_jobs]

    with open("jobs_output.json", "w", encoding="utf-8") as f:
        json.dump(jobs_dict, f, ensure_ascii=False, indent=2)

    logger.info(f"成功保存 {len(jobs_dict)} 条岗位信息到 jobs_output.json")
```

- [ ] **Step 3: Commit changes**
```bash
git add src/main.py
git commit -m "feat: integrate async job enrichment pipeline"
```
