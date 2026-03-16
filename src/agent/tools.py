def unified_search_tool(query: str, platform: str = "nowcoder") -> list[dict[str, str]]:
    """
    Mocked version of unified_search_tool.
    Returns a list of dicts: [{"title": str, "url": str, "description": str}].
    """
    return [
        {
            "title": f"Mocked result for {query} on {platform}",
            "url": f"https://example.com/search?q={query}&p={platform}",
            "description": f"This is a mocked description for the search query '{query}'.",
        }
    ]
