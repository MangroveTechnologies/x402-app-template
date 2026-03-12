# x402 App Template

A service template for building APIs that get paid per-call using the [x402 payment protocol](https://www.x402.org/). Built with FastAPI, MCP, and the Coinbase x402 SDK. Deploys to GCP Cloud Run.

An agent calls your API. If the endpoint requires payment, the server responds with HTTP 402 and the payment details. The agent's x402 client signs the payment, retries, and gets the response. No subscriptions, no billing integration, no Stripe. Just HTTP and USDC on Base.

This template gives you a working example of that flow out of the box, plus the scaffolding to build your own x402-enabled service.

## Table of Contents

- [About](#about)
- [Built With](#built-with)
- [Getting Started](#getting-started)
- [Try the x402 Endpoint](#try-the-x402-endpoint)
- [Three-Tier Access Model](#three-tier-access-model)
- [x402 Payment Configuration](#x402-payment-configuration)
- [Discovery and Documentation](#discovery-and-documentation)
- [Architecture](#architecture)
- [Adding Your Own Endpoints](#adding-your-own-endpoints)
- [Full Stack Mode](#full-stack-mode)
- [Deploy to GCP](#deploy-to-gcp)
- [Configuration Reference](#configuration-reference)
- [Project Structure](#project-structure)
- [License](#license)

## About

The x402 protocol (HTTP 402 Payment Required) lets APIs charge per-call using stablecoins. Instead of API keys tied to billing accounts, agents pay directly at the HTTP layer -- the same way they make any other request.

This template demonstrates three access tiers that most APIs need:

- **Free endpoints** -- health checks, documentation, echo. No credentials required.
- **Auth-gated endpoints** -- CRUD operations. Requires an API key (`X-API-Key` header).
- **x402-gated endpoints** -- paid computation. Agents pay per-call in USDC on Base, or get free access with an API key.

The template ships with a working x402-gated endpoint (the "easter egg") that costs $0.05 USDC. It uses the Coinbase facilitator for payment verification and on-chain settlement. Both REST and MCP protocols are served on a single port.

### Built With

- [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/)
- [FastMCP](https://github.com/jlowin/fastmcp) (Streamable HTTP)
- [x402 Python SDK](https://github.com/coinbase/x402) (Coinbase)
- [Terraform](https://www.terraform.io/) (GCP Cloud Run)
- PostgreSQL 16, Redis 7 (optional, via Docker profiles)

## Getting Started

No GCP account required. No database required. Just Docker.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Python 3.11+](https://www.python.org/) (for running tests locally)

### Installation

```bash
git clone https://github.com/MangroveTechnologies/x402-app-template.git my-service
cd my-service
```

Create your local config (gitignored -- your secrets go here):

```bash
cp src/config/local-example-config.json src/config/local-config.json
```

Start the service:

```bash
docker compose up -d --build
```

Verify it's running:

```bash
curl http://localhost:8080/health
```

## Try the x402 Endpoint

The template includes a working x402-gated endpoint at `/api/v1/easter-egg`. This is a real x402 endpoint -- when called without credentials, it responds with HTTP 402 and the payment details an agent needs to pay $0.05 USDC on Base.

**Without credentials** -- see the payment requirements:

```bash
curl -s http://localhost:8080/api/v1/easter-egg | python3 -m json.tool
```

The response includes the network (`eip155:84532`), the USDC contract address, the deposit address, the amount (50000 base units = $0.05), and the facilitator URL. This is everything an x402-enabled client needs to sign a payment and retry the request.

**With an API key** -- subscribers get free access:

```bash
curl -s http://localhost:8080/api/v1/easter-egg -H "X-API-Key: dev-key-1"
```

**With a real x402 payment** -- an agent using the Coinbase x402 SDK handles this automatically. The SDK sees the 402, signs the payment with the agent's wallet, and retries. The facilitator verifies and settles on-chain. See `scripts/test_x402_mainnet.py` for a working example.

## Three-Tier Access Model

| Tier | No credentials | API key | x402 payment |
|------|---------------|---------|-------------|
| **Free** | OK | OK | OK |
| **Auth-gated** | 401 Unauthorized | OK | 401 |
| **x402-gated** | 402 Payment Required | OK (free) | OK (paid) |

API key holders get full access to everything. Public agents pay per-call via x402 for gated endpoints. Free endpoints are always open.

Try all three:

```bash
# Free
curl http://localhost:8080/api/v1/echo?hello=world

# Auth-gated (401 without key, 201 with key)
curl -s http://localhost:8080/api/v1/items
curl -X POST http://localhost:8080/api/v1/items \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-1" \
  -d '{"name":"Widget"}'

# x402-gated (402 without credentials, 200 with key)
curl -s http://localhost:8080/api/v1/easter-egg
curl -s http://localhost:8080/api/v1/easter-egg -H "X-API-Key: dev-key-1"
```

## x402 Payment Configuration

All x402 settings live in the per-environment JSON config files (`src/config/*.json`):

| Key | Description | Testnet | Mainnet |
|-----|-------------|---------|---------|
| `X402_FACILITATOR_URL` | Coinbase facilitator | `https://x402.org/facilitator` | `https://api.cdp.coinbase.com/platform/v2/x402` |
| `X402_NETWORK` | Chain (CAIP-2) | `eip155:84532` (Sepolia) | `eip155:8453` (Base) |
| `X402_PAY_TO` | Your deposit address | `0x...` | `0x...` |
| `X402_USDC_CONTRACT` | USDC token | `0x036CbD...` | `0x833589...` |
| `X402_EASTER_EGG_PRICE` | Price in base units | `50000` ($0.05) | `50000` ($0.05) |
| `X402_CDP_API_KEY_ID` | CDP API key | (empty) | `secret:...:cdp_api_key_id` |
| `X402_CDP_API_KEY_SECRET` | CDP API secret | (empty) | `secret:...:cdp_api_key_secret` |

**Two facilitators:**
- **x402.org** -- No API key needed. Base Sepolia testnet only. Free.
- **CDP** -- Requires CDP API keys from [Coinbase Developer Platform](https://docs.cdp.coinbase.com/). Base mainnet, Solana, Polygon. 1,000 free transactions/month.

The default config uses x402.org (testnet). Switch to CDP for mainnet by updating the config values.

## Discovery and Documentation

All discovery endpoints are free -- no auth required.

### For Agents

| Endpoint | Format | Purpose |
|----------|--------|---------|
| `GET /openapi.json` | OpenAPI 3.0 | Full REST API spec -- routes, parameters, response models |
| `GET /api/v1/docs/tools` | JSON | MCP tool catalog -- names, parameters, access tiers, pricing |

An agent calls these two endpoints to understand the full API before making requests or connecting via MCP.

### For Humans

| Endpoint | Purpose |
|----------|---------|
| `/docs` | Swagger UI -- interactive API explorer |
| `/redoc` | ReDoc -- reference documentation |

## Architecture

```
FastAPI app (port 8080)
  |
  +-- /health                  (free)
  +-- /docs                    (Swagger UI -- for humans)
  +-- /openapi.json            (OpenAPI 3.0 spec -- for agents)
  +-- /api/v1/*                (REST endpoints)
  |     +-- /docs/tools        (MCP tool catalog -- for agents)
  |     +-- /echo              (free -- request reflection)
  |     +-- /items/*           (auth-gated -- CRUD demo)
  |     +-- /easter-egg        (x402-gated -- $0.05 USDC on Base)
  |
  +-- /mcp                     (MCP Streamable HTTP transport)
        +-- echo               (free)
        +-- items_*            (auth-gated)
        +-- easter_egg         (x402-gated)
```

## Adding Your Own Endpoints

### REST endpoint

1. Create `src/api/routes/your_route.py` with a FastAPI `APIRouter`
2. Create `src/services/your_service.py` with business logic
3. Include in `src/api/router.py`:
   ```python
   from src.api.routes.your_route import router as your_router
   api_router.include_router(your_router, tags=["your-tag"])
   ```

Pydantic response models and docstrings are automatically included in the OpenAPI spec and Swagger UI.

### MCP tool

1. Add tool function in `src/mcp/tools.py` inside `register()`:
   ```python
   @server.tool()
   async def your_tool(param: str) -> str:
       """Description for agents."""
       result = your_service_function(param)
       return json.dumps(result)
   ```

2. Add catalog entry for discovery:
   ```python
   register_tool(ToolEntry(
       name="your_tool",
       description="Description for agents.",
       access="free",  # or "auth" or "x402"
       parameters=[ToolParam(name="param", type="string", required=True)],
   ))
   ```

### x402-gated endpoint

Add the route pattern to `x402_routes` in `src/app.py`. The official x402 SDK middleware handles the 402 response, payment verification, and on-chain settlement automatically.

## Full Stack Mode

The default setup runs just the app (no database, no cache). When you need PostgreSQL and Redis:

```bash
cp src/config/local-full-example-config.json src/config/local-config.json
docker compose --profile full up -d --build
```

The `full` profile starts PostgreSQL 16 and Redis 7 alongside the app. The config loader validates that DB and Redis keys are properly configured when they're present in your config file.

## Deploy to GCP

### Bootstrap

When you're ready to deploy, run the bootstrap to replace placeholder values across all Terraform, CI/CD, and config files:

```bash
# For agents (non-interactive):
./init.sh --name my-service --gcp-project my-gcp-project --region us-central1

# For humans (interactive):
./init-interactive.sh
```

### Terraform

```bash
cd infra/terraform
terraform init -backend-config=backend-dev.hcl
terraform plan -var-file=environment-dev.tfvars
terraform apply -var-file=environment-dev.tfvars
```

See `infra/terraform/SETUP.md` for prerequisites (GCP project, Terraform state bucket, OIDC workload identity setup).

### CI/CD

GitHub Actions workflow at `.github/workflows/deploy-cloudrun.yaml`. Manual trigger by default -- uncomment the push or pull_request triggers when ready.

Requires GitHub secrets:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL`

## Configuration Reference

All config lives in per-environment JSON files at `src/config/`. Only two env vars exist: `ENVIRONMENT` (selects which config file to load) and `GCP_PROJECT_ID` (for Secret Manager lookups).

| File | Purpose |
|------|---------|
| `local-example-config.json` | Local dev template (minimal, x402 only) |
| `local-full-example-config.json` | Local dev template (full stack with DB + Redis) |
| `test-config.json` | Used by pytest |
| `dev-config.json` | Development (Secret Manager refs) |
| `prod-config.json` | Production (Secret Manager refs) |

Copy an example to `local-config.json` (gitignored) to get started.

**Key categories** in `configuration-keys.json`:
- **`required`** -- Always validated at startup. App fails without them.
- **`full_app_keys`** -- Validated only if present in your config file. If present but empty, startup fails (catches misconfiguration). If absent, the app runs without those features.

Secret Manager syntax: `"secret:secret-name:property"`

## Project Structure

```
src/
  app.py                    -- FastAPI app, x402 middleware, MCP mount
  config.py                 -- Config singleton (JSON + Secret Manager)
  health.py                 -- Health check
  api/
    router.py               -- REST router (/api/v1)
    routes/
      docs.py               -- MCP tool catalog
      echo.py               -- Free endpoint
      items.py              -- Auth-gated CRUD
      easter_egg.py         -- x402-gated endpoint
  services/
    items.py                -- Items business logic
    easter_egg.py           -- Easter egg message
  mcp/
    server.py               -- FastMCP server
    tools.py                -- MCP tool definitions
    registry.py             -- Tool discovery catalog
  shared/
    types.py                -- Pydantic base model
    auth/middleware.py       -- API key validation
    x402/config.py          -- Payment config (reads from app_config)
    x402/models.py          -- Payment data models
    x402/middleware.py       -- x402 payment decorator
    x402/facilitator.py     -- Facilitator HTTP client
    x402/errors.py          -- Error hierarchy
    db/pool.py              -- PostgreSQL connection
    db/exceptions.py        -- DB error hierarchy
    gcp_secret_utils.py     -- Secret Manager client
  config/                   -- Per-env JSON config files
tests/                      -- 30 tests
infra/terraform/            -- GCP Cloud Run IaC
.github/workflows/          -- CI/CD (manual trigger)
scripts/                    -- x402 payment test scripts
init.sh                     -- Bootstrap for agents
init-interactive.sh         -- Bootstrap for humans
```

## License

Distributed under the MIT License.

## Links

- [x402 Protocol](https://www.x402.org/)
- [Coinbase x402 SDK](https://github.com/coinbase/x402)
- [Coinbase Developer Platform](https://docs.cdp.coinbase.com/x402/welcome)
- [MangroveTechnologies](https://github.com/MangroveTechnologies)
