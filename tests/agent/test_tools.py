from unittest.mock import patch, MagicMock
from src.agent.tools import unified_search_tool


@patch("src.agent.tools.firecrawl.FirecrawlApp")
def test_unified_search_tool_returns_mocked_results(mock_firecrawl):
    # Setup mock
    mock_app = MagicMock()
    mock_app.scrape_url.return_value = {"success": True, "markdown": "dummy content"}
    mock_firecrawl.return_value = mock_app

    query = "test query"
    platform = "nowcoder"
    results = unified_search_tool(query=query, platform=platform)

    assert isinstance(results, list)
    assert len(results) > 0
    for item in results:
        assert isinstance(item, dict)
        assert "title" in item
        assert "url" in item
        assert "description" in item
        assert isinstance(item["title"], str)
        assert isinstance(item["url"], str)
        assert isinstance(item["description"], str)


@patch("src.agent.tools.firecrawl.FirecrawlApp")
def test_unified_search_tool_default_platform(mock_firecrawl):
    # Setup mock
    mock_app = MagicMock()
    mock_app.scrape_url.return_value = {"success": True, "markdown": "dummy content"}
    mock_firecrawl.return_value = mock_app

    query = "test query"
    results = unified_search_tool(query=query)
    assert len(results) > 0
