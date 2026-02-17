# PaperBanana HTTP API

Base URL: `https://<your-domain>` (Docker + Caddy) or `http://localhost:8000` (local dev)

Interactive docs: `GET /docs` (Swagger UI) | `GET /redoc` (ReDoc)

---

## Quick Start

```bash
# Local dev
pip install -e ".[api]"
uvicorn api.app:app --reload

# Docker
docker compose up -d
```

---

## Endpoints

### Health Check

```
GET /health
```

**Response** `200`

```json
{
  "status": "ok"
}
```

---

### Submit Generation Task

```
POST /api/v1/generate
Content-Type: application/json
```

Submits an async diagram generation task. Returns immediately with a task ID.

**Request Body**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `source_context` | string | Yes | | Methodology text or paper excerpt |
| `communicative_intent` | string | Yes | | Figure caption describing what to communicate |
| `diagram_type` | string | No | `"methodology"` | `"methodology"` or `"statistical_plot"` |
| `raw_data` | object | No | `null` | Raw data for statistical plots (CSV path or dict) |
| `refinement_iterations` | integer | No | `null` | Override default refinement iterations (default: 3) |

**Response** `202 Accepted`

```json
{
  "task_id": "a1b2c3d4e5f6",
  "status": "pending",
  "status_url": "/api/v1/tasks/a1b2c3d4e5f6"
}
```

---

### Query Task Status

```
GET /api/v1/tasks/{task_id}
```

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `task_id` | string | Task ID returned by the generate endpoint |

**Response** `200`

Task status transitions: `pending` -> `running` -> `completed` | `failed`

```json
{
  "task_id": "a1b2c3d4e5f6",
  "status": "completed",
  "created_at": "2026-02-15T10:30:00Z",
  "completed_at": "2026-02-15T10:32:15Z",
  "progress": null,
  "result": {
    "image_url": "/api/v1/tasks/a1b2c3d4e5f6/image",
    "run_id": "20260215_103000_abc123",
    "description": "A methodology diagram showing the three-phase pipeline...",
    "total_iterations": 2,
    "metadata": {}
  },
  "error": null
}
```

When `status` is `"running"`:

```json
{
  "task_id": "a1b2c3d4e5f6",
  "status": "running",
  "created_at": "2026-02-15T10:30:00Z",
  "completed_at": null,
  "progress": "Running generation pipeline",
  "result": null,
  "error": null
}
```

When `status` is `"failed"`:

```json
{
  "task_id": "a1b2c3d4e5f6",
  "status": "failed",
  "created_at": "2026-02-15T10:30:00Z",
  "completed_at": "2026-02-15T10:30:05Z",
  "progress": null,
  "result": null,
  "error": "VLM provider returned an error: 401 Unauthorized"
}
```

**Error** `404`

```json
{
  "detail": "Task a1b2c3d4e5f6 not found"
}
```

---

### Download Generated Image

```
GET /api/v1/tasks/{task_id}/image
```

Returns the final PNG image as a file download.

**Response** `200` — `Content-Type: image/png`

Binary PNG data. The `Content-Disposition` header is set to `attachment; filename="{task_id}.png"`.

**Error** `404` — Task not found or image file missing

**Error** `409` — Task has not completed successfully

```json
{
  "detail": "Task has not completed successfully"
}
```

---

## Examples

### cURL: Generate a Methodology Diagram

```bash
# 1. Submit task
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_context": "Our method consists of three stages. First, a retrieval module selects relevant reference diagrams from a curated set using VLM-based similarity scoring. Second, a planning module generates a detailed textual description via in-context learning with the retrieved examples. Third, an iterative refinement loop alternates between image generation and critic evaluation until the output meets publication quality standards.",
    "communicative_intent": "Overview of the three-stage pipeline for automated academic diagram generation"
  }')

echo "$RESPONSE"
# {"task_id":"a1b2c3d4e5f6","status":"pending","status_url":"/api/v1/tasks/a1b2c3d4e5f6"}

TASK_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

# 2. Poll until complete
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/tasks/$TASK_ID)
  echo "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"]}')"

  DONE=$(echo "$STATUS" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  if [ "$DONE" = "completed" ] || [ "$DONE" = "failed" ]; then
    break
  fi
  sleep 5
done

# 3. Download image
curl -s http://localhost:8000/api/v1/tasks/$TASK_ID/image -o diagram.png
echo "Saved to diagram.png"
```

### cURL: Generate a Statistical Plot

```bash
curl -s -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "source_context": "We evaluated four models on three benchmarks. GPT-4 achieved 92.1%, 87.3%, and 95.0% on MMLU, HellaSwag, and ARC respectively. Claude-3 scored 91.5%, 86.8%, 94.2%. Gemini-Pro scored 88.7%, 84.1%, 91.3%. Llama-3 scored 84.2%, 81.5%, 87.8%.",
    "communicative_intent": "Grouped bar chart comparing model accuracy across three benchmarks",
    "diagram_type": "statistical_plot",
    "raw_data": {
      "models": ["GPT-4", "Claude-3", "Gemini-Pro", "Llama-3"],
      "MMLU": [92.1, 91.5, 88.7, 84.2],
      "HellaSwag": [87.3, 86.8, 84.1, 81.5],
      "ARC": [95.0, 94.2, 91.3, 87.8]
    },
    "refinement_iterations": 2
  }'
```

### Python: Full Workflow

```python
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


async def generate_diagram():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=300) as client:
        # 1. Submit
        resp = await client.post("/api/v1/generate", json={
            "source_context": (
                "The encoder-decoder architecture processes input tokens through "
                "a stack of self-attention layers, followed by cross-attention to "
                "the encoded representation, producing output tokens autoregressively."
            ),
            "communicative_intent": "Encoder-decoder transformer architecture diagram",
        })
        resp.raise_for_status()
        task = resp.json()
        task_id = task["task_id"]
        print(f"Task submitted: {task_id}")

        # 2. Poll
        while True:
            resp = await client.get(f"/api/v1/tasks/{task_id}")
            resp.raise_for_status()
            status = resp.json()
            print(f"  Status: {status['status']}  Progress: {status.get('progress')}")

            if status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(5)

        if status["status"] == "failed":
            print(f"Error: {status['error']}")
            return

        # 3. Download image
        resp = await client.get(f"/api/v1/tasks/{task_id}/image")
        resp.raise_for_status()
        with open("output.png", "wb") as f:
            f.write(resp.content)
        print(f"Image saved to output.png")
        print(f"Description: {status['result']['description'][:100]}...")


asyncio.run(generate_diagram())
```

### Python: Minimal One-Shot (Blocking Poll)

```python
import httpx, time

BASE = "http://localhost:8000"

# Submit
task_id = httpx.post(f"{BASE}/api/v1/generate", json={
    "source_context": "We propose a multi-agent framework with five specialized agents.",
    "communicative_intent": "System architecture of the multi-agent framework",
}).json()["task_id"]

# Poll
while True:
    r = httpx.get(f"{BASE}/api/v1/tasks/{task_id}").json()
    if r["status"] in ("completed", "failed"):
        break
    time.sleep(5)

# Download
if r["status"] == "completed":
    img = httpx.get(f"{BASE}/api/v1/tasks/{task_id}/image").content
    open("result.png", "wb").write(img)
```

---

## Configuration

The API reads configuration from environment variables (or `.env` file):

| Variable | Description | Example |
|---|---|---|
| `VLM_PROVIDER` | VLM provider to use | `apicore`, `gemini`, `openrouter` |
| `VLM_MODEL` | Model identifier | `google/gemini-2.0-flash` |
| `IMAGE_PROVIDER` | Image generation provider | `nanobanana`, `google_imagen`, `openrouter_imagen` |
| `APICORE_API_KEY` | API key for apicore.ai | |
| `KIE_API_KEY` | API key for kie.ai (NanoBanana) | |
| `GOOGLE_API_KEY` | Google Gemini API key | |
| `VLM_BASE_URL` | Override VLM endpoint URL | `https://api.apicore.ai/v1` |

---

## Deployment

### Local Development

```bash
pip install -e ".[api]"
uvicorn api.app:app --reload --port 8000
```

### Docker + HTTPS

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your API keys and DOMAIN

# 2. Launch
docker compose up -d

# 3. Verify
curl https://your-domain.com/health
```

Caddy automatically provisions TLS certificates via Let's Encrypt when `DOMAIN` is set to a public domain. For local development, `DOMAIN=localhost` uses a self-signed certificate.

---

## Rate Limits

The server processes at most **3 tasks concurrently**. Additional tasks queue as `pending` until a slot opens.

---

## Error Codes

| HTTP Code | Meaning |
|---|---|
| `200` | Success |
| `202` | Task accepted (async) |
| `404` | Task not found / image file missing |
| `409` | Task not yet completed (image download) |
| `422` | Request validation error (missing/invalid fields) |
| `500` | Internal server error |
