# Soufet Agent

Soufet is an AI business data assistant. The LLM provider for this project is the NVIDIA hosted API, called through its OpenAI-compatible endpoint. The project does not run or download a model locally.

## NVIDIA API configuration

Create `.env` from `.env.example` and set a valid NVIDIA API key:

```env
NVIDIA_API_BASE=https://integrate.api.nvidia.com/v1
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_TIMEOUT_SECONDS=120
DATABASE_URL=postgresql+psycopg://soufet:your_password@localhost:5432/soufet
```

Never put a real key in `.env.example`, source code, logs, or chat. `.env` is ignored by Git. The NVIDIA integration is isolated in `app/agent/llm.py` and uses the OpenAI Python SDK with a 120-second timeout and no automatic retries.

## Test the NVIDIA connection first

Install dependencies and run the basic completion test:

```powershell
pip install -r requirements.txt
python scripts/test_nvidia.py
```

It prints the model, streamed response, and latency. It reports missing keys, authentication errors, timeouts, rate limits, and connection failures without displaying the API key. This smoke test enables reasoning; the production agent disables it and limits response tokens for faster tool routing.

## PostgreSQL and API

Use a PostgreSQL instance you already have, configure `DATABASE_URL`, and seed the synthetic demo data:

```powershell
python -m app.database.seed
```

The seed creates 120 customers, 30 products, 650 orders covering 2025 and 2026, and 1,623 order items. Then start the API:

```powershell
uvicorn app.main:app --reload
```

Health: `http://127.0.0.1:8000/health`  
Interactive API docs: `http://127.0.0.1:8000/docs`

The existing agent tools cover PostgreSQL schema and read-only SQL, safe calculations, chart specifications, and Markdown document search. Revenue is `SUM(quantity * unit_price)`; completed orders are included by default. Demo company policy is in `data/documents/refund_policy.md`.

Tool descriptions and selection guidance are supplied to the model in each tool schema and `app/agent/prompts.py`. The model decides each tool call from the request and prior tool results; the app does not hardcode question-specific tool sequences. SQL runs in a read-only transaction and is validated before execution. SQL errors are returned to the model so it can correct and retry.

Visualization tools return structured JSON only, with `chartType`, `meta`, `series`, and complete `data`; Cartesian charts use `xKey` and `xAxisLabel`, while pie charts use `nameKey` and `valueKey`. Supported chart types are `line`, `bar`, `pie`, and `scatter`.

Run automated local tests with `python -m pytest -q` (or `python -m pytest -q -p no:cacheprovider` if pytest cannot write its cache directory). The suite includes nine deterministic tool-sequence/recovery scenarios; it does not make live NVIDIA API calls.

## Web frontend

The Next.js and Tailwind frontend lives in `frontend/`. Start the FastAPI backend in one terminal, then in a second terminal:

```powershell
cd frontend
pnpm install
Copy-Item .env.example .env.local
pnpm dev
```

Open `http://localhost:3000`. The frontend proxies chat and health requests to `SOUFET_API_URL` (defaults to `http://127.0.0.1:8000`), renders Markdown safely, and maps validated visualization JSON to trusted Recharts components.
