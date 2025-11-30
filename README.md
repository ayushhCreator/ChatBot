# ChatBot - Generative AI Chat Interface

A fullstack AI-powered chat application with FastAPI backend and Next.js frontend.

## Quick Start

```bash
# Start both backend and frontend
./start_chat.sh

# Or manually:
# Terminal 1 - Backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Visit `http://localhost:3000` to use the chat interface.

## Architecture

- **Backend**: FastAPI with streaming SSE support (Python)
- **Frontend**: Next.js with Vercel AI SDK (React/TypeScript)
- **State**: In-memory (no database required)
- **AI**: DSPy integration ready (currently echo mode)

## Features

✅ Real-time streaming chat with token-by-token display  
✅ Generative UI support (booking cards, tool results)  
✅ Session management (in-memory)  
✅ Vercel AI SDK protocol compatibility  
✅ CORS configured for local development  

## Project Structure

```
ChatBot/
├── main.py                          # FastAPI app entry point
├── chat_api.py                      # Streaming chat endpoint
├── chat_api_dspy_example.py        # DSPy integration example
├── frontend/                        # Next.js application
│   ├── app/
│   │   ├── page.tsx                # Chat UI
│   │   └── layout.tsx              # Root layout
│   └── .env.local                  # Backend URL config
├── booking/                         # Booking logic modules
├── orchestrator/                    # Message processing
└── CHAT_SETUP.md                   # Detailed setup guide
```

## API Endpoints

### Streaming Chat
- `POST /api/chat` - Streaming chat with SSE

### Legacy Endpoints
- `POST /chat` - Original chat endpoint
- `POST /sentiment` - Sentiment analysis
- `POST /extract` - Data extraction
- `POST /api/confirmation` - Booking confirmation

## Documentation

- [CHAT_SETUP.md](CHAT_SETUP.md) - Detailed setup and integration guide
- [docs/](docs/) - Architecture and implementation docs

## Development

### Backend Requirements
```bash
pip install fastapi uvicorn
```

### Frontend Requirements
```bash
cd frontend
npm install
```

## Next Steps

- Integrate DSPy for intelligent responses (see `chat_api_dspy_example.py`)
- Add more generative UI components
- Implement tool calling
- Add conversation persistence
