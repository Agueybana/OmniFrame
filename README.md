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

```bash
cd /Users/gabrielsuarez/OmniFrame
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm install
npm run dev
```

If this Codex desktop environment does not expose a global `npm`, use the local bootstrapper:

```bash
cd /Users/gabrielsuarez/OmniFrame
bash scripts/bootstrap-local-npm.sh
node .local/npm/bin/npm-cli.js install --cache .local/npm-cache
node .local/npm/bin/npm-cli.js run dev
```

Open:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/api/health

## LLM Analysis

The deterministic fallback works without credentials, but production-quality domain analysis expects OpenAI or Gemini credentials. If keys are present, LLM analysis is enabled by default unless `OMNIFRAME_USE_LLM=false`.

```bash
export OPENAI_API_KEY="..."
export GEMINI_API_KEY="..."
export OMNIFRAME_USE_LLM=true
npm run dev
```

If inference fails or credentials are absent, OmniFrame falls back to deterministic routing and schema-preserving canvases.

## Docker

```bash
cd /Users/gabrielsuarez/OmniFrame
docker compose up db          # postgres only for local dev
docker compose up --build     # app + postgres
alembic upgrade head          # if migrations are not auto-run on startup
```

Open http://localhost:8080 when running the full stack.

For local development with `npm run dev`, start Postgres separately:

```bash
docker compose up db
cp .env.example .env
npm run dev
```

The backend reads `DATABASE_URL` from `.env`. Postgres is exposed on host port **5433** (to avoid conflicts with other local Postgres instances on 5432). Anonymous profiles are created on first load and sent via the `X-OmniFrame-Profile-Id` header.

## AWS Elastic Beanstalk ZIP

```bash
cd /Users/gabrielsuarez/OmniFrame
npm run package:eb
```

Upload `omniframe-eb.zip` to an Elastic Beanstalk Docker environment.

## Novus by Pendo

The Pendo web SDK is installed in `index.html` with API key `c23d007d-a08e-4387-8564-e0a5e94c3810`. Anonymous visitor initialization is guarded and called exactly once per page lifecycle.
