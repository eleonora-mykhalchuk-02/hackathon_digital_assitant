# Technical Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Chat UI   │  │ Judge Panel  │  │ Settings Panel   │  │
│  │             │  │ (scores/     │  │ (criteria config)│  │
│  │             │  │  feedback)   │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP + WebSocket
             │
┌────────────▼────────────────────────────────────────────────┐
│                      Backend (Python)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              API Layer (FastAPI)                    │  │
│  │  - REST endpoints  - WebSocket handlers             │  │
│  └────────┬────────────────────────────────────────────┘  │
│           │                                                │
│  ┌────────▼─────────┐     ┌──────────────────────────┐   │
│  │ Orchestrator     │     │  Configuration Manager   │   │
│  │ - Conversation   │◄────┤  - Load criteria         │   │
│  │   flow control   │     │  - Validate settings     │   │
│  │ - Judge triggers │     └──────────────────────────┘   │
│  └────┬─────────┬───┘                                     │
│       │         │                                          │
│  ┌────▼────┐  ┌▼──────────┐                              │
│  │ Chatbot │  │   Judge   │                              │
│  │ Service │  │  Service  │                              │
│  │         │  │           │                              │
│  │ - LLM   │  │ - LLM     │                              │
│  │   calls │  │   calls   │                              │
│  │ - Prompt│  │ - Scoring │                              │
│  │   mgmt  │  │ - Feedback│                              │
│  └────┬────┘  └┬──────────┘                              │
│       │        │                                          │
│  ┌────▼────────▼───────┐                                 │
│  │   LLM Provider       │                                 │
│  │   Adapter            │                                 │
│  │ - AWS Bedrock        │                                 │
│  │ - Claude Sonnet 4.5  │                                 │
│  └──────────────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Components

#### Chat UI
- Message display (user, chatbot, system)
- Input field with send button
- Loading states and animations
- Support for markdown/rich text

#### Judge Panel
- Real-time score display (0-100)
- Traffic light indicators for scores:
  - 🟢 Green (70-100): Good quality
  - 🟠 Orange (40-69): Needs improvement
  - 🔴 Red (0-39): Poor quality
- Breakdown by criteria with individual traffic lights
- Feedback text from judge
- History of iterations (if feedback loop used)

#### Settings Panel
- Criteria configuration editor
- Enable/disable specific criteria
- Adjust weight of each criterion
- Toggle features (input critique, feedback loop)
- Select LLM providers

### 2. Backend Components

#### API Layer (FastAPI)
**Endpoints:**
- `POST /api/chat` - Send message, get response
- `GET /api/chat/history` - Retrieve conversation history
- `POST /api/judge/evaluate` - Manually evaluate a message
- `GET /api/criteria` - Get current criteria configuration
- `PUT /api/criteria` - Update criteria configuration
- `WS /ws/chat` - WebSocket for real-time streaming

**WebSocket Events:**
- `user_message` - User sends message
- `judge_input_critique` - Judge feedback on user input
- `chatbot_generating` - Chatbot is generating
- `chatbot_response` - Initial chatbot response
- `judge_evaluating` - Judge is evaluating
- `judge_result` - Judge scores and feedback
- `chatbot_refining` - Chatbot improving response
- `final_response` - Final approved response

#### Orchestrator
**Responsibilities:**
- Coordinate chatbot and judge interactions
- Implement conversation flow logic
- Manage feedback loop (iteration control)
- Handle error cases and fallbacks
- Store conversation state

**Flow Modes:**
1. **Simple Mode**: User → Chatbot → Judge → Display
2. **Feedback Mode**: User → Chatbot → Judge → Chatbot (refine) → Judge → Display
3. **Input Critique Mode**: User → Judge (critique) → Chatbot → Judge (evaluate) → Display

#### Chatbot Service
**Features:**
- LLM API integration
- Prompt engineering
- Context management (conversation history)
- Handle judge feedback for refinement
- Streaming response support

**Prompt Structure:**
```
System: [Role and behavior instructions]
History: [Previous messages]
[If refinement]: Judge Feedback: [Specific improvements needed]
User: [Current message]
```

#### Judge Service
**Features:**
- Evaluate messages against criteria
- Generate scores (0-100) per criterion
- Provide actionable feedback
- Determine if regeneration needed
- Support both input and output evaluation

**Evaluation Process:**
1. Load active criteria from config
2. Build evaluation prompt with criteria
3. Call LLM with structured output request
4. Parse scores and feedback
5. Calculate weighted overall score
6. Return structured result

#### Configuration Manager
**Features:**
- Load criteria from YAML file
- Validate criteria format
- Hot-reload configuration
- Provide defaults
- Support criteria profiles (strict, moderate, lenient)

### 3. Data Models

#### Message
```python
{
    "id": "uuid",
    "role": "user|assistant|system",
    "content": "text",
    "timestamp": "ISO datetime",
    "metadata": {
        "judge_score": float,
        "iteration": int
    }
}
```

#### JudgeEvaluation
```python
{
    "overall_score": float,  # 0-100
    "criteria_scores": {
        "accuracy": float,
        "relevance": float,
        ...
    },
    "feedback": "text",
    "should_regenerate": bool,
    "suggestions": ["list of improvements"]
}
```

#### Criterion
```python
{
    "name": "accuracy",
    "description": "Information is factual and correct",
    "weight": float,  # 0-1
    "enabled": bool,
    "threshold": float  # minimum acceptable score
}
```

## Configuration File Structure

### criteria.yaml
```yaml
profiles:
  strict:
    overall_threshold: 80
  moderate:
    overall_threshold: 60
  lenient:
    overall_threshold: 40

criteria:
  - name: accuracy
    description: "Response contains factually correct information"
    weight: 0.25
    enabled: true
    threshold: 70

  - name: relevance
    description: "Response directly addresses the user's question"
    weight: 0.25
    enabled: true
    threshold: 70

  - name: completeness
    description: "Response fully answers all aspects of the question"
    weight: 0.20
    enabled: true
    threshold: 60

  - name: clarity
    description: "Response is clear, well-structured, and easy to understand"
    weight: 0.15
    enabled: true
    threshold: 60

  - name: tone
    description: "Response maintains appropriate professional tone"
    weight: 0.10
    enabled: true
    threshold: 50

  - name: safety
    description: "Response is safe, appropriate, and doesn't contain harmful content"
    weight: 0.05
    enabled: true
    threshold: 90

settings:
  active_profile: moderate
  max_refinement_iterations: 2
  enable_input_critique: true
  enable_feedback_loop: true
  show_iteration_history: true

  # Traffic light thresholds
  traffic_light:
    green_threshold: 70    # 🟢 Good (>= 70)
    orange_threshold: 40   # 🟠 Needs improvement (40-69)
                           # 🔴 Poor (< 40)
```

## Technology Choices

### Backend Framework: FastAPI
**Reasons:**
- Modern Python framework with async support
- Built-in WebSocket support
- Automatic API documentation (Swagger)
- Fast performance
- Type hints and validation (Pydantic)

### Frontend: React with TypeScript
**Reasons:**
- Component-based architecture
- Large ecosystem
- Good WebSocket libraries
- TypeScript for type safety
- Easy to build real-time UI

### LLM Integration
**Provider:**
- **AWS Bedrock** with Claude Sonnet 4.5 (anthropic.claude-sonnet-4-5-v1:0)

**Configuration:**
- AWS credentials via environment variables
- AWS region configuration
- Model IDs configurable per service (chatbot/judge)
- Support for AWS IAM roles and session tokens

## Deployment Considerations

### Development
- UV for fast Python package management
- Docker Compose for local development
- Environment variables for API keys
- Hot reload for both frontend and backend

### Production (Optional)
- Docker containers
- Nginx reverse proxy
- Environment-based configuration
- HTTPS support

## Security & Privacy

- API keys stored in environment variables
- No conversation data persistence (POC only)
- Optional conversation logging for debugging
- Input sanitization
- Rate limiting on API endpoints

## Performance Considerations

- Async LLM calls where possible
- Streaming responses to frontend
- Caching of criteria configuration
- Connection pooling for LLM APIs
- WebSocket for reduced latency
