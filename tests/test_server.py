"""Tests for the PhenotypeLibrary MCP Server."""

import pytest
from unittest.mock import MagicMock, patch

from phenotypelibrary_mcp.server import (
    PhenotypeLibraryClient,
    Config,
    PaginatedResponse,
)


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        base_url="https://test.api/v1/",
        username="test_user",
        password="test_pass",
    )


@pytest.fixture
def client(config):
    """Create a test client."""
    return PhenotypeLibraryClient(config)


def test_client_initialization(client):
    """Test client initialization."""
    assert client.config.base_url == "https://test.api/v1/"
    assert client.config.username == "test_user"
    assert client.config.password == "test_pass"
    assert client._client is None


def test_get_client_creates_http_client(client):
    """Test that _get_client creates an HTTP client with auth."""
    with patch("phenotypelibrary_mcp.server.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        result = client._get_client()
        
        assert result == mock_client
        mock_client_class.assert_called_once()
        call_kwargs = mock_client_class.call_args.kwargs
        assert call_kwargs["base_url"] == "https://test.api/v1/"
        assert call_kwargs["timeout"] == 30.0
        assert call_kwargs["auth"] is not None


def test_get_client_without_auth():
    """Test client creation without authentication."""
    config = Config(base_url="https://test.api/v1/")
    client = PhenotypeLibraryClient(config)
    
    with patch("phenotypelibrary_mcp.server.httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        result = client._get_client()
        
        assert result == mock_client
        call_kwargs = mock_client_class.call_args.kwargs
        assert call_kwargs["auth"] is None


def test_close_client(client):
    """Test closing the HTTP client."""
    mock_client = MagicMock()
    client._client = mock_client
    
    client.close()
    
    mock_client.close.assert_called_once()
    assert client._client is None


def test_get_request(client):
    """Test making a GET request."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"count": 1, "results": [{"id": "1"}]}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    client._client = mock_client
    
    result = client._get("/test/", {"param": "value"})
    
    assert result == {"count": 1, "results": [{"id": "1"}]}
    mock_client.get.assert_called_once_with("/test/", params={"param": "value"})


def test_get_collections(client):
    """Test getting collections."""
    mock_response = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "name": "Test"}]}
    
    with patch.object(client, "_get", new_callable=MagicMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = client.get_collections(search="test")
        
        assert isinstance(result, PaginatedResponse)
        assert result.count == 1
        mock_get.assert_called_once_with("/collections/", {"search": "test"})


def test_get_concepts(client):
    """Test getting concepts with various parameters."""
    mock_response = {"count": 1, "next": None, "previous": None, "results": [{"id": "C1", "name": "Test"}]}
    
    with patch.object(client, "_get", new_callable=MagicMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = client.get_concepts(
            search="asthma",
            tags="1,2",
            collections="3",
            page=2,
            page_size=2,
            no_pagination=True,
        )
        
        assert isinstance(result, PaginatedResponse)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/concepts/"
        params = call_args[0][1]
        assert params["search"] == "asthma"
        assert params["tags"] == "1,2"
        assert params["collections"] == "3"
        assert params["page"] == 2
        assert params["page_size"] == 2
        assert params["no_pagination"] == ""


def test_get_phenotypes(client):
    """Test getting phenotypes with various parameters."""
    mock_response = {"count": 1, "next": None, "previous": None, "results": [{"id": "PH1", "name": "Test"}]}
    
    with patch.object(client, "_get", new_callable=MagicMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = client.get_phenotypes(
            search="diabetes",
            template_id=5,
            tags="1",
            collections="2",
            page=1,
            page_size=1,
        )
        
        assert isinstance(result, PaginatedResponse)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/phenotypes/"
        params = call_args[0][1]
        assert params["search"] == "diabetes"
        assert params["template_id"] == 5
        assert params["tags"] == "1"
        assert params["collections"] == "2"


def test_get_ontology_nodes(client):
    """Test getting ontology nodes."""
    mock_response = {"count": 1, "next": None, "previous": None, "results": [{"id": 1, "reference_id": "MONDO:0001"}]}
    
    with patch.object(client, "_get", new_callable=MagicMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = client.get_ontology_nodes(
            search="heart",
            codes="MONDO:0001",
            exact_codes=True,
            type_ids="1",
            reference_ids="MONDO:0001",
            page=1,
            page_size=1,
        )
        
        assert isinstance(result, PaginatedResponse)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/ontology/node/"
        params = call_args[0][1]
        assert params["search"] == "heart"
        assert params["codes"] == "MONDO:0001"
        assert params["exact_codes"] == ""
        assert params["type_ids"] == "1"
        assert params["reference_ids"] == "MONDO:0001"


def test_paginated_response_model():
    """Test PaginatedResponse model validation."""
    data = {
        "count": 100,
        "next": "https://api/test/?page=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    
    response = PaginatedResponse(**data)
    
    assert response.count == 100
    assert response.next == "https://api/test/?page=2"
    assert response.previous is None
    assert len(response.results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])