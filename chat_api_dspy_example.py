"""
Example: Integrating DSPy with the streaming chat API.
Replace the echo logic in chat_api.py with this approach.
"""
import json
import asyncio
from typing import List, Dict, Any

# Example DSPy integration (uncomment when ready)
# import dspy
# from dspy_config import dspy_configurator

async def generate_response_with_dspy(messages: List[Dict[str, str]], session_id: str):
    """Generate streaming response using DSPy."""
    
    user_message = messages[-1]["content"] if messages else ""
    
    # Initialize DSPy (if not already configured)
    # dspy_configurator.configure()
    
    # Example: Use your existing orchestrator
    # from orchestrator.message_processor import MessageProcessor
    # processor = MessageProcessor()
    # result = processor.process_message(
    #     conversation_id=session_id,
    #     user_message=user_message
    # )
    # response_text = result.message
    
    # For now, use echo
    response_text = f"Echo: {user_message}"
    
    # Stream tokens
    for char in response_text:
        yield f'0:"{char}"\n'.encode()
        await asyncio.sleep(0.02)
    
    # Example: Send generative UI based on intent
    # if result.intent == "booking":
    #     ui_data = {
    #         "type": "booking_card",
    #         "data": result.scratchpad or {}
    #     }
    #     yield f'3:{json.dumps([ui_data])}\n'.encode()
    
    # Finish
    yield f'd:{json.dumps({"finishReason": "stop"})}\n'.encode()


# Example: Tool calling with DSPy
async def generate_with_tools(messages: List[Dict[str, str]], session_id: str):
    """Example showing tool calling pattern."""
    
    user_message = messages[-1]["content"]
    
    # Detect if tool is needed
    if "weather" in user_message.lower():
        # Send tool call
        tool_call = {
            "toolCallId": "call_1",
            "toolName": "get_weather",
            "args": {"location": "San Francisco"}
        }
        yield f'9:{json.dumps([tool_call])}\n'.encode()
        
        # Simulate tool execution
        await asyncio.sleep(0.5)
        
        # Send tool result
        tool_result = {
            "toolCallId": "call_1",
            "result": {"temperature": 72, "condition": "sunny"}
        }
        yield f'a:{json.dumps([tool_result])}\n'.encode()
    
    # Generate response
    response = "The weather is sunny and 72°F"
    for char in response:
        yield f'0:"{char}"\n'.encode()
        await asyncio.sleep(0.02)
    
    yield f'd:{json.dumps({"finishReason": "stop"})}\n'.encode()
