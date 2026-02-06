# LLM Judge + Chatbot

A proof-of-concept application demonstrating how an "LLM Judge" can work alongside a chatbot to provide real-time quality assessment and feedback.

## Features

- **Dual LLM System**: Separate chatbot and judge LLMs working together
- **Real-time Evaluation**: Judge scores responses on multiple criteria with traffic light indicators (🟢/🟠/🔴)
- **Iterative Refinement**: Automatic response improvement based on judge feedback
- **Configurable Criteria**: Easy YAML-based configuration without code changes
- **Input Critique**: Optional evaluation of user questions
- **WebSocket Support**: Real-time streaming updates

## Technology Stack

- **Backend**: Python, FastAPI, AWS Bedrock (Claude Sonnet 4.5)
- **Frontend**: React, TypeScript, Vite
- **Package Management**: UV for Python, npm for Node.js

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- UV package manager
- AWS account with Bedrock access

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

4. Run the server:
```bash
uv run uvicorn app.main:app --reload
```

API available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend available at: http://localhost:5173

## Configuration

### Judge Criteria

Edit `backend/config/criteria.yaml` to customize:
- Evaluation criteria and weights
- Quality thresholds
- Traffic light thresholds
- Feature toggles

### Environment Variables

Edit `backend/.env` to configure:
- AWS credentials and region
- Model IDs
- Feature flags
- Server settings

## API Endpoints

- `GET /` - Health check
- `POST /api/chat` - Send message (REST)
- `WS /ws/chat` - Real-time chat (WebSocket)
- `GET /api/criteria` - Get criteria configuration
- `PUT /api/criteria` - Update criteria
- `GET /api/chat/history/{id}` - Get conversation history

## Documentation

See `docs/planning/` for detailed documentation:
- `instructions.md` - Project overview and concept
- `architecture.md` - Technical architecture
- `implementation-plan.md` - Implementation details
- `project-structure.md` - File structure

## Development

### Project Structure

```
├── backend/          # Python FastAPI backend
│   ├── app/         # Application code
│   └── config/      # Configuration files
├── frontend/        # React TypeScript frontend
│   └── src/        # Source code
└── docs/           # Documentation
    └── planning/   # Planning documents
```

### Testing

Run the backend tests:
```bash
cd backend
uv run pytest
```

## License

MIT

## Authors

Created for OneGov Hackathon February 2026
