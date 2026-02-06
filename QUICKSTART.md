# Quick Start Guide

## Prerequisites Check

Before running the application, ensure you have:

- ✅ Python 3.11+ installed
- ✅ Node.js 22+ installed (run `node --version`)
- ✅ UV package manager installed
- ✅ AWS account with Bedrock access
- ✅ Claude Sonnet 4.5 model enabled in your AWS region

## Step 1: Configure AWS Credentials

Edit `backend/.env` with your AWS credentials:

```bash
cd backend
nano .env  # or use any text editor
```

Required fields:
- `AWS_REGION`: Your AWS region (e.g., us-east-1)
- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

## Step 2: Start the Backend

```bash
cd backend
uv run uvicorn app.main:app --reload
```

The backend will start at: http://localhost:8000
API docs available at: http://localhost:8000/docs

## Step 3: Start the Frontend

Open a **new terminal** and run:

```bash
cd frontend
npm run dev
```

The frontend will start at: http://localhost:5173

## Step 4: Test the Application

1. Open http://localhost:5173 in your browser
2. Type a question in the chat input
3. Click "Send" or press Enter
4. Watch as:
   - The chatbot generates a response
   - The judge evaluates it with scores
   - Traffic lights indicate quality (🟢/🟠/🔴)

## Troubleshooting

### Backend Issues

**Problem**: Import errors or missing modules
```bash
cd backend
uv sync  # Re-sync dependencies
```

**Problem**: AWS credentials error
- Check your `.env` file has correct AWS credentials
- Verify your AWS account has Bedrock access
- Confirm Claude Sonnet 4.5 is available in your region

**Problem**: Port 8000 already in use
```bash
# Change PORT in backend/.env
PORT=8001
# Then update VITE_API_URL and VITE_WS_URL in frontend/.env
```

### Frontend Issues

**Problem**: Connection refused
- Ensure backend is running first
- Check backend URL in `frontend/.env`

**Problem**: WebSocket connection fails
- Verify `VITE_WS_URL` in `frontend/.env`
- Check browser console for errors

**Problem**: Node.js version error
```bash
nvm use 22  # Switch to Node.js 22
```

## Configuration

### Adjust Judge Criteria

Edit `backend/config/criteria.yaml` to:
- Add/remove evaluation criteria
- Adjust weights and thresholds
- Change traffic light thresholds
- Enable/disable features

After editing, the backend will hot-reload automatically.

### Change Conversation Mode

Edit `frontend/src/components/ChatUI.tsx`:
- `SIMPLE`: Basic mode without feedback loop
- `FEEDBACK`: Iterative refinement (default)
- `INPUT_CRITIQUE`: Also critiques user input

## Next Steps

- Review judge criteria in `backend/config/criteria.yaml`
- Experiment with different questions
- Try adjusting thresholds to see how scoring changes
- Check the API documentation at http://localhost:8000/docs

## Development Tips

- Backend auto-reloads on file changes (thanks to `--reload` flag)
- Frontend auto-refreshes via Vite HMR
- Check browser console for frontend logs
- Check terminal for backend logs

Enjoy your LLM Judge + Chatbot! 🚀
