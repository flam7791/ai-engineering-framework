# Model and technology selection

Version 0.1 · How to choose between commercial, open-source and open-weight options for each
use case, and the local stack every pattern can run on.

## The decision, in order

1. **What does the data allow?** The classification decides the topology
   ([intake](use-case-intake.md)). Restricted or confidential information means open-weight
   models on the organisation's own infrastructure, whatever the quality of external models.
2. **What does the task need?** Measure it: run the service's evaluation against two or three
   candidate models and compare pass rate, safety failures, latency and tokens on the same cases.
   Many tasks (classification, extraction, short grounded answers, wording from computed
   figures) pass on small local models; long multi-step reasoning often needs a larger one.
3. **What does it cost at the expected volume?** Commercial: tokens × price, linear in volume.
   Local: no per-use API cost, but hardware, energy and someone to run it; cheap at low volume
   on existing machines, worth a GPU server at sustained volume.
4. **Who can support it?** A model nobody can update or monitor is a liability. Prefer what the
   operating team already runs.
5. **Can we leave?** Keep the OpenAI-compatible contract and the gateway in front, so any choice
   above is reversible by configuration.

Record the outcome in the service's `docs/decisions.md`, with the evaluation results that
justified it.

## Commercial, open-source, open-weight

| | Commercial API (external) | Commercial in tenant | Open-weight, self-hosted |
|---|---|---|---|
| Examples | Claude, OpenAI, Mistral API | Azure OpenAI and similar, in the organisation's region | Llama, Mistral, Qwen, Gemma, Phi through Ollama or vLLM |
| Data leaves the organisation | Yes, to the provider | To the tenant's processor, under its contract | No |
| Quality ceiling | Highest | High | Lower for the same hardware budget; closing for many tasks |
| Cost model | Per token | Per token or reserved capacity | Hardware, energy, operation |
| Latency | Low | Low | Depends on hardware: slow on CPU, fast on GPU |
| Lock-in risk | Medium | Medium | Low (weights stay; licence terms apply) |
| Use for | Public or approved internal data, hardest tasks | Most internal work | Restricted data, air-gapped networks, high-volume simple tasks, cost control |

"Open-weight" is not "open source": model licences differ (Apache 2.0, MIT, or the vendor's own
community licence with use restrictions). Check the licence of the exact model and size before
production.

## The local and open-source stack

Every component below is self-hostable and replaceable; the reference implementations use the
ones marked ●.

| Need | Options | Notes |
|---|---|---|
| Model runtime, laptop or small server | ● **Ollama**, llama.cpp server, LM Studio | OpenAI-compatible API; quantised models on CPU or a modest GPU |
| Model serving at volume | **vLLM**, Hugging Face TGI | GPU servers; batching; OpenAI-compatible API |
| Chat models | ● Llama 3.x, Qwen 2.5, Mistral, Gemma, Phi | Pick by evaluation, not leaderboard |
| Embedding models | ● nomic-embed-text, bge-m3 | Through the same runtime; keep one model per index |
| Keyword search | ● BM25 in Python, SQLite FTS5, OpenSearch | Often enough for curated corpora |
| Vector search | ● In-memory for small corpora; pgvector, Qdrant | Add when paraphrases miss |
| Tool protocol | ● Model Context Protocol (official Python SDK) | stdio locally, streamable HTTP on a network |
| Gateway | ● governed-llm-gateway; LiteLLM proxy | Routing, budgets, masking, local_only |
| Metrics and alerts | ● Prometheus, Grafana | |
| Traces | OpenTelemetry with Jaeger or Grafana Tempo; Langfuse (self-hosted) for LLM traces | |
| Chat front end | Open WebUI | Points at the gateway |
| Containers and orchestration | ● Docker Compose; Kubernetes (k3s, OpenShift) on-premises | |

### Rough hardware planning

Planning figures for 4-bit quantised models; confirm with a load test on your own hardware.

| Model size | Memory for weights | Runs on | Suits |
|---|---|---|---|
| 1–4B parameters | about 1–3 GB | Any recent laptop CPU | Classification, extraction, short grounded answers, wording |
| 7–9B | about 5–6 GB | Laptop (slow), small GPU (8 GB+) | Most P1, P3, P4 work; agent fast tier |
| 14–32B | about 9–20 GB | Single data-centre or workstation GPU | Harder reasoning; agent strong tier on-premises |
| 70B+ | about 40 GB+ | One or more large GPUs | Near-commercial quality for restricted work |

## What the measurements say so far

From [governed-llm-gateway](https://github.com/flam7791/governed-llm-gateway)'s recorded
evaluation (24 tasks with deterministic checks, October 2026): Llama 3.1 8B through Ollama on a
laptop CPU passed 19 of 24 tasks, the same as the commercial strong model, at zero API cost, but
took about 18 seconds per answer against about one second. Routing each task to the tier that
suits it passed all 24. Twenty-four tasks are directional, not a benchmark; the method is the
point: measure each candidate on the service's own cases.

## Running each reference implementation locally

| Repository | Local model setting |
|---|---|
| template-generated services | default: `llama3.2:3b` through Ollama |
| policy-evidence-mcp | `EVIDENCE_MCP_EMBEDDINGS_URL=http://localhost:11434/v1` with `nomic-embed-text` |
| governed-llm-gateway | `local_only` team policy; local model through Ollama |
| governed-agents | `GOVAGENTS_PROVIDER=openai_compatible`, `GOVAGENTS_BASE_URL=http://localhost:11434/v1` |
| reference-resolver-agent | `REFRESOLVER_PROVIDER=openai_compatible` with an Ollama model |
| oecd-data-pipeline | `python -m oecd_pipeline interpret` writes the notes with a local model (Ollama by default) |
| copilot-team-knowledge | `teamkb ask` answers from the published bundles with a local model |
| governed-ai-platform | `scripts/new_env.py --sovereign`, then `docker compose --profile sovereign up`: every tier on open-weight models |
