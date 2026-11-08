"""Main MCP Server for PhenotypeLibrary/Concept Library API."""

import os
import argparse
from typing import Any, Optional
from dataclasses import dataclass

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Load environment variables
load_dotenv()


# Configuration
@dataclass
class Config:
    """Configuration for the PhenotypeLibrary API client."""
    base_url: str = os.getenv("PHENOTYPELIBRARY_BASE_URL", "https://conceptlibrary.saildatabank.com/api/v1/")
    timeout: float = float(os.getenv("PHENOTYPELIBRARY_TIMEOUT", "30.0"))
    username: Optional[str] = os.getenv("PHENOTYPELIBRARY_USERNAME")
    password: Optional[str] = os.getenv("PHENOTYPELIBRARY_PASSWORD")


# Global config instance
config = Config()


# Health check endpoint for Render
async def health_check(request):
    """Health check endpoint for Render."""
    return JSONResponse({"status": "healthy", "service": "phenotypelibrary-mcp"})


def create_app():
    """Create the Starlette app with MCP and health check."""
    app = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
        ]
    )
    return app


# Pydantic models for API responses
class PaginatedResponse(BaseModel):
    """Base model for paginated API responses."""
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[dict[str, Any]]


class Collection(BaseModel):
    """Collection model."""
    id: int
    name: str
    description: Optional[str] = None
    created: str
    modified: str


class Tag(BaseModel):
    """Tag model."""
    id: int
    name: str
    description: Optional[str] = None
    created: str
    modified: str


class DataSource(BaseModel):
    """Data source model."""
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    datasource_id: Optional[str] = None
    uid: Optional[str] = None
    created: str
    modified: str


class Concept(BaseModel):
    """Concept model."""
    id: str
    name: str
    description: Optional[str] = None
    coding_system: Optional[dict] = None
    owner: Optional[dict] = None
    organisation: Optional[dict] = None
    tags: list[dict] = Field(default_factory=list)
    collections: list[dict] = Field(default_factory=list)
    created: str
    modified: str
    version: Optional[int] = None


class Phenotype(BaseModel):
    """Phenotype model."""
    id: str
    name: str
    description: Optional[str] = None
    template: Optional[dict] = None
    owner: Optional[dict] = None
    organisation: Optional[dict] = None
    tags: list[dict] = Field(default_factory=list)
    collections: list[dict] = Field(default_factory=list)
    created: str
    modified: str
    version: Optional[int] = None


class OntologyNode(BaseModel):
    """Ontology node model."""
    id: int
    reference_id: str
    name: str
    description: Optional[str] = None
    type: Optional[dict] = None
    parent: Optional[int] = None
    children: list[int] = Field(default_factory=list)
    mappings: list[dict] = Field(default_factory=list)


class Template(BaseModel):
    """Template model."""
    id: int
    name: str
    description: Optional[str] = None
    fields: list[dict] = Field(default_factory=list)
    created: str
    modified: str


# API Client
class PhenotypeLibraryClient:
    """Client for interacting with the PhenotypeLibrary/Concept Library API."""

    def __init__(self, config: Config):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            auth = None
            if self.config.username and self.config.password:
                auth = httpx.BasicAuth(self.config.username, self.config.password)
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                auth=auth,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make a GET request to the API."""
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    # Collections
    async def get_collections(self, search: Optional[str] = None, id: Optional[str] = None) -> PaginatedResponse:
        """Get all collections."""
        params = {}
        if search:
            params["search"] = search
        if id:
            params["id"] = id
        data = await self._get("/collections/", params)
        return PaginatedResponse(**data)

    async def get_collection_detail(self, collection_id: int) -> dict[str, Any]:
        """Get detail of a specific collection."""
        return await self._get(f"/collections/{collection_id}/detail/")

    # Tags
    async def get_tags(self, search: Optional[str] = None, id: Optional[str] = None) -> PaginatedResponse:
        """Get all tags."""
        params = {}
        if search:
            params["search"] = search
        if id:
            params["id"] = id
        data = await self._get("/tags/", params)
        return PaginatedResponse(**data)

    async def get_tag_detail(self, tag_id: int) -> dict[str, Any]:
        """Get detail of a specific tag."""
        return await self._get(f"/tags/{tag_id}/detail/")

    # Data Sources
    async def get_data_sources(
        self,
        search: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        datasource_id: Optional[str] = None,
        url: Optional[str] = None,
        source: Optional[str] = None,
    ) -> PaginatedResponse:
        """Get all data sources."""
        params = {}
        if search:
            params["search"] = search
        if id:
            params["id"] = id
        if name:
            params["name"] = name
        if uid:
            params["uid"] = uid
        if datasource_id:
            params["datasource_id"] = datasource_id
        if url:
            params["url"] = url
        if source:
            params["source"] = source
        data = await self._get("/data-sources/", params)
        return PaginatedResponse(**data)

    async def get_data_source_detail(self, datasource_id: str) -> dict[str, Any]:
        """Get detail of a specific data source."""
        return await self._get(f"/data-sources/{datasource_id}/detail/")

    async def get_data_source_export(self, datasource_id: str) -> dict[str, Any]:
        """Export a specific data source."""
        return await self._get(f"/data-sources/{datasource_id}/export/")

    # Concepts
    async def get_concepts(
        self,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 1,
        no_pagination: bool = False,
        phenotype_id: Optional[str] = None,
        phenotype_owner: Optional[str] = None,
        tags: Optional[str] = None,
        collections: Optional[str] = None,
        coding_system: Optional[str] = None,
        owner: Optional[str] = None,
        organisation: Optional[str] = None,
    ) -> PaginatedResponse:
        """Get all concepts with optional filtering."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if no_pagination:
            params["no_pagination"] = ""
        if phenotype_id:
            params["phenotype_id"] = phenotype_id
        if phenotype_owner:
            params["phenotype_owner"] = phenotype_owner
        if tags:
            params["tags"] = tags
        if collections:
            params["collections"] = collections
        if coding_system:
            params["coding_system"] = coding_system
        if owner:
            params["owner"] = owner
        if organisation:
            params["organisation"] = organisation
        data = await self._get("/concepts/", params)
        return PaginatedResponse(**data)

    async def get_concept_detail(self, concept_id: str) -> dict[str, Any]:
        """Get detail of a specific concept."""
        return await self._get(f"/concepts/C{concept_id}/detail/")

    async def get_concept_codelist(self, concept_id: str) -> dict[str, Any]:
        """Export codes for a specific concept."""
        return await self._get(f"/concepts/C{concept_id}/export/codes/")

    async def get_concept_component_data(self, concept_id: str) -> dict[str, Any]:
        """Export component data for a specific concept."""
        return await self._get(f"/concepts/C{concept_id}/export/component-data/")

    async def get_concept_versions(self, concept_id: str) -> dict[str, Any]:
        """Get version history of a specific concept."""
        return await self._get(f"/concepts/C{concept_id}/get-versions/")

    async def get_concept_version_detail(self, concept_id: str, version_id: str) -> dict[str, Any]:
        """Get detail of a specific concept version."""
        return await self._get(f"/concepts/C{concept_id}/version/{version_id}/detail/")

    async def get_concept_version_codelist(self, concept_id: str, version_id: str) -> dict[str, Any]:
        """Export codes for a specific concept version."""
        return await self._get(f"/concepts/C{concept_id}/version/{version_id}/export/codes/")

    async def get_concept_version_component_data(self, concept_id: str, version_id: str) -> dict[str, Any]:
        """Export component data for a specific concept version."""
        return await self._get(f"/concepts/C{concept_id}/version/{version_id}/export/component-data/")

    # Phenotypes
    async def get_phenotypes(
        self,
        search: Optional[str] = None,
        template_id: Optional[int] = None,
        template_version_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 1,
        no_pagination: bool = False,
        tags: Optional[str] = None,
        collections: Optional[str] = None,
        created: Optional[str] = None,
    ) -> PaginatedResponse:
        """Get all phenotypes with optional filtering."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if template_id:
            params["template_id"] = template_id
        if template_version_id:
            params["template_version_id"] = template_version_id
        if no_pagination:
            params["no_pagination"] = ""
        if tags:
            params["tags"] = tags
        if collections:
            params["collections"] = collections
        if created:
            params["created"] = created
        data = await self._get("/phenotypes/", params)
        return PaginatedResponse(**data)

    async def get_phenotype_detail(self, phenotype_id: str) -> dict[str, Any]:
        """Get detail of a specific phenotype."""
        return await self._get(f"/phenotypes/{phenotype_id}/detail/")

    async def get_phenotype_export(self, phenotype_id: str, field: str) -> dict[str, Any]:
        """Export a specific field of a phenotype."""
        return await self._get(f"/phenotypes/{phenotype_id}/export/{field}/")

    async def get_phenotype_versions(self, phenotype_id: str) -> dict[str, Any]:
        """Get version history of a specific phenotype."""
        return await self._get(f"/phenotypes/{phenotype_id}/get-versions/")

    async def get_phenotype_version_detail(self, phenotype_id: str, version_id: str) -> dict[str, Any]:
        """Get detail of a specific phenotype version."""
        return await self._get(f"/phenotypes/{phenotype_id}/version/{version_id}/detail/")

    async def get_phenotype_version_export(self, phenotype_id: str, version_id: str, field: str) -> dict[str, Any]:
        """Export a specific field of a phenotype version."""
        return await self._get(f"/phenotypes/{phenotype_id}/version/{version_id}/export/{field}/")

    # Ontology
    async def get_ontology_groups(self) -> dict[str, Any]:
        """Get all ontology groups and their root nodes."""
        return await self._get("/ontology/")

    async def get_ontology_nodes(
        self,
        search: Optional[str] = None,
        codes: Optional[str] = None,
        exact_codes: bool = False,
        type_ids: Optional[str] = None,
        reference_ids: Optional[str] = None,
        page: int = 1,
        page_size: int = 1,
    ) -> PaginatedResponse:
        """Query ontology nodes."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        if codes:
            params["codes"] = codes
        if exact_codes:
            params["exact_codes"] = ""
        if type_ids:
            params["type_ids"] = type_ids
        if reference_ids:
            params["reference_ids"] = reference_ids
        data = await self._get("/ontology/node/", params)
        return PaginatedResponse(**data)

    async def get_ontology_node_by_id(self, node_id: str) -> dict[str, Any]:
        """Get an ontology node by ID."""
        return await self._get(f"/ontology/node/{node_id}/")

    async def get_ontology_node_by_term(self, term: str) -> dict[str, Any]:
        """Get an ontology node by term/reference_id."""
        return await self._get(f"/ontology/node/{term}/")

    async def get_ontology_type(self, ontology_id: str) -> dict[str, Any]:
        """Get ontology group type detail."""
        return await self._get(f"/ontology/type/{ontology_id}/")

    # Templates
    async def get_templates(
        self,
        search: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> PaginatedResponse:
        """Get all templates."""
        params = {}
        if search:
            params["search"] = search
        if id:
            params["id"] = id
        if name:
            params["name"] = name
        data = await self._get("/templates/", params)
        return PaginatedResponse(**data)

    async def get_template_detail(self, template_id: int) -> dict[str, Any]:
        """Get detail of a specific template."""
        return await self._get(f"/templates/{template_id}/detail/")

    async def get_template_versions(self, template_id: int) -> dict[str, Any]:
        """Get version history of a specific template."""
        return await self._get(f"/templates/{template_id}/get-versions/")

    async def get_template_version_detail(self, template_id: int, version_id: str) -> dict[str, Any]:
        """Get detail of a specific template version."""
        return await self._get(f"/templates/{template_id}/version/{version_id}/detail/")


# Create the MCP server
mcp = FastMCP("PhenotypeLibrary")

# Initialize the client
client = PhenotypeLibraryClient(config)


@mcp.tool()
async def search_phenotypes(
    search: Optional[str] = None,
    template_id: Optional[int] = None,
    tags: Optional[str] = None,
    collections: Optional[str] = None,
    page: int = 1,
    page_size: int = 1,
    no_pagination: bool = False,
) -> dict[str, Any]:
    """
    Search for phenotypes in the Concept Library.
    
    Args:
        search: Full-text search across phenotype name and description
        template_id: Filter by template ID
        tags: Comma-separated list of tag IDs or names
        collections: Comma-separated list of collection IDs or names
        page: Page number (default: 1)
        page_size: Page size enum (1=20, 2=50, 3=100)
        no_pagination: Disable pagination to get all results
    """
    result = await client.get_phenotypes(
        search=search,
        template_id=template_id,
        tags=tags,
        collections=collections,
        page=page,
        page_size=page_size,
        no_pagination=no_pagination,
    )
    return result.model_dump()


@mcp.tool()
async def get_phenotype_detail(phenotype_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific phenotype.
    
    Args:
        phenotype_id: The phenotype ID (e.g., "PH1")
    """
    return await client.get_phenotype_detail(phenotype_id)


@mcp.tool()
async def get_phenotype_codelist(phenotype_id: str, version_id: Optional[str] = None) -> dict[str, Any]:
    """
    Get the codelist (clinical codes) for a phenotype.
    
    Args:
        phenotype_id: The phenotype ID (e.g., "PH1")
        version_id: Optional version ID to get a specific version
    """
    if version_id:
        return await client.get_phenotype_version_export(phenotype_id, version_id, "codes")
    return await client.get_phenotype_export(phenotype_id, "codes")


@mcp.tool()
async def get_phenotype_versions(phenotype_id: str) -> dict[str, Any]:
    """
    Get version history for a phenotype.
    
    Args:
        phenotype_id: The phenotype ID (e.g., "PH1")
    """
    return await client.get_phenotype_versions(phenotype_id)


@mcp.tool()
async def search_concepts(
    search: Optional[str] = None,
    tags: Optional[str] = None,
    collections: Optional[str] = None,
    coding_system: Optional[str] = None,
    page: int = 1,
    page_size: int = 1,
    no_pagination: bool = False,
) -> dict[str, Any]:
    """
    Search for concepts (clinical code lists) in the Concept Library.
    
    Args:
        search: Full-text search across concept name and description
        tags: Comma-separated list of tag IDs
        collections: Comma-separated list of collection IDs
        coding_system: Comma-separated list of coding system IDs
        page: Page number (default: 1)
        page_size: Page size enum (1=20, 2=50, 3=100)
        no_pagination: Disable pagination to get all results
    """
    result = await client.get_concepts(
        search=search,
        tags=tags,
        collections=collections,
        coding_system=coding_system,
        page=page,
        page_size=page_size,
        no_pagination=no_pagination,
    )
    return result.model_dump()


@mcp.tool()
async def get_concept_detail(concept_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific concept.
    
    Args:
        concept_id: The concept ID (e.g., "C714")
    """
    return await client.get_concept_detail(concept_id)


@mcp.tool()
async def get_concept_codelist(concept_id: str, version_id: Optional[str] = None) -> dict[str, Any]:
    """
    Get the codelist (clinical codes) for a concept.
    
    Args:
        concept_id: The concept ID (e.g., "C714")
        version_id: Optional version ID to get a specific version
    """
    if version_id:
        return await client.get_concept_version_codelist(concept_id, version_id)
    return await client.get_concept_codelist(concept_id)


@mcp.tool()
async def get_concept_versions(concept_id: str) -> dict[str, Any]:
    """
    Get version history for a concept.
    
    Args:
        concept_id: The concept ID (e.g., "C714")
    """
    return await client.get_concept_versions(concept_id)


@mcp.tool()
async def search_ontology(
    search: Optional[str] = None,
    codes: Optional[str] = None,
    exact_codes: bool = False,
    type_ids: Optional[str] = None,
    reference_ids: Optional[str] = None,
    page: int = 1,
    page_size: int = 1,
) -> dict[str, Any]:
    """
    Search the ontology (MONDO, MeSH, SNOMED, etc.) for terms.
    
    Args:
        search: Full-text search across names, descriptions & synonyms
        codes: Search by codes (e.g., "MONDO:0004995", "MESH:D002309", "ICD10CM:I21")
        exact_codes: If true, search for exact codes instead of fuzzy matching
        type_ids: Filter by ontology type IDs
        reference_ids: Filter by vocabulary reference IDs
        page: Page number (default: 1)
        page_size: Page size enum (1=20, 2=50, 3=100)
    """
    result = await client.get_ontology_nodes(
        search=search,
        codes=codes,
        exact_codes=exact_codes,
        type_ids=type_ids,
        reference_ids=reference_ids,
        page=page,
        page_size=page_size,
    )
    return result.model_dump()


@mcp.tool()
async def get_ontology_node(term: str) -> dict[str, Any]:
    """
    Get an ontology node by term/reference_id.
    
    Args:
        term: The ontology term (e.g., "MONDO:0004995", "MESH:D002309", "SCTID:394579002")
    """
    return await client.get_ontology_node_by_term(term)


@mcp.tool()
async def get_ontology_groups() -> dict[str, Any]:
    """Get all ontology groups and their root nodes."""
    return await client.get_ontology_groups()


@mcp.tool()
async def get_ontology_type(ontology_id: str) -> dict[str, Any]:
    """
    Get ontology group type detail.
    
    Args:
        ontology_id: The ontology type ID
    """
    return await client.get_ontology_type(ontology_id)


@mcp.tool()
async def get_collections(search: Optional[str] = None) -> dict[str, Any]:
    """
    Get all collections.
    
    Args:
        search: Full-text search across collection name
    """
    result = await client.get_collections(search=search)
    return result.model_dump()


@mcp.tool()
async def get_collection_detail(collection_id: int) -> dict[str, Any]:
    """
    Get detail of a specific collection.
    
    Args:
        collection_id: The collection ID
    """
    return await client.get_collection_detail(collection_id)


@mcp.tool()
async def get_tags(search: Optional[str] = None) -> dict[str, Any]:
    """
    Get all tags.
    
    Args:
        search: Full-text search across tag name
    """
    result = await client.get_tags(search=search)
    return result.model_dump()


@mcp.tool()
async def get_tag_detail(tag_id: int) -> dict[str, Any]:
    """
    Get detail of a specific tag.
    
    Args:
        tag_id: The tag ID
    """
    return await client.get_tag_detail(tag_id)


@mcp.tool()
async def get_data_sources(
    search: Optional[str] = None,
    name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get all data sources.
    
    Args:
        search: Full-text search across name and description
        name: Case insensitive direct match of name field
    """
    result = await client.get_data_sources(search=search, name=name)
    return result.model_dump()


@mcp.tool()
async def get_data_source_detail(datasource_id: str) -> dict[str, Any]:
    """
    Get detail of a specific data source.
    
    Args:
        datasource_id: The data source ID or UUID
    """
    return await client.get_data_source_detail(datasource_id)


@mcp.tool()
async def get_templates(search: Optional[str] = None) -> dict[str, Any]:
    """
    Get all templates.
    
    Args:
        search: Full-text search across template name and description
    """
    result = await client.get_templates(search=search)
    return result.model_dump()


@mcp.tool()
async def get_template_detail(template_id: int) -> dict[str, Any]:
    """
    Get detail of a specific template.
    
    Args:
        template_id: The template ID
    """
    return await client.get_template_detail(template_id)


@mcp.tool()
async def get_template_versions(template_id: int) -> dict[str, Any]:
    """
    Get version history for a template.
    
    Args:
        template_id: The template ID
    """
    return await client.get_template_versions(template_id)


# Resource endpoints
@mcp.resource("phenotype://{phenotype_id}")
async def phenotype_resource(phenotype_id: str) -> str:
    """Get a phenotype as a resource."""
    detail = await client.get_phenotype_detail(phenotype_id)
    return str(detail)


@mcp.resource("concept://{concept_id}")
async def concept_resource(concept_id: str) -> str:
    """Get a concept as a resource."""
    detail = await client.get_concept_detail(concept_id)
    return str(detail)


@mcp.resource("ontology://{term}")
async def ontology_resource(term: str) -> str:
    """Get an ontology node as a resource."""
    detail = await client.get_ontology_node_by_term(term)
    return str(detail)


# Prompts
@mcp.prompt()
def phenotype_search_prompt(condition: str) -> str:
    """Generate a prompt for searching phenotypes related to a condition."""
    return f"Search for phenotypes related to {condition} in the Concept Library. Use the search_phenotypes tool with search='{condition}'."


@mcp.prompt()
def concept_search_prompt(condition: str) -> str:
    """Generate a prompt for searching concepts related to a condition."""
    return f"Search for clinical code lists (concepts) related to {condition} in the Concept Library. Use the search_concepts tool with search='{condition}'."


@mcp.prompt()
def ontology_search_prompt(term: str) -> str:
    """Generate a prompt for searching ontology terms."""
    return f"Search the ontology for terms related to {term}. Use the search_ontology tool with search='{term}'."


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PhenotypeLibrary MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.transport == "stdio":
        mcp.run()
    else:
        # For HTTP transports, we need to run with uvicorn
        import uvicorn
        from mcp.server.streamable_http import create_streamable_http_app
        from mcp.server.sse import create_sse_app
        
        if args.transport == "streamable-http":
            app = create_streamable_http_app(mcp)
        elif args.transport == "sse":
            app = create_sse_app(mcp)
        
        # Add health check route
        app.router.routes.insert(0, Route("/health", health_check, methods=["GET"]))
        
        uvicorn.run(app, host=args.host, port=args.port)