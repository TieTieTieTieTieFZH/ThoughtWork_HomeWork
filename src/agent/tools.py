import os
import firecrawl
from loguru import logger
import concurrent.futures
from pydantic import BaseModel, Field
from src.agent.state import JobModel


class JobDetailSchema(BaseModel):
    tech_tags: list[str] = Field(
        description="提取出来的技术关键词，例如 ['LLM', 'CV', 'NLP', '推荐系统', '数据分析'] 等"
    )
    requirements: str = Field(
        description="岗位核心技能摘要，简明扼要地用一段话总结该岗位所需要的核心技能与经验要求"
    )


def extract_job_detail(app: firecrawl.FirecrawlApp, job: JobModel) -> JobModel:
    url = job.job_url
    if not url or not url.startswith("http"):
        return job

    # logger.info(f"开始抓取详情页并提取技术栈: {job.title} ({url})")
    try:
        result = app.scrape(
            url,
            formats=[
                {
                    "type": "json",
                    "schema": JobDetailSchema.model_json_schema(),
                    "prompt": "仔细阅读岗位的描述内容，提取出专业的技术关键词(tech_tags)，并将岗位职责与要求精简为一段核心技能摘要(requirements)。",
                }
            ],
            only_main_content=True,
            timeout=120000,
        )
        if result and hasattr(result, "json") and result.json:
            detail_data = result.json
            # logger.info(f"详细描述：{detail_data}")
            if detail_data.get("tech_tags"):
                job.tech_tags = detail_data.get("tech_tags")
            if detail_data.get("requirements"):
                job.requirements = detail_data.get("requirements")
            # logger.success(f"成功提取详情: {job.title} (Tags: {job.tech_tags})")
        # Handle dict response which might be what SDK returns depending on version
        elif isinstance(result, dict) and "json" in result:
            detail_data = result["json"]
            if detail_data and detail_data.get("tech_tags"):
                job.tech_tags = detail_data.get("tech_tags")
            if detail_data and detail_data.get("requirements"):
                job.requirements = detail_data.get("requirements")
            # logger.success(f"成功提取详情: {job.title} (Tags: {job.tech_tags})")
        else:
            logger.warning(f"详情页未返回JSON内容: {url}")

    except Exception as e:
        logger.error(f"详情页抓取失败 {url}: {e}")

    return job


def enrich_job_details(jobs: list[JobModel], max_workers: int = 5) -> list[JobModel]:
    """并发请求抓取各个岗位的详情页"""
    if not jobs:
        return jobs

    from dotenv import load_dotenv

    load_dotenv()

    app = firecrawl.FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    logger.info(f"启动多线程详情页抓取，共有 {len(jobs)} 个新岗位待处理...")

    enriched_jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_job_detail, app, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            enriched_jobs.append(future.result())

    return enriched_jobs


def unified_search_tool(
    query: str, platform: str = "nowcoder", page: int = 3
) -> list[dict[str, str]]:
    """
    Scrapes job listings from Nowcoder using Firecrawl.
    Returns a list of dicts: [{"title": str, "url": str, "description": str}].
    """
    app = firecrawl.FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    if platform == "nowcoder":
        # Using the specified intern center search URL
        url = f"https://www.nowcoder.com/jobs/school/jobs?search={query}&order={page}"
    elif platform == "yingjiesheng":
        url = f"https://q.yingjiesheng.com/jobs/search/{query}"
    else:
        url = f"https://www.nowcoder.com/jobs/school/jobs?search={query}&order={page}"

    logger.info(f"当前访问的网站地址：{url}")
    # Scraping logic
    # Firecrawl SDK v4.0.0+ uses keyword arguments for scraping
    try:
        result = app.scrape(
            url,
            formats=["markdown"],
            wait_for=10000,
            mobile=False,
            only_main_content=True,
        )
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return []

    # Check for success
    if result and hasattr(result, "markdown") and result.markdown:
        markdown_content = result.markdown
        # logger.info(f"firecrawl 爬取的信息：{result.markdown[:500]}")
        return [
            {
                "title": f"Firecrawl result for {query} on {platform}",
                "url": url,
                "markdown": markdown_content,
                "description": f"Successfully captured Markdown (length: {len(markdown_content)})",
            }
        ]

    return []
