from src.agent.tools import unified_search_tool


def test_unified_search_tool_returns_mocked_results():
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


def test_unified_search_tool_default_platform():
    query = "test query"
    results = unified_search_tool(query=query)
    assert len(results) > 0
