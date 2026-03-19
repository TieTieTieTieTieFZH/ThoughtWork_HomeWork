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
    raw_search_results: str
