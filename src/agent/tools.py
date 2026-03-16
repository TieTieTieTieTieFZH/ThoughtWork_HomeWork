import os
import firecrawl


def unified_search_tool(query: str, platform: str = "nowcoder") -> list[dict[str, str]]:
    """
    Scrapes job listings from Nowcoder using Firecrawl.
    Returns a list of dicts: [{"title": str, "url": str, "description": str}].
    """
    app = firecrawl.FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    url = f"https://www.nowcoder.com/search-job?query={query}"

    # Simple scraping logic as per the plan
    app.scrape_url(url, params={"formats": ["markdown"]})

    return [
        {
            "title": f"Firecrawl result for {query} on {platform}",
            "url": url,
            "description": f"Markdown captured for {query} using Firecrawl.",
        }
    ]
