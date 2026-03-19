import json
from dotenv import load_dotenv

load_dotenv()
from src.agent.graph import build_graph


def run_agent():
    graph = build_graph()
    initial_state = {
        "target_count": 50,  # Target 50 jobs
        "collected_jobs": [],
        "visited_urls": set(),
        "search_queries": [],
        "current_site_index": 0,
        "iteration_count": 0,
        "raw_search_results": "",
    }

    final_state = graph.invoke(initial_state)

    print(f"Finished! Collected {len(final_state['collected_jobs'])} jobs.")

    # Output to JSON
    jobs_dict = [job.model_dump() for job in final_state["collected_jobs"]]
    with open("jobs_output.json", "w", encoding="utf-8") as f:
        json.dump(jobs_dict, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run_agent()
