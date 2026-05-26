# OmniFrame

OmniFrame is an agentic "CAD for Thought" prototype. A user enters a business, engineering, product, personal, or strategy goal; the backend builds a domain brief, routes it to a live framework, and the frontend generates an editable visual canvas.

## Live Routes

- SWOT: strategic baseline audit
- Lean Startup: Build-Measure-Learn validation loops
- OKRs: measurable alignment and operating cadence
- Porter's Five Forces: industry pressure analysis
- PESTLE: macro-environment analysis
- RICE: product and roadmap prioritization
- TRIZ: engineering contradiction solving

The full 50-framework reference catalog lives at `backend/app/data/framework_catalog.json` and is exposed through the Framework Library UI. Future frameworks are visible but locked.

## Analysis Skills

Framework and domain reasoning is configured through markdown skills in `backend/app/skills/`.

- `domain_analyst.md` extracts the subject model for any prompt.
- `context_accumulator.md` keeps regeneration tied to the original prompt plus the user's current layer edits.
- `frameworks/*.md` defines professional expectations for each live framework.

These files are loaded into inference prompts so examples do not have to be hardcoded in Python.

## Local Development

The whole project runs in Docker — Postgres, the FastAPI backend (hot-reloaded by uvicorn), and the Vite dev server with hot reload. No host Node/Python toolchain is required.

```bash
cp .env.example .env      # add OPENAI_API_KEY / GEMINI_API_KEY if you have them
docker compose up
```

Open:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health

Source is bind-mounted, so edits under `src/` and `backend/` reload live, and Alembic migrations run automatically on backend startup. Host port `8000` must be free (it conflicts with any other local stack published on `:8000`).

## LLM Analysis

The deterministic fallback works without credentials, but production-quality domain analysis expects OpenAI or Gemini credentials. If keys are present, LLM analysis is enabled by default unless `OMNIFRAME_USE_LLM=false`. Set them in `.env` (read automatically by `docker compose up`):

```bash
OPENAI_API_KEY="..."
GEMINI_API_KEY="..."
OMNIFRAME_USE_LLM=true
```

If inference fails or credentials are absent, OmniFrame falls back to deterministic routing and schema-preserving canvases.

## Docker

```bash
docker compose up                                     # full dev stack: db + backend (:8000) + frontend (:5173), hot reload
docker compose up db                                  # Postgres only (host :5433)
docker compose -f docker-compose.prod.yml up --build  # prod-like combined image on :8080
```

The dev stack overrides `DATABASE_URL` to reach the `db` service over the Compose network; Postgres is also exposed on host port **5433** (to avoid conflicts with other local Postgres instances on 5432) for direct inspection. Anonymous profiles are created on first load and sent via the `X-OmniFrame-Profile-Id` header.

## AWS Elastic Beanstalk ZIP

```bash
cd /Users/gabrielsuarez/OmniFrame
npm run package:eb
```

Upload `omniframe-eb.zip` to an Elastic Beanstalk Docker environment.

## Novus by Pendo

The Pendo web SDK is installed in `index.html` with API key `c23d007d-a08e-4387-8564-e0a5e94c3810`. Anonymous visitor initialization is guarded and called exactly once per page lifecycle.
