from src.agent.state import AgentState, JobModel
from src.agent.tools import unified_search_tool
from src.agent.parser import get_parser, parse_card_with_llm
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
from loguru import logger
from dotenv import load_dotenv


class SearchJobsQuery(BaseModel):
    """Call the search tool to find jobs."""

    query: str = Field(
        description="The search keyword, MUST be very short and concise core technical terms only, e.g. 'AI', '大模型', 'NLP', '机器学习'"
    )
    reasoning: str = Field(
        description="Why you chose this query to find new, unique jobs."
    )


def plan_search(state: AgentState) -> dict:
    """Agentic planning node: Uses LLM to autonomously decide the next search query based on current progress."""
    load_dotenv()

    volc_model = os.getenv("VOLC_MODEL")
    volc_api_key = os.getenv("VOLC_API_KEY")
    volc_api_base = os.getenv("VOLC_API_BASE")

    if not volc_model or not volc_api_key:
        raise ValueError("Missing Volcengine credentials.")

    llm = ChatOpenAI(
        model=volc_model, api_key=volc_api_key, base_url=volc_api_base, temperature=0.5
    )

    llm_with_tools = llm.bind_tools([SearchJobsQuery])

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an autonomous AI Job Search Agent. Your goal is to collect {target_count} distinct 'AI Engineer' jobs for fresh graduates/interns.\n\n"
                "Progress: Collected {current_count} jobs out of {target_count}.\n"
                "Past search queries used: {search_queries}\n\n"
                "Your task: You MUST call the search tool by providing a NEW, distinct search query to find more relevant jobs. "
                "CRITICAL RULE: The target website search engine is very strict and fails on long conversational queries. "
                "You MUST use VERY SHORT, core technical keywords ONLY (e.g., 2-4 Chinese characters or short English acronyms). "
                "DO NOT include words like '实习', '校招', '应届生', '工程师', '算法' in your query. "
                "Good query examples: 'AI', '大模型', 'NLP', 'CV', '深度学习', '机器学习', 'AIGC', '强化学习', '推荐系统', '数据挖掘'.\n"
                "Do not reuse exact queries from the past list.",
            ),
            ("human", "Decide the next search action by calling the search tool."),
        ]
    )

    chain = prompt | llm_with_tools

    try:
        res = chain.invoke(
            {
                "target_count": state.get("target_count", 50),
                "current_count": len(state.get("collected_jobs", [])),
                "search_queries": state.get("search_queries", []),
            }
        )

        if hasattr(res, "tool_calls") and len(res.tool_calls) > 0:
            tool_args = res.tool_calls[0]["args"]
            new_query = tool_args.get("query", "AI")
            reasoning = tool_args.get("reasoning", "No reasoning provided.")
            logger.info(
                f"Agent 自主规划搜索 (Tool Call): query='{new_query}', 思考逻辑: '{reasoning}'"
            )
        else:
            logger.warning("Agent 并没有调用工具，使用默认降级词")
            new_query = "AI"
    except Exception as e:
        logger.error(f"Agent规划异常，使用fallback: {e}")
        fallbacks = ["AI", "算法工程师", "大模型"]
        idx = state.get("iteration_count", 0) % len(fallbacks)
        new_query = fallbacks[idx]

    return {
        "iteration_count": state.get("iteration_count", 0) + 1,
        "search_queries": state.get("search_queries", []) + [new_query],
        "current_site_index": state.get("current_site_index", 0) + 1,
    }


def search_jobs(state: AgentState) -> dict:
    query = state.get("search_queries", ["AI"])[-1]

    platforms = ["nowcoder", "yingjiesheng"]
    idx = state.get("current_site_index", 0) % len(platforms)
    platform = platforms[idx]

    results = unified_search_tool(query, platform=platform)
    if not results:
        return {
            "visited_urls": state.get("visited_urls", set()),
            "raw_search_results": "",
        }

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

    platforms = ["nowcoder", "yingjiesheng"]
    idx = state.get("current_site_index", 0) % len(platforms)
    platform = platforms[idx]

    # logger.info(f"原始输入：{raw_markdown}")

    parser = get_parser(platform)

    # 2. Split into cards
    cards = parser.split_job_cards(raw_markdown)

    # logger.info(f"筛选后的 LLM 输入：{cards}")

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
    is_ai_list = parser.is_ai_related_batch(cards, llm)
    logger.info(f"AI相关判断结果: {is_ai_list}")

    # 阶段2: 代码解析所有AI相关岗位
    existing_jobs = state.get("collected_jobs", [])
    existing_urls = {j.job_url for j in existing_jobs if hasattr(j, "job_url")}

    jobs = []
    for i, (card, is_ai) in enumerate(zip(cards, is_ai_list)):
        if is_ai:
            try:
                job = parser.parse_card_regex(card)
                if job:
                    if job.job_url not in existing_urls:
                        logger.info(f"解析成功并添加: {job.title} - {job.company}")
                        jobs.append(job)
                        existing_urls.add(job.job_url)
                    else:
                        logger.debug(f"跳过重复岗位: {job.title} - {job.company}")
            except Exception as e:
                logger.error(f"解析第{i + 1}个卡片失败: {e}")
                continue

    return {"collected_jobs": existing_jobs + jobs}
