"""Entry point for the PhenotypeLibrary MCP Server."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from phenotypelibrary_mcp.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run()