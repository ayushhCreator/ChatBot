# Generative AI Chat Interface Setup

## Architecture

- **Backend**: FastAPI (Python) with streaming SSE support
- **Frontend**: Next.js (React) with Vercel AI SDK
- **State**: In-memory (no database required)

## Project Structure

```
ChatBot/
├── main.py                 # FastAPI app with existing endpoints
├── chat_api.py            # New streaming chat endpoint
├── frontend/              # Next.js application
│   ├── app/
│   │   ├── page.tsx      # Chat UI component
│   │   └── layout.tsx    # Root layout
│   └── .env.local        # Backend URL configuration
```

## Setup & Run

### 1. Backend (FastAPI)

```bash
# Install dependencies (if not already installed)
pip install fastapi uvicorn

# Run the server
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### 2. Frontend (Next.js)

```bash
# Navigate to frontend directory
cd frontend

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

### Current Implementation

- ✅ Streaming chat with token-by-token display
- ✅ Echo response (placeholder for DSPy integration)
- ✅ Generative UI support (booking cards)
- ✅ In-memory session storage
- ✅ Vercel AI SDK protocol compatibility

### Streaming Protocol

The backend uses Vercel AI SDK protocol:
- `0:"text"` - Text chunks
- `3:[{...}]` - Tool/UI data
- `d:{...}` - Finish message

### Generative UI Example

When user mentions "book" or "appointment", the backend sends a booking card:

```json
{
  "type": "booking_card",
  "data": {
    "service": "Car Wash",
    "date": "2024-01-15",
    "time": "10:00 AM"
  }
}
```

## Integration with DSPy

Replace the echo logic in `chat_api.py` with your DSPy integration:

```python
# In generate_response function
async def generate_response(messages: List[Message], session_id: str):
    user_message = messages[-1].content
    
    # Replace this with DSPy call
    # response_text = dspy_model.generate(user_message)
    response_text = f"Echo: {user_message}"
    
    # Stream the response...
```

## API Endpoints

### POST /api/chat

Streaming chat endpoint compatible with Vercel AI SDK.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "Book an appointment"}
  ],
  "session_id": "optional-session-id"
}
```

**Response:** Server-Sent Events stream

## Environment Variables

### Frontend (.env.local)

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Testing

1. Start backend: `uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open browser: `http://localhost:3000`
4. Type a message and see the streaming response
5. Try typing "book" to see generative UI

## Next Steps

- [ ] Integrate DSPy for intelligent responses
- [ ] Add more generative UI components
- [ ] Implement tool calling
- [ ] Add conversation history persistence
- [ ] Enhance UI with more features
