# AI Job Search Assistant Todo List

## Current Phase: Enhancement & Filtering

- [x] **Task 1: Model Robustness**
    - [x] Fix Pydantic validation warning by making `location`, `salary`, `requirements` optional in `src/agent/state.py`.
    - [x] Ensure `load_dotenv()` is called at the absolute beginning of `src/main.py`.

- [x] **Task 2: Implement Evaluator Node / Parsing Optimization**
    - [x] Implement logic to evaluate jobs in batch using Volcengine LLM (returns True/False for each card).
    - [x] Extract `company`, `title`, `salary`, `location` and `requirements` fields accurately using regex for high speed.
    - [x] Filter out jobs that are not related to AI Engineer.
    - [x] Correct sequence combination logic (Job -> Enterprise) based on Firecrawl extraction layout.

- [x] **Task 3: Scale Up Execution**
    - [x] Update `target_count` to 50 in `src/main.py`.
    - [x] Increase `iteration_count` limit for safety in `src/agent/graph.py` to allow more loops.

- [x] **Task 4: Final Verification**
    - [x] Run end-to-end to collect 50 jobs.
    - [x] Verify `jobs_output.json` contains only relevant AI Engineer roles.
