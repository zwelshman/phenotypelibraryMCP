"""Entry point for the PhenotypeLibrary MCP Server."""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from phenotypelibrary_mcp import server as server_module
from phenotypelibrary_mcp.server import mcp

__all__ = ["main", "mcp"]


def main():
    """Run the MCP server, honoring --transport/--host/--port CLI arguments.

    Kept in sync with server.parse_args so `phenotypelibrary-mcp` (the console
    script declared in pyproject.toml) behaves like `python -m ...` invocations.
    """
    args = server_module.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        import uvicorn

        uvicorn.run(
            server_module.app,
            host=args.host,
            port=args.port,
            timeout_keep_alive=300,
        )


if __name__ == "__main__":
    main()