"""
Streaming chat API endpoint compatible with Vercel AI SDK.
"""
import json
import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

logger = logging.getLogger("chat_api")

router = APIRouter()

# In-memory session storage
sessions: Dict[str, List[Dict[str, str]]] = {}


class Message(BaseModel):
    role: str
    content: str


class ChatStreamRequest(BaseModel):
    messages: List[Message]
    session_id: Optional[str] = "default"


async def generate_response(messages: List[Message], session_id: str, request: Request):
    """Generate streaming response using DSPy orchestrator."""
    
    # Store messages in session
    sessions[session_id] = [{"role": m.role, "content": m.content} for m in messages]
    
    # Get last user message
    user_message = messages[-1].content if messages else ""
    logger.info(f"🚀 CHAT API: session_id={session_id}, user_message='{user_message}'")
    
    try:
        # Get orchestrator from app state
        orchestrator = getattr(request.app.state, "orchestrator", None)
        logger.info(f"🔧 ORCHESTRATOR: Available={orchestrator is not None}")
        
        if orchestrator:
            logger.info(f"📤 PROCESSING: Sending to orchestrator...")
            try:
                # Process message through intelligent orchestrator (run in thread with timeout)
                import concurrent.futures
                loop = asyncio.get_event_loop()
                logger.info(f"🔧 Creating thread pool executor...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    logger.info(f"🔧 Submitting orchestrator task...")
                    future = loop.run_in_executor(
                        pool,
                        orchestrator.process_message,
                        session_id,
                        user_message
                    )
                    logger.info(f"⏱️  Waiting for orchestrator (max 60s timeout)...")
                    # Wait max 60 seconds for orchestrator response (DSPy makes multiple LLM calls)
                    result = await asyncio.wait_for(future, timeout=60.0)
                    logger.info(f"✅ Orchestrator returned successfully")
                response_text = result.message
                logger.info(f"📥 RESULT: intent={getattr(result, 'intent', 'None')}, response_length={len(response_text)}, state={getattr(result, 'state', 'None')}")
            except asyncio.TimeoutError:
                logger.error(f"❌ ORCHESTRATOR TIMEOUT: Took longer than 5s - falling back to simple response")
                response_text = f"Hello! I'm here to help you book a car wash. What's your name?"
                result = type('obj', (object,), {
                    'intent': 'general',
                    'scratchpad': None,
                    'message': response_text
                })()
            except Exception as orch_error:
                logger.error(f"❌ ORCHESTRATOR ERROR: {type(orch_error).__name__}: {str(orch_error)}", exc_info=True)
                # Fallback to simple greeting
                response_text = f"Hello! I'm here to help you book a car wash. What's your name?"
                result = type('obj', (object,), {
                    'intent': 'general',
                    'scratchpad': None,
                    'message': response_text
                })()
            

        else:
            # Fallback: Use Ollama directly for natural responses
            logger.warning(f"⚠️  FALLBACK: Using direct Ollama LLM")
            
            try:
                import httpx
                # Build conversation context
                conversation = "\n".join([f"{m.role}: {m.content}" for m in messages[-5:]])  # Last 5 messages
                
                prompt = f"""You are a helpful car wash booking assistant for Yawlit Car Wash.
Your job is to help customers book car wash appointments by collecting:
- Name
- Phone number
- Vehicle details (brand, model, plate)
- Preferred date and time

Be friendly, concise (1-2 sentences), and guide them through booking.

Conversation:
{conversation}

Respond naturally and helpfully:"""
                
                # Call Ollama directly with short timeout
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama3.2:1b",
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.7, "num_predict": 100}
                        }
                    )
                    result_json = response.json()
                    response_text = result_json.get("response", "").strip()
                    
                    if not response_text:
                        raise Exception("Empty response from LLM")
                    
                    logger.info(f"✅ LLM response generated: {len(response_text)} chars")
                    
            except Exception as llm_error:
                logger.error(f"❌ LLM fallback failed: {llm_error}")
                # Final fallback to keyword-based
                msg_lower = user_message.lower()
                if any(word in msg_lower for word in ['hi', 'hello', 'hey', 'namaste']):
                    response_text = "Hello! Welcome to Yawlit Car Wash. I'm here to help you book a car wash service. What's your name?"
                elif any(word in msg_lower for word in ['book', 'wash', 'service', 'clean']):
                    response_text = "Great! I can help you book a car wash. To get started, could you please tell me your name?"
                elif any(word in msg_lower for word in ['price', 'cost', 'rate', 'charge']):
                    response_text = "Our car wash services start from ₹500. We offer basic wash, premium detailing, and full service packages. Would you like to book an appointment?"
                else:
                    response_text = "I understand. I'm here to help you book a car wash service. Could you tell me your name to get started?"
            
            result = type('obj', (object,), {
                'intent': 'general',
                'scratchpad': None
            })()
            
        # Stream the response (common for both success and fallback)
        for char in response_text:
            chunk = f'0:"{char}"\n'
            yield chunk.encode()
            await asyncio.sleep(0.02)
        
        # Send generative UI based on intent/state
        if hasattr(result, 'intent') and (result.intent == "booking" or "book" in user_message.lower()):
            logger.info(f"🎨 UI: Sending booking card, scratchpad={getattr(result, 'scratchpad', None)}")
            ui_data = {
                "type": "booking_card",
                "data": result.scratchpad or {
                    "service": "Car Wash",
                    "date": "2024-01-15",
                    "time": "10:00 AM"
                }
            }
            ui_chunk = f'3:{json.dumps([ui_data])}\n'
            yield ui_chunk.encode()
        
        # Finish with usage stats
        finish_data = {
            "finishReason": "stop",
            "usage": {"promptTokens": len(user_message), "completionTokens": len(response_text)}
        }

    except Exception as e:
        # Error fallback
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        error_msg = f"Error: {str(e)}"
        for char in error_msg:
            yield f'0:"{char}"\n'.encode()
            await asyncio.sleep(0.02)
        
        finish_data = {
            "finishReason": "error",
            "usage": {"promptTokens": len(user_message), "completionTokens": len(error_msg)}
        }
    
    logger.info(f"✅ COMPLETE: Streaming finished")
    yield f'd:{json.dumps(finish_data)}\n'.encode()


@router.post("/api/chat")
async def chat_stream(request: ChatStreamRequest, req: Request):
    """Streaming chat endpoint compatible with Vercel AI SDK."""
    logger.info(f"🔄 ENDPOINT: /api/chat called with {len(request.messages)} messages, session={request.session_id}")
    return StreamingResponse(
        generate_response(request.messages, request.session_id, req),
        media_type="text/plain; charset=utf-8"
    )
