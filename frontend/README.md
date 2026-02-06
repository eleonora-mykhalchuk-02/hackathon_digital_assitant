# LLM Judge + Chatbot Frontend

React + TypeScript frontend for the LLM Judge + Chatbot application.

## Features

- Real-time chat interface with WebSocket support
- Live evaluation display with traffic light indicators (🟢/🟠/🔴)
- Streaming responses with typing indicators
- Inline criterion feedback and explanations
- Retry functionality for responses
- Stop generation control

## Setup

### Prerequisites
- Node.js 18+
- npm

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
# Create .env file (or use existing)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── ChatUI.tsx     # Main chat interface
│   │   ├── Message.tsx    # Individual message display
│   │   ├── JudgePanel.tsx # Judge evaluation panel
│   │   └── TrafficLight.tsx # Traffic light indicator
│   ├── services/          # API and WebSocket clients
│   │   ├── api.ts        # REST API client
│   │   └── websocket.ts  # WebSocket client
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Root component
│   └── main.tsx          # Entry point
├── public/               # Static assets
└── package.json          # Dependencies
```

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **WebSocket** - Real-time communication

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint

## Features Explained

### Traffic Light System

- 🟢 **Green** (70-100): Good quality, meets standards
- 🟠 **Orange** (40-69): Needs improvement
- 🔴 **Red** (0-39): Poor quality, fails to meet standards

### Real-time Updates

The frontend receives the following WebSocket events:

- `chatbot_generating` - Chatbot starts generating response
- `chatbot_chunk` - Streaming response chunks
- `chatbot_response` - Complete response received
- `judge_evaluating` - Judge starts evaluation
- `judge_criterion_result` - Individual criterion score (streaming)
- `judge_result` - Final evaluation complete
- `user_input_evaluation` - User input quality assessment
- `error` - Error occurred

### Message Flow

1. User sends message
2. Input evaluation (neutraliteit, impact, context, privacy, duidelijkheid)
3. Chatbot generates response with streaming
4. Judge evaluates response (bias, impact, complexiteit, volledigheid, relevantie, bruikbaarheid)
5. Traffic lights display inline with messages
6. If quality insufficient, automatic refinement (up to 2 iterations)

## Configuration

Edit `.env` to change backend URLs:
- `VITE_API_URL` - REST API endpoint
- `VITE_WS_URL` - WebSocket endpoint

## Development Notes

- Hot Module Replacement (HMR) enabled for fast development
- TypeScript strict mode enabled
- ESLint configured for code quality
- Component-scoped styling with inline styles

## Browser Support

Modern browsers with WebSocket support:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

