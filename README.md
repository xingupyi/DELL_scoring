## Distress Scoring MVP

Backend service that exposes a `/score` endpoint to compute AI-assisted distress scores from text using Vertex AI Gemini plus 7‑day persistence logic.

### 1. Setup

- **Python version**: 3.10+ recommended.
- Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate  # on Windows
# or
source .venv/bin/activate  # on macOS/Linux
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configuration

Environment variables (optional for local dev, recommended for real deployments):

- `DATABASE_URL` – SQLAlchemy URL (default `sqlite:///./distress.db`).
- `VERTEX_PROJECT_ID` – GCP project ID (default `test-project` for local/tests).
- `VERTEX_LOCATION` – Vertex region (default `us-central1`).
- `VERTEX_MODEL_NAME` – Gemini model name (default `gemini-1.5-pro`).

You can place these in a `.env` file in the project root.

### 3. Running the API

Start the FastAPI app with uvicorn:

```bash
uvicorn app.main:app --reload
```

Key endpoints:

- `GET /health` – simple health check.
- `POST /score` – compute distress scores.

Example request body:

```json
{
  "user_id": "user-123",
  "timestamp": "2025-01-08T12:00:00Z",
  "text": "I feel completely overwhelmed and can't focus on anything."
}
```

Example response fields:

- `emotional_intensity` (0–33)
- `functional_impact` (0–33)
- `persistence` (0–33) – based on prior 7‑day history
- `total_score` (0–100)
- `risk_level` – Low / Moderate / High / Critical
- `ei_evidence`, `fi_evidence` – short supporting phrases

### 4. Running Tests

The test suite uses a mocked Gemini client so it does **not** call Vertex AI.

From the project root:

```bash
pytest
```

Tests cover:

- Risk band mapping for different EI/FI combinations.
- Persistence scoring, including trend flag behaviour and capping at 33.

