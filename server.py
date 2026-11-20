"""PhenotypeLibrary MCP server.

Single-file server for the Phenotype Library / Concept Library API
(https://conceptlibrary.saildatabank.com/api/v1/).

Run directly: `python server.py` (streamable-HTTP transport at /mcp,
health check at /health, host/port from the HOST/PORT environment vars).
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

# Line buffering so logs print instantly in cloud control panels
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

load_dotenv()

BASE_URL = os.getenv(
    "PHENOTYPELIBRARY_BASE_URL", "https://conceptlibrary.saildatabank.com/api/v1/"
)
TIMEOUT = float(os.getenv("PHENOTYPELIBRARY_TIMEOUT", "30"))
USERNAME = os.getenv("PHENOTYPELIBRARY_USERNAME")
PASSWORD = os.getenv("PHENOTYPELIBRARY_PASSWORD")


class PaginatedResponse(BaseModel):
    """The API returns either a bare list, DRF-style count/results, or a paged mapping."""

    count: int
    next: str | None = None
    previous: str | None = None
    results: list[dict[str, Any]]


class PhenotypeLibraryClient:
    """Thin sync httpx client for the Phenotype Library API."""

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        auth = httpx.BasicAuth(username, password) if username and password else None
        self.http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            auth=auth,
            headers={"Accept": "application/json"},
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET a path and return parsed JSON."""
        response = self.http.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def list(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET a list endpoint and normalize any of the API's response shapes."""
        data = self.get(path, params)
        if isinstance(data, list):
            return {"count": len(data), "next": None, "previous": None, "results": data}
        if isinstance(data, dict) and "data" in data:
            return {"count": len(data["data"]), "next": None, "previous": None, "results": data["data"]}
        return data

    def close(self) -> None:
        self.http.close()

    @staticmethod
    def normalize_concept_id(concept_id: str) -> str:
        """Return the concept ID in canonical 'C###' form ('714', 'c714', 'C714' -> 'C714')."""
        cid = concept_id.strip()
        if cid.upper().startswith("C"):
            return f"C{cid[1:]}"
        return f"C{cid}"

    @staticmethod
    def normalize_phenotype_id(phenotype_id: str) -> str:
        """Return the phenotype ID in canonical 'PH###' form ('215', 'ph215', 'PH215' -> 'PH215')."""
        pid = phenotype_id.strip().upper()
        return pid if pid.startswith("PH") or pid.startswith("CPH") and False else (
            pid[1:] if pid.startswith("C") and pid[1:3] == "PH" else f"PH{pid}"
        )

    @staticmethod
    def _match_id(raw: str, prefix: str) -> str:
        """Normalize an identifier to '{prefix}<digits>' from any case/prefix variant.

        Handles bare digits ('215'), lowercase ('ph215'), double-prefixed ('CPH215'
        → 'PH215'), and the exact form ('PH215').
        """
        digits = re.sub(r"[^0-9]", "", raw) or re.sub(r"[^0-9]", "", prefix)
        return f"{prefix}{digits}" if digits else raw.strip().upper()


client = PhenotypeLibraryClient(BASE_URL, TIMEOUT, USERNAME, PASSWORD)


from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings

_orig_report_progress = Context.report_progress


def _safe_report_progress(self: Context, *args: Any, **kwargs: Any) -> None:
    """Tolerate the SDK passing 'current' instead of 'progress'; never crash tools."""
    if "current" in kwargs and "progress" not in kwargs:
        kwargs["progress"] = kwargs.pop("current")
    try:
        _orig_report_progress(self, *args, **kwargs)
    except Exception:  # noqa: BLE001, S110 — progress reporting must never crash tools
        pass


Context.report_progress = _safe_report_progress

# Explicit transport security: the SDK auto-enables DNS rebinding protection
# with localhost-only allowed_hosts when transport_security is None AND the
# default host is 127.0.0.1 — which 421s production Host headers (Render's
# phenotypelibrarymcp.onrender.com) and rejects remote clients. Configured
# explicitly here instead: protection on unless env disables it, hosts and
# origins from env so the deployed domain works.
mcp: FastMCP = FastMCP(
    "PhenotypeLibrary",
    instructions=(
        "Tools for the Phenotype Library / Concept Library API. "
        "Use search_phenotypes / search_concepts for discovery, "
        "get_*_detail / get_*_codelist / get_*_versions for codes and "
        "definitions, and search_ontology for MONDO/MeSH/SNOMED/ICD-10 terms."
    ),
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=(
            os.environ.get("MCP_ENABLE_DNS_REBINDING_PROTECTION", "true").lower()
            not in ("false", "0", "no", "off")
        ),
        allowed_hosts=[
            h.strip()
            for h in os.environ.get("MCP_ALLOWED_HOSTS", "phenotypelibrarymcp.onrender.com").split(",")
            if h.strip()
        ],
        allowed_origins=[
            o.strip()
            for o in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",")
            if o.strip()
        ],
    ),
)


def _unwrap(value: Any) -> Any:
    """Detail endpoints return a single-item list; return the item or the value."""
    return value[0] if isinstance(value, list) and len(value) == 1 else value


def _paginate(params: dict[str, Any], page: int, page_size: int) -> dict[str, Any]:
    params["page"] = page
    params["page_size"] = page_size
    return params


# ============================================================
# Phenotypes
# ============================================================

@mcp.tool()
def search_phenotypes(
    search: str | None = None,
    template_id: int | None = None,
    tags: str | None = None,
    collections: str | None = None,
    page: int = 1,
    page_size: int = 1,
    no_pagination: bool = False,
) -> dict[str, Any]:
    """Search phenotype definitions in the Concept Library.

    Args:
        search: Full-text search across phenotype name and description.
        template_id: Filter by template ID.
        tags: Comma-separated list of tag IDs or names.
        collections: Comma-separated list of collection IDs or names.
        page: Page number (default 1).
        page_size: Page size enum (1=20, 2=50, 3=100).
        no_pagination: Disable pagination to get all results.
    """
    params = _paginate({}, page, page_size)
    if search:
        params["search"] = search
    if template_id:
        params["template_id"] = template_id
    if tags:
        params["tags"] = tags
    if collections:
        params["collections"] = collections
    if no_pagination:
        params["no_pagination"] = ""
    return client.list("/phenotypes/", params)


@mcp.tool()
def get_phenotype_detail(phenotype_id: str) -> Any:
    """Get detailed information about a specific phenotype.

    Args:
        phenotype_id: Phenotype ID (e.g., "PH1").
    """
    return _unwrap(client.get(f"/phenotypes/{phenotype_id.strip()}/detail/"))


@mcp.tool()
def get_phenotype_codelist(phenotype_id: str, version_id: str | None = None) -> Any:
    """Get the codelist (clinical codes) for a phenotype.

    Args:
        phenotype_id: Phenotype ID (e.g., "PH1").
        version_id: Optional version ID to get a specific version.
    """
    phenotype_id = phenotype_id.strip()
    if version_id:
        return _unwrap(
            client.get(f"/phenotypes/{phenotype_id}/version/{version_id.strip()}/export/codes/")
        )
    return _unwrap(client.get(f"/phenotypes/{phenotype_id}/export/codes/"))


@mcp.tool()
def get_phenotype_versions(phenotype_id: str) -> Any:
    """Get version history for a phenotype.

    Args:
        phenotype_id: Phenotype ID (e.g., "PH1").
    """
    return _unwrap(client.get(f"/phenotypes/{phenotype_id.strip()}/get-versions/"))


# ============================================================
# Concepts (clinical code lists)
# ============================================================

@mcp.tool()
def search_concepts(
    search: str | None = None,
    tags: str | None = None,
    collections: str | None = None,
    coding_system: str | None = None,
    page: int = 1,
    page_size: int = 1,
    no_pagination: bool = False,
) -> dict[str, Any]:
    """Search for concepts (clinical code lists) in the Concept Library.

    Args:
        search: Full-text search across concept name and description.
        tags: Comma-separated list of tag IDs or names.
        collections: Comma-separated list of collection IDs or names.
        coding_system: Comma-separated list of coding system IDs.
        page: Page number (default 1).
        page_size: Page size enum (1=20, 2=50, 3=100).
        no_pagination: Disable pagination to get all results.
    """
    params = _paginate({}, page, page_size)
    if search:
        params["search"] = search
    if tags:
        params["tags"] = tags
    if collections:
        params["collections"] = collections
    if coding_system:
        params["coding_system"] = coding_system
    if no_pagination:
        params["no_pagination"] = ""
    return client.list("/concepts/", params)


@mcp.tool()
def get_concept_detail(concept_id: str) -> Any:
    """Get detailed information about a specific concept.

    Args:
        concept_id: Concept ID (e.g., "714" or "C714").
    """
    return _unwrap(
        client.get(f"/concepts/{client.normalize_concept_id(concept_id)}/detail/")
    )


@mcp.tool()
def get_concept_codelist(concept_id: str, version_id: str | None = None) -> Any:
    """Get the codelist (clinical codes) for a concept.

    Args:
        concept_id: Concept ID (e.g., "714" or "C714").
        version_id: Optional version ID to get a specific version.
    """
    cid = client.normalize_concept_id(concept_id)
    if version_id:
        return _unwrap(client.get(f"/concepts/{cid}/version/{version_id.strip()}/export/codes/"))
    return _unwrap(client.get(f"/concepts/{cid}/export/codes/"))


@mcp.tool()
def get_concept_versions(concept_id: str) -> Any:
    """Get version history for a concept.

    Args:
        concept_id: Concept ID (e.g., "714" or "C714").
    """
    return _unwrap(client.get(f"/concepts/{client.normalize_concept_id(concept_id)}/get-versions/"))


# ============================================================
# Ontology
# ============================================================

@mcp.tool()
def search_ontology(
    search: str | None = None,
    codes: str | None = None,
    exact_codes: bool = False,
    type_ids: str | None = None,
    reference_ids: str | None = None,
    page: int = 1,
    page_size: int = 1,
) -> dict[str, Any]:
    """Search the ontology (MONDO, MeSH, SNOMED, etc.) for terms.

    Args:
        search: Full-text search across names, descriptions & synonyms.
        codes: Search by codes (e.g., "MONDO:0004995", "MESH:D002309", "ICD10CM:I21").
        exact_codes: If true, search for exact codes instead of fuzzy matching.
        type_ids: Filter by ontology type IDs.
        reference_ids: Filter by vocabulary reference IDs.
        page: Page number (default 1).
        page_size: Page size enum (1=20, 2=50, 3=100).
    """
    params = _paginate({}, page, page_size)
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
    return client.list("/ontology/node/", params)


@mcp.tool()
def get_ontology_groups() -> Any:
    """Get all ontology groups and their root nodes."""
    return _unwrap(client.get("/ontology/"))


@mcp.tool()
def get_ontology_node(term: str) -> Any:
    """Get an ontology node by term/reference_id.

    Args:
        term: Ontology term (e.g., "MONDO:0004995", "MESH:D002309", "SCTID:394579002").
    """
    return _unwrap(client.get(f"/ontology/node/{term.strip()}/"))


@mcp.tool()
def get_ontology_type(ontology_id: str) -> Any:
    """Get ontology group type detail.

    Args:
        ontology_id: The ontology type ID.
    """
    return _unwrap(client.get(f"/ontology/type/{ontology_id.strip()}/"))


# ============================================================
# Collections & tags
# ============================================================

@mcp.tool()
def get_collections(search: str | None = None) -> dict[str, Any]:
    """Get all collections of related phenotypes/concepts.

    Args:
        search: Filter collections by name.
    """
    return client.list("/collections/", {"search": search} if search else None)


@mcp.tool()
def get_collection_detail(collection_id: int) -> Any:
    """Get details of a specific collection.

    Args:
        collection_id: The collection ID.
    """
    return _unwrap(client.get(f"/collections/{collection_id}/detail/"))


@mcp.tool()
def get_tags(search: str | None = None) -> dict[str, Any]:
    """Get all tags used to categorize phenotypes/concepts.

    Args:
        search: Filter tags by name.
    """
    return client.list("/tags/", {"search": search} if search else None)


@mcp.tool()
def get_tag_detail(tag_id: int) -> Any:
    """Get details of a specific tag.

    Args:
        tag_id: The tag ID.
    """
    return _unwrap(client.get(f"/tags/{tag_id}/detail/"))


# ============================================================
# Data sources & templates
# ============================================================

@mcp.tool()
def get_data_sources(search: str | None = None, name: str | None = None) -> dict[str, Any]:
    """Get all data sources (e.g., TPP, NHS Digital).

    Args:
        search: Filter data sources by name/description.
        name: Case-insensitive exact match on the name field.
    """
    params: dict[str, Any] = _paginate({}, 1, 3)
    if search:
        params["search"] = search
    if name:
        params["name"] = name
    return client.list("/data-sources/", params)


@mcp.tool()
def get_data_source_detail(datasource_id: str) -> Any:
    """Get details of a specific data source.

    Args:
        datasource_id: The data source ID or UUID.
    """
    return _unwrap(client.get(f"/data-sources/{datasource_id.strip()}/detail/"))


@mcp.tool()
def get_templates(search: str | None = None) -> dict[str, Any]:
    """Get all templates.

    Args:
        search: Filter templates by name/description.
    """
    return client.list("/templates/", {"search": search} if search else None)


@mcp.tool()
def get_template_detail(template_id: int) -> Any:
    """Get details of a specific template.

    Args:
        template_id: The template ID.
    """
    return _unwrap(client.get(f"/templates/{template_id}/detail/"))


@mcp.tool()
def get_template_versions(template_id: int) -> Any:
    """Get version history for a template.

    Args:
        template_id: The template ID.
    """
    return _unwrap(client.get(f"/templates/{template_id}/get-versions/"))


# =============================================================================
# Health check (custom route, separate from the MCP path)
# =============================================================================

from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    """Health check endpoint for hosting platforms (Render)."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "phenotypelibrary-mcp",
            "mcp_endpoint": "/mcp",
        }
    )


# =============================================================================
# Main entry point — streamable HTTP transport
# =============================================================================

def main() -> None:
    """Serve the streamable-HTTP MCP transport at /mcp, binding env HOST/PORT."""
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    # Set before run() — settings are consumed when the server binds and
    # run_streamable_http_async reads host/port from mcp.settings at serve time.
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()