import os
import firecrawl
from loguru import logger


def unified_search_tool(query: str, platform: str = "nowcoder") -> list[dict[str, str]]:
    """
    Scrapes job listings from Nowcoder using Firecrawl.
    Returns a list of dicts: [{"title": str, "url": str, "description": str}].
    """
    app = firecrawl.FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    if platform == "nowcoder":
        # Using the specified intern center search URL
        url = (
            f"https://www.nowcoder.com/jobs/school/jobs?search={query}"
        )
    else:
        url = (
            f"https://www.nowcoder.com/jobs/school/jobs?search={query}"
        )

    logger.info(f"当前访问的网站地址：{url}")
    # Scraping logic
    # Firecrawl SDK v4.0.0+ uses keyword arguments for scraping
    try:
        result = app.scrape(
            url, 
            formats=["markdown"],
            wait_for=5000, 
            mobile=False
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
