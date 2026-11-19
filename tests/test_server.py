"""Tests for the PhenotypeLibrary MCP Server."""

from unittest.mock import MagicMock, patch

import pytest

from server import (
    PaginatedResponse,
    PhenotypeLibraryClient,
)


@pytest.fixture
def client():
    """Create a test client (no auth)."""
    return PhenotypeLibraryClient(
        base_url="https://test.api/v1/",
        timeout=30.0,
    )


def test_client_initialization(client):
    """Test client initialization."""
    assert str(client.http.base_url).startswith("https://test.api/v1/")
    assert client.http.auth is None


def test_client_auth_configured():
    """Test client sets BasicAuth when credentials are present."""
    c = PhenotypeLibraryClient(
        base_url="https://test.api/v1/",
        timeout=30.0,
        username="user",
        password="pass",
    )
    assert c.http.auth is not None


def test_get_request(client):
    """Test making a GET request via client.get."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"count": 1, "results": [{"id": "1"}]}
    mock_response.raise_for_status = MagicMock()
    mock_http = MagicMock()
    mock_http.get.return_value = mock_response
    client.http = mock_http

    result = client.get("/test/", {"param": "value"})

    assert result == {"count": 1, "results": [{"id": "1"}]}
    mock_http.get.assert_called_once_with("/test/", params={"param": "value"})


def test_list_normalizes_bare_list(client):
    """A bare JSON array becomes count/results."""
    data = [{"id": 1}, {"id": 2}]
    with patch.object(client, "get", return_value=data):
        result = client.list("/collections/")
    assert result == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    assert isinstance(PaginatedResponse(**result), PaginatedResponse)


def test_list_normalizes_paged_mapping(client):
    """A page/total_pages/data mapping becomes count/results."""
    data = {"page": 1, "total_pages": 1, "data": [{"id": 1}]}
    with patch.object(client, "get", return_value=data):
        result = client.list("/data-sources/")
    assert result["count"] == 1
    assert result["results"] == [{"id": 1}]


def test_list_passes_through_drf_shape(client):
    """A DRF count/next/previous/results mapping passes through unchanged."""
    data = {
        "count": 1,
        "next": "https://test.api/v1/tags/?page=2",
        "previous": None,
        "results": [{"id": 1, "name": "Test"}],
    }
    with patch.object(client, "get", return_value=data):
        result = client.list("/tags/", {"search": "test"})
    assert result == data


def test_normalize_concept_id():
    """Concept IDs get a single 'C' prefix."""
    assert PhenotypeLibraryClient.normalize_concept_id("714") == "C714"
    assert PhenotypeLibraryClient.normalize_concept_id("c714") == "c714"
    assert PhenotypeLibraryClient.normalize_concept_id("C714") == "C714"
    assert PhenotypeLibraryClient.normalize_concept_id(" 714 ") == "C714"


def test_unwrap():
    """Single-item lists from detail endpoints are unwrapped."""
    from server import _unwrap

    assert _unwrap([{"id": 1}]) == {"id": 1}
    assert _unwrap([{"id": 1}, {"id": 2}]) == [{"id": 1}, {"id": 2}]
    assert _unwrap({"id": 1}) == {"id": 1}


def test_mcp_tool_registry():
    """All expected tools are registered on the FastMCP instance."""
    import asyncio

    from server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "search_phenotypes",
        "get_phenotype_codelist",
        "get_phenotype_detail",
        "get_phenotype_versions",
        "search_concepts",
        "get_concept_codelist",
        "get_concept_detail",
        "get_concept_versions",
        "search_ontology",
        "get_ontology_groups",
        "get_ontology_node",
        "get_ontology_type",
        "get_collections",
        "get_collection_detail",
        "get_tags",
        "get_tag_detail",
        "get_data_sources",
        "get_data_source_detail",
        "get_templates",
        "get_template_detail",
        "get_template_versions",
    }
    assert names == expected


def test_mcp_resource_and_prompt_registry():
    """The stdio/SSE-only resource+prompt helpers were removed with the refactor."""
    import asyncio

    from server import mcp

    assert list(asyncio.run(mcp.list_resources())) == []
    assert list(asyncio.run(mcp.list_prompts())) == []


def test_health_route_registered():
    """/health is a custom route on the streamable HTTP ASGI app."""
    from server import mcp

    app = mcp.streamable_http_app()
    routes = {r.path for r in app.routes}
    assert "/health" in routes
    assert "/mcp" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])