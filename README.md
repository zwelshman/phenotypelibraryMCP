# PhenotypeLibrary MCP Server

A Model Context Protocol (MCP) server for the [Phenotype Library / Concept Library API](https://conceptlibrary.saildatabank.com/api/v1/).

This server provides access to clinical code lists, phenotypes, ontology terms, and other research metadata from the SAIL Databank Concept Library.

## Features

- **Phenotypes**: Search and retrieve phenotype definitions, codelists, and version history
- **Concepts**: Search and retrieve clinical code lists (concepts), codelists, and version history
- **Ontology**: Search ontology terms (MONDO, MeSH, SNOMED CT, ICD-10, etc.)
- **Collections**: Browse collections of phenotypes/concepts
- **Tags**: Browse tags for categorization
- **Data Sources**: Access data source metadata
- **Templates**: Browse phenotype templates

## Installation

```bash
# Install from source
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file with your configuration:

```env
# API Configuration
PHENOTYPELIBRARY_BASE_URL=https://conceptlibrary.saildatabank.com/api/v1/
PHENOTYPELIBRARY_TIMEOUT=30.0

# Optional: Authentication (for private data)
PHENOTYPELIBRARY_USERNAME=your_username
PHENOTYPELIBRARY_PASSWORD=your_password
```

### Available Domains

- **SAIL** (default): `https://conceptlibrary.saildatabank.com/api/v1/`
- **HDRUK**: `https://phenotypes.healthdatagateway.org/api/v1/`
- **Demo**: `https://conceptlibrary.demo-dev.saildatabank.com/api/v1/`
- **ADP**: `https://conceptlibrary.saildatabank.com/ADP/api/v1/`
- **Gateway**: `https://conceptlibrary.serp.ac.uk/api/v1/`

## Deployment

### Render (Web Service)

1. Connect your GitHub repository to Render
2. Create a new **Web Service**
3. Use the `render.yaml` configuration file (or manually configure):
   - **Build Command**: `pip install -e .`
   - **Start Command**: `python server.py`
   - **Health Check Path**: `/health`
4. Add environment variables:
   - `PHENOTYPELIBRARY_BASE_URL` (optional, defaults to SAIL)
   - `PHENOTYPELIBRARY_TIMEOUT` (optional, defaults to 30.0)
   - `PHENOTYPELIBRARY_USERNAME` (optional, for private data)
   - `PHENOTYPELIBRARY_PASSWORD` (optional, for private data)
   - `MCP_ALLOWED_HOSTS` (comma-separated Host values the transport accepts; includes your deployed domain, e.g. `phenotypelibrarymcp.onrender.com`)
   - `MCP_ALLOWED_ORIGINS` (optional, comma-separated browser Origin values)
   - `MCP_ENABLE_DNS_REBINDING_PROTECTION` (optional, `true` by default; set `false` to disable Host/Origin validation)

### MCP Endpoint

Once deployed, the MCP server will be available at:
- **Streamable HTTP Endpoint**: `https://your-app.onrender.com/mcp`
- **Health Check**: `https://your-app.onrender.com/health`

### Docker Compose

_Deprecated_ — Docker files were removed from this project; use the pip
install + `python server.py` flow above instead.

## Usage

### Running the Server

```bash
# Streamable HTTP transport (binds $HOST/$PORT, defaults 0.0.0.0:8000)
python server.py

# Or use the console script
phenotypelibrary-mcp
```

> **Local testing note:** DNS rebinding protection is on by default and only accepts
> hosts listed in `MCP_ALLOWED_HOSTS` (default: `phenotypelibrarymcp.onrender.com`).
> For local testing, set `MCP_ALLOWED_HOSTS=localhost:*,127.0.0.1:*`.

### Using with MCP Inspector

```bash
# Test with MCP Inspector (streamable HTTP transport)
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### Using with MCP Clients

Add to your MCP client config (Cursor, Claude Desktop, etc.):

```json
{
  "mcpServers": {
    "phenotypelibrary": {
      "url": "https://phenotypelibrarymcp.onrender.com/mcp"
    }
  }
}
```

### Available Tools

#### Phenotypes
- `search_phenotypes` - Search phenotypes with filters
- `get_phenotype_detail` - Get detailed phenotype information
- `get_phenotype_codelist` - Get clinical codes for a phenotype
- `get_phenotype_versions` - Get version history

#### Concepts
- `search_concepts` - Search concepts (clinical code lists)
- `get_concept_detail` - Get detailed concept information
- `get_concept_codelist` - Get clinical codes for a concept
- `get_concept_versions` - Get version history

#### Ontology
- `search_ontology` - Search ontology terms
- `get_ontology_node` - Get specific ontology node by term
- `get_ontology_groups` - Get all ontology groups
- `get_ontology_type` - Get ontology type details

#### Collections & Tags
- `get_collections` - List all collections
- `get_collection_detail` - Get collection details
- `get_tags` - List all tags
- `get_tag_detail` - Get tag details

#### Data Sources & Templates
- `get_data_sources` - List data sources
- `get_data_source_detail` - Get data source details
- `get_templates` - List templates
- `get_template_detail` - Get template details
- `get_template_versions` - Get template version history

### Example Usage

```python
# Search for asthma phenotypes
result = await search_phenotypes(search="asthma")

# Get phenotype detail
detail = await get_phenotype_detail("PH1")

# Get codelist for a phenotype
codelist = await get_phenotype_codelist("PH1")

# Search ontology for diabetes terms
ontology = await search_ontology(search="diabetes")

# Get specific ontology node
node = await get_ontology_node("MONDO:0005148")
```

## API Response Handling

The Concept Library API returns varying response shapes. `client.list()`
normalizes them all to a single form:

- **Bare JSON array** → wrapped into `{"count": N, "next": null, "previous": null, "results": [...]}`
- **Paged mapping** (`page`/`total_pages`/`data`) → `data` becomes `results`
- **DRF-style mapping** (`count`/`next`/`previous`/`results`) → passed through as-is

Detail endpoints return a single-item list; the tools unwrap it to the item.
All ID parameters are stripped of whitespace, and concept IDs get a `C` prefix
(normalized via `PhenotypeLibraryClient.normalize_concept_id`).

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## License

GPL-3.0 - See LICENSE file for details.

## References

- [Concept Library Website](https://conceptlibrary.saildatabank.com/)
- [API Documentation](https://conceptlibrary.saildatabank.com/api/v1/)
- [Python Client](https://github.com/SwanseaUniversityMedical/pyconceptlibraryclient)
- [R Client](https://github.com/SwanseaUniversityMedical/concept-library-client-r)
- [GitHub Repository](https://github.com/SwanseaUniversityMedical/concept-library)