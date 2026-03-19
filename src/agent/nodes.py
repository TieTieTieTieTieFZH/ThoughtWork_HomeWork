from src.agent.state import AgentState, JobModel
from src.agent.tools import unified_search_tool
from src.agent.parser import (
    split_job_cards,
    parse_card_with_llm,
    is_ai_related_batch,
    parse_card_regex,
)
from langchain_openai import ChatOpenAI
import os
from loguru import logger


def plan_search(state: AgentState) -> dict:
    queries = ["AI", "大模型算法实习生", "NLP 算法工程师 校招"]
    idx = state.get("iteration_count", 0) % len(queries)
    new_query = queries[idx]
    logger.info(f"plan_search 输出：{state.get('search_queries', []) + [new_query]}")
    return {
        "iteration_count": state.get("iteration_count", 0) + 1,
        "search_queries": state.get("search_queries", []) + [new_query],
    }


def search_jobs(state: AgentState) -> dict:
    query = state.get("search_queries", ["AI"])[-1]
    # TODO query的选取需要处理，AI Enginner 在牛客无法检索内容，但是AI 工程师可以
    results = unified_search_tool(query)
    if not results:
        return {
            "visited_urls": state.get("visited_urls", set()),
            "raw_search_results": "",
        }

    # We take the first result's markdown as the current raw_search_results
    raw_md = results[0].get("markdown", "")
    new_urls = {res["url"] for res in results}
    return {
        "visited_urls": state.get("visited_urls", set()).union(new_urls),
        "raw_search_results": raw_md,
    }


def scrape_and_parse(state: AgentState) -> dict:
    from dotenv import load_dotenv

    load_dotenv()

    raw_markdown = state.get("raw_search_results", "")
    if not raw_markdown:
        return {"collected_jobs": state.get("collected_jobs", [])}

    # 2. Split into cards
    cards = split_job_cards(raw_markdown)

    if not cards:
        return {"collected_jobs": state.get("collected_jobs", [])}

    volc_model = os.getenv("VOLC_MODEL")
    volc_api_key = os.getenv("VOLC_API_KEY")
    volc_api_base = os.getenv("VOLC_API_BASE")

    if not volc_model or not volc_api_key:
        raise ValueError(
            f"Missing Volcengine credentials: MODEL={volc_model}, KEY={volc_api_key}"
        )

    llm = ChatOpenAI(model=volc_model, api_key=volc_api_key, base_url=volc_api_base)

    # 阶段1: LLM一次判断所有卡片是否AI相关
    is_ai_list = is_ai_related_batch(cards, llm)
    logger.info(f"AI相关判断结果: {is_ai_list}")

    # 阶段2: 代码解析所有AI相关岗位
    jobs = []
    for i, (card, is_ai) in enumerate(zip(cards, is_ai_list)):
        if is_ai:
            try:
                job = parse_card_regex(card)
                if job:
                    logger.info(f"解析成功: {job}")
                    jobs.append(job)
            except Exception as e:
                logger.error(f"解析第{i + 1}个卡片失败: {e}")
                continue

    return {"collected_jobs": state.get("collected_jobs", []) + jobs}
