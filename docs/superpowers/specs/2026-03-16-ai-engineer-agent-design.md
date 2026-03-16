# AI Engineer Job Search Agent - Design Specification

## 1. Overview
An autonomous Agentic system built to collect, filter, and structure 50 "AI Engineer" campus recruitment/internship job postings. It addresses the challenge of manually searching across multiple platforms (e.g., Nowcoder, Boss Zhipin) by fully automating the pipeline: search -> scrape -> parse -> evaluate -> iterate.

## 2. Architecture & Tech Stack
- **Framework:** LangGraph (State Machine / Directed Graph approach).
- **Core LLM:** OpenAI compatible API (e.g., GPT-4o-mini or GPT-4o) via `langchain-openai`.
- **Primary Data Sources:** Nowcoder (牛客), Boss Zhipin (Boss直聘), Liepin (猎聘).
- **Format:** Python Script.

## 3. Agent Graph Design (LangGraph)
The system is modeled as a state machine where the State holds:
- `target_count` (int, default 50)
- `collected_jobs` (list of dicts)
- `visited_urls` (set of string URLs)
- `search_queries` (list of used queries)
- `current_site_index` (int)
- `iteration_count` (int, for anti-infinite loop)

### Nodes
1. **Planner Node (`plan_search`)**:
   - Generates/refines search queries (e.g., "AI Engineer 校园招聘", "大模型算法实习生").
   - Switches platforms if current one yields no new results.
2. **Searcher Node (`search_jobs`)**:
   - Calls a Search Tool (simulated or real SERP) targeting the current platform using the query.
   - Extracts job URLs.
3. **Scraper & Parser Node (`scrape_and_parse`)**:
   - Fetches content from URLs.
   - Uses LLM Tool/Function Calling to extract structured data: `title, company, location, salary, tech_tags, requirements, source, job_url`.
4. **Evaluator Node (`evaluate_job`)**:
   - Semantic judgment: LLM assesses if the job truly matches "AI Engineer" AND "Campus/Intern" criteria.
   - Filters out generic backend or senior roles.
   - Valid jobs are appended to `collected_jobs`.

### Edges
- **Conditional Edge (`check_progress`)**:
   - Checks `len(collected_jobs) >= target_count`.
   - If YES -> End.
   - If NO -> Checks `iteration_count < max_iterations`.
   - If under limit -> loops back to **Planner Node**.
   - If over limit -> Fallback/End.

## 4. Addressing Core Challenges
- **Semantic Judgment**: LLM is explicitly prompted to act as a strict HR screener to verify the "AI Engineer" aspect.
- **Dynamic Iteration**: If results are exhausted or insufficient, the Planner node automatically generates novel semantic variations of the query.
- **Infinite Loop Prevention**: A hard limit on graph iterations and a tracking set of `visited_urls` prevents getting stuck.
- **Fallback**: If one site blocks scraping or has no results, the agent increments `current_site_index` to rotate to a fallback platform.

## 5. Output Format
Standardized JSON/CSV containing:
- title, company, location, salary, tech_tags, requirements, source, job_url
