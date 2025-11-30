#!/bin/bash

# Start the chat interface (backend + frontend)

echo "🚀 Starting AI Chat Interface..."
echo ""

# Check if backend is running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend already running on port 8000"
else
    echo "🔧 Starting FastAPI backend..."
    uvicorn main:app --reload --port 8000 &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
fi

echo ""
echo "🔧 Starting Next.js frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Chat interface is starting..."
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8002"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
