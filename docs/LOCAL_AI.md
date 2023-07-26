# Local AI — FLLC CyberDeck (Pi400)

## Adapters

| Backend | Description |
|---------|-------------|
| `none` | Default. App works fully. No LLM calls. |
| `ollama` | Local Ollama instance with health check at `/api/tags` |
| `openai-compatible-local` | Any `/v1/chat/completions` endpoint (LM Studio, vLLM, LocalAI) |

## Configuration

```bash
# Via API
curl -X POST http://localhost:8000/settings/ai \
  -H 'Content-Type: application/json' \
  -d '{"backend":"ollama","config":{"endpoint":"http://localhost:11434","model":"llama3"}}'
```

Or via Settings page in the web UI.

## AI Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /ai/summarize` | Summarise analyst notes |
| `POST /ai/draft-finding` | Draft professional finding language |
| `POST /ai/suggest-names` | Suggest component/device names |
| `POST /ai/cluster` | Cluster evidence items |
| `POST /ai/assist-report` | Generate executive summary text |

## Running Ollama on Pi400

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3    # or a smaller model for Pi400
```

Or add to docker-compose.yml (uncomment the `ollama` service).

## Safety

AI is ONLY for: summarisation, drafting, clustering, naming, report writing.
AI is NEVER for: payload generation, exploitation, credential harvesting, evasion.

See also: `docs/latex/local_ai.tex`