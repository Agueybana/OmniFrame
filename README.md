# OmniFrame

OmniFrame is an agentic "CAD for Thought" prototype. A user enters a business or engineering goal, the backend routes it to one of three V1 frameworks, and the frontend generates an editable visual canvas.

## V1 Routes

- SWOT: strategic baseline audit
- RICE: product and roadmap prioritization
- TRIZ: engineering contradiction solving

The full 50-framework reference catalog lives at `backend/app/data/framework_catalog.json` and is exposed through the Framework Library UI. Future frameworks are visible but locked.

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

## Optional LLM Routing

The deterministic router works without credentials. To enable LangChain-backed routing:

```bash
export OPENAI_API_KEY="..."
export OMNIFRAME_USE_LLM=true
export OMNIFRAME_ROUTER_MODEL="gpt-4.1-mini"
npm run dev
```

If LangChain routing fails or credentials are absent, OmniFrame falls back to deterministic routing.

## Docker

```bash
cd /Users/gabrielsuarez/OmniFrame
docker compose up --build
```

Open http://localhost:8080.

## AWS Elastic Beanstalk ZIP

```bash
cd /Users/gabrielsuarez/OmniFrame
npm run package:eb
```

Upload `omniframe-eb.zip` to an Elastic Beanstalk Docker environment.

## Novus by Pendo

The Pendo web SDK is installed in `index.html` with API key `c23d007d-a08e-4387-8564-e0a5e94c3810`. Anonymous visitor initialization is guarded and called exactly once per page lifecycle.
