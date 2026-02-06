# LLM Judge + Chatbot Backend

Python backend using FastAPI for the LLM Judge + Chatbot application.

## Setup

### Prerequisites
- Python 3.11+
- UV package manager

### Installation

1. Initialize the project with UV:
```bash
cd backend
uv init
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Running the Server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation available at `http://localhost:8000/docs`

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── services/            # Business logic
│   ├── api/                 # API routes
│   └── utils/               # Utilities
├── config/
│   └── criteria.yaml        # Judge criteria
└── pyproject.toml           # Dependencies
```

## API Endpoints

- `GET /` - Health check
- `POST /api/chat` - Send message and get response
- `GET /api/criteria` - Get judge criteria
- `PUT /api/criteria` - Update criteria
- `WS /ws/chat` - WebSocket for real-time chat

## Configuration

Edit `config/criteria.yaml` to customize judge criteria and thresholds.
