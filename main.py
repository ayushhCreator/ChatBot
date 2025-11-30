"""
FastAPI integration for the intelligent chatbot with graceful startup/shutdown.
"""
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

from orchestrator.message_processor import MessageProcessor
from dspy_config import dspy_configurator
from chat_api import router as chat_router

# Backward compatibility: ChatbotOrchestrator is now MessageProcessor
ChatbotOrchestrator = MessageProcessor

# Configure logging to show application-level logs (not just ASGI traces)
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['default'],
    },
}

logging.config.dictConfig(logging_config)

logger = logging.getLogger("yawlit.chatbot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic lives here.
    - Configure global things (dspy).
    - Create/start orchestrator and attach to app.state.
    - On shutdown: call orchestrator.shutdown() and any dspy shutdown hooks.
    """
    # --- Startup ---
    logger.info("Starting lifespan: configuring DSPy and starting orchestrator...")
    # configure DSPy (synchronous or async depending on your code)
    dspy_configurator.configure()

    # create orchestrator and start any background tasks it needs
    orchestrator = ChatbotOrchestrator()
    # If your orchestrator has an async start method, await it; otherwise call start()
    if hasattr(orchestrator, "start") and callable(orchestrator.start):
        maybe_coro = orchestrator.start()
        if hasattr(maybe_coro, "__await__"):
            await maybe_coro

    # attach to app for endpoint access
    app.state.orchestrator = orchestrator
    app.state.dspy_configurator = dspy_configurator

    yield

    # --- Shutdown ---
    logger.info("Shutdown initiated: stopping orchestrator and DSPy...")
    try:
        orch = app.state.orchestrator
        # Prefer an async shutdown if available
        if hasattr(orch, "shutdown") and callable(orch.shutdown):
            maybe_coro = orch.shutdown()
            if hasattr(maybe_coro, "__await__"):
                await maybe_coro
        logger.info("Orchestrator shutdown completed.")
    except Exception as e:
        logger.exception("Error shutting down orchestrator: %s", e)

    # If your dspy_configurator exposes a shutdown/cleanup hook, call it
    try:
        if hasattr(dspy_configurator, "shutdown"):
            maybe_coro = dspy_configurator.shutdown()
            if hasattr(maybe_coro, "__await__"):
                await maybe_coro
            logger.info("DSPy configurator shutdown completed.")
    except Exception as e:
        logger.exception("Error shutting down dspy_configurator: %s", e)

    logger.info("Lifespan shutdown finished.")


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Yawlit Intelligent Chatbot",
    description="DSPy-powered intelligent layer for car wash chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for Next.js frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include streaming chat router
app.include_router(chat_router)


# Pydantic models
class ChatRequest(BaseModel):
    conversation_id: str
    user_message: str
    current_state: Optional[str] = None  # DEPRECATED: State is now managed internally


class ChatResponse(BaseModel):
    message: str
    should_proceed: bool
    extracted_data: Optional[Dict[str, Any]] = None
    sentiment: Optional[Dict[str, float]] = None
    intent: Optional[str] = None  # NEW: Classified intent from user message
    intent_confidence: float = 0.0  # NEW: Confidence score for intent classification
    suggestions: Optional[Dict[str, Any]] = None
    should_confirm: bool = False
    scratchpad_completeness: float = 0.0
    scratchpad: Optional[Dict[str, Any]] = None  # NEW: Current scratchpad state
    state: str = "greeting"
    data_extracted: bool = False
    typo_corrections: Optional[Dict[str, str]] = None
    service_request_id: Optional[str] = None
    service_request: Optional[Dict[str, Any]] = None  # NEW: Full service request details if booking was created


class SentimentRequest(BaseModel):
    conversation_id: str
    user_message: str


class DataExtractionRequest(BaseModel):
    user_message: str
    extraction_type: str  # 'name', 'vehicle', 'date'


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Yawlit Intelligent Chatbot",
        "dspy_configured": getattr(app.state, "dspy_configurator", None) is not None
    }


def get_orchestrator(request: Request) -> ChatbotOrchestrator:
    orch = getattr(request.app.state, "orchestrator", None)
    if orch is None:
        raise HTTPException(status_code=503, detail="Orchestrator not available")
    return orch


@app.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest, req: Request):
    try:
        orchestrator = get_orchestrator(req)

        # State is now managed internally by orchestrator
        # The current_state parameter is deprecated and ignored
        result = orchestrator.process_message(
            conversation_id=request.conversation_id,
            user_message=request.user_message
        )

        return ChatResponse(
            message=result.message,
            should_proceed=result.should_proceed,
            extracted_data=result.extracted_data,
            sentiment=result.sentiment,
            intent=result.intent,  # NEW: Include intent class
            intent_confidence=result.intent_confidence,  # NEW: Include confidence
            suggestions=result.suggestions,
            should_confirm=result.should_confirm,
            scratchpad_completeness=result.scratchpad_completeness,
            scratchpad=result.scratchpad,  # NEW: Include scratchpad contents
            state=result.state,
            data_extracted=result.data_extracted,
            typo_corrections=result.typo_corrections,
            service_request_id=result.service_request_id,
            service_request=result.service_request  # NEW: Include full service request
        )

    except Exception as e:
        logger.exception("Error processing chat: %s", e)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.post("/sentiment")
async def analyze_sentiment(request: SentimentRequest, req: Request):
    try:
        orchestrator = get_orchestrator(req)

        context = orchestrator.conversation_manager.get_or_create(
            request.conversation_id
        )

        history = context.get_history_text(max_messages=10)
        sentiment = orchestrator.sentiment_service.analyze(
            history,
            request.user_message
        )

        return {
            "sentiment": sentiment.to_dict() if hasattr(sentiment, 'to_dict') else vars(sentiment),
            "should_proceed": sentiment.should_proceed() if hasattr(sentiment, 'should_proceed') else True,
            "needs_engagement": sentiment.needs_engagement() if hasattr(sentiment, 'needs_engagement') else False,
            "should_disengage": sentiment.should_disengage() if hasattr(sentiment, 'should_disengage') else False,
            "reasoning": getattr(sentiment, 'reasoning', 'No reasoning available')
        }
    except Exception as e:
        logger.exception("Error analyzing sentiment: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract")
async def extract_data(request: DataExtractionRequest, req: Request):
    try:
        orchestrator = get_orchestrator(req)

        # Access data extractor through extraction_coordinator
        data_extractor = orchestrator.extraction_coordinator.data_extractor

        if request.extraction_type == "name":
            result = data_extractor.extract_name(request.user_message)
            return {"extracted": result.__dict__ if result else None}

        elif request.extraction_type == "vehicle":
            result = data_extractor.extract_vehicle_details(request.user_message)
            return {"extracted": result.__dict__ if result else None}

        elif request.extraction_type == "date":
            result = data_extractor.parse_date(request.user_message)
            return {"extracted": result.__dict__ if result else None}

        else:
            raise HTTPException(status_code=400, detail="Invalid extraction type")

    except Exception as e:
        logger.exception("Error extracting data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/confirmation")
async def handle_confirmation(req: Request):
    """Handle user actions on confirmation screen (confirm/edit/cancel).

    CRITICAL FIX: Uses same ConversationManager and ScratchpadCoordinator from orchestrator.
    This ensures scratchpad data populated during /chat is available for booking creation.
    """
    from booking_orchestrator_bridge import BookingOrchestrationBridge

    try:
        # Parse JSON body
        body = await req.json()
        conversation_id = body.get("conversation_id")
        user_input = body.get("user_input")
        action = body.get("action")

        if not conversation_id or not user_input or not action:
            raise HTTPException(
                status_code=422,
                detail="Missing required fields: conversation_id, user_input, action"
            )

        # Get orchestrator from app state (same instance used by /chat endpoint)
        orchestrator = get_orchestrator(req)

        # CRITICAL DEBUG: Check state before processing
        context_before = orchestrator.conversation_manager.get_or_create(conversation_id)
        logger.critical(f"🔍 /api/confirmation ENTRY: conversation_id={conversation_id}, state_before={context_before.state}, action={action}")

        # Initialize bridge with SHARED resources from orchestrator
        # This ensures /chat and /api/confirmation use the SAME state and scratchpad
        bridge = BookingOrchestrationBridge(
            conversation_manager=orchestrator.conversation_manager,
            scratchpad_coordinator=orchestrator.scratchpad_coordinator
        )
        bridge.initialize_booking(conversation_id)

        # Process through booking flow
        response_msg, service_request = bridge.process_booking_turn(
            user_input, {}, intent=None, action=action
        )

        # CRITICAL DEBUG: Check state after processing
        context_after = orchestrator.conversation_manager.get_or_create(conversation_id)
        logger.critical(f"🔍 /api/confirmation AFTER process: state_after={context_after.state}, response_msg={response_msg[:50] if response_msg else 'None'}")

        # FOOLPROOF: Extract service_request_id with multiple fallback layers
        service_request_id = None

        # Layer 1: Direct from service_request object
        if service_request:
            service_request_id = service_request.service_request_id
            logger.critical(f"🔷 Layer 1: Got service_request_id from service_request object: {service_request_id}")

        # Layer 2: Check conversation metadata (stored by booking flow)
        if not service_request_id:
            context = orchestrator.conversation_manager.get_or_create(conversation_id)
            service_request_id = context.metadata.get('service_request_id')
            if service_request_id:
                logger.critical(f"🔷 Layer 2: Retrieved service_request_id from conversation metadata: {service_request_id}")

        # Layer 3: Check if current state is COMPLETED (means booking was done)
        if not service_request_id and bridge.get_booking_state() == "completed":
            # Try to retrieve the scratchpad and rebuild the service request
            scratchpad = bridge.booking_manager.scratchpad if bridge.booking_manager else None
            if scratchpad:
                from booking.service_request import ServiceRequestBuilder
                service_request = ServiceRequestBuilder.build(scratchpad, conversation_id)
                service_request_id = service_request.service_request_id
                logger.critical(f"🔷 Layer 3: Rebuilt service_request_id from scratchpad in COMPLETED state: {service_request_id}")
                # Store it for next time
                context = orchestrator.conversation_manager.get_or_create(conversation_id)
                context.metadata['service_request_id'] = service_request_id

        logger.critical(f"✅✅✅ CONFIRMATION RESPONSE: service_request_id={service_request_id}, state={bridge.get_booking_state()}")

        # CRITICAL: Dump service request JSON and clear scratchpad (BUTTON mode only)
        # User requirement: "IN any and ALL cases if and only if service request ID is made then scratchpad can be reset else NOT"
        if service_request_id and bridge.booking_manager:
            scratchpad = bridge.booking_manager.scratchpad
            if scratchpad:
                scratchpad_completeness = scratchpad.get_completeness()

                # CRITICAL: Check if scratchpad is empty (already cleared by CHAT mode)
                # If service_request_id exists but scratchpad is empty, skip dump (already done)
                if scratchpad_completeness == 0.0:
                    logger.warning(f"⏭️  SKIP DUMP: Scratchpad already cleared (booking done in CHAT mode), service_request_id={service_request_id}")
                else:
                    # Dump service request JSON before clearing scratchpad (BUTTON mode only)
                    from service_request_dumper import dump_service_request
                    try:
                        dump_service_request(
                            service_request_id=service_request_id,
                            conversation_id=conversation_id,
                            scratchpad=scratchpad,
                            confirmation_method="button",
                            additional_metadata={"confirmation_mode": "BUTTON", "action": action}
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to dump service request: {e}")

                    # Now clear scratchpad after successful dump
                    scratchpad.clear_all()
                    logger.info(f"🧹 SCRATCHPAD CLEARED (BUTTON MODE): service_request_id={service_request_id} confirmed")

        return {
            "message": response_msg,
            "service_request_id": service_request_id,
            "state": bridge.get_booking_state(),
        }

    except Exception as e:
        logger.exception("Error handling confirmation: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # In production prefer to run `uvicorn module:app --host 0.0.0.0 --port 8002 --workers 1`
    uvicorn.run("your_module_name:app", host="0.0.0.0", port=8002, log_level="info")
