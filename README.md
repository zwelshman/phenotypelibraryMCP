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
   - **Start Command**: `python -m phenotypelibrary_mcp.server --transport sse --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add environment variables:
   - `PHENOTYPELIBRARY_BASE_URL` (optional, defaults to SAIL)
   - `PHENOTYPELIBRARY_TIMEOUT` (optional, defaults to 30.0)
   - `PHENOTYPELIBRARY_USERNAME` (optional, for private data)
   - `PHENOTYPELIBRARY_PASSWORD` (optional, for private data)

### MCP Endpoint

Once deployed, the MCP server will be available at:
- **SSE Endpoint**: `https://your-app.onrender.com/mcp/sse`
- **Health Check**: `https://your-app.onrender.com/health`

### Docker

```bash
# Build the image
docker build -t phenotypelibrary-mcp .

# Run the container
docker run -p 8000:8000 \
  -e PHENOTYPELIBRARY_BASE_URL=https://conceptlibrary.saildatabank.com/api/v1/ \
  phenotypelibrary-mcp
```

### Docker Compose

```bash
docker-compose up -d
```

## Usage

### Running the Server

```bash
# Run with stdio transport (for MCP clients)
python -m phenotypelibrary_mcp.server

# Or use the entry point
phenotypelibrary-mcp
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

## Resources

The server also exposes resources:
- `phenotype://{phenotype_id}` - Phenotype details
- `concept://{concept_id}` - Concept details
- `ontology://{term}` - Ontology node details

## Prompts

Pre-built prompts for common tasks:
- `phenotype_search_prompt(condition)` - Search phenotypes for a condition
- `concept_search_prompt(condition)` - Search concepts for a condition
- `ontology_search_prompt(term)` - Search ontology for a term

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