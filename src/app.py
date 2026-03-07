"""FastAPI application factory.

Serves dual protocols on a single port:
- REST API at /api/v1/* with OpenAPI 3.0 docs at /docs and /openapi.json
- MCP server at /mcp (Streamable HTTP transport)

Auto-documentation:
- Swagger UI: /docs (for humans)
- OpenAPI spec: /openapi.json (for agents)
- MCP tool catalog: /api/v1/docs/tools (for agents)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.health import health_payload
from src.api.router import api_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Mount MCP server
    from src.mcp.server import create_mcp_server
    mcp_server = create_mcp_server()
    application.mount("/mcp", mcp_server.streamable_http_app())
    yield


app = FastAPI(
    title="GCP App Template",
    description=(
        "FastAPI + MCP service template with three-tier access control.\n\n"
        "## For Agents\n\n"
        "- **REST discovery**: GET `/openapi.json` for the full OpenAPI 3.0 spec\n"
        "- **MCP tool catalog**: GET `/api/v1/docs/tools` for tool names, parameters, access tiers, and pricing\n"
        "- **MCP endpoint**: Connect to `/mcp` via Streamable HTTP transport\n\n"
        "## Access Tiers\n\n"
        "| Tier | How to access |\n"
        "|------|---------------|\n"
        "| Free | No credentials needed |\n"
        "| Auth | `X-API-Key` header |\n"
        "| x402 | Payment via x402 protocol (or API key for free access) |\n"
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "discovery", "description": "API and tool discovery endpoints (free, no auth)"},
        {"name": "echo", "description": "Echo/reflect endpoints (free, no auth)"},
        {"name": "items", "description": "Items CRUD (auth-gated, requires API key)"},
        {"name": "easter-egg", "description": "Easter egg endpoint (x402-gated, $0.05 USDC on Base)"},
    ],
)

app.include_router(api_router)


@app.get(
    "/health",
    summary="Health check",
    description="Returns service health status and timestamp. Free, no auth required.",
    tags=["discovery"],
)
async def health():
    return health_payload()
