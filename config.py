"""
Configuration settings for the intelligent chatbot system.
"""
from enum import Enum
from typing import Dict
from datetime import time


class SentimentDimension(str, Enum):
    """Sentiment dimensions to track."""
    INTEREST = "interest"
    DISGUST = "disgust"
    ANGER = "anger"
    BOREDOM = "boredom"
    NEUTRAL = "neutral"


class ConversationState(str, Enum):
    """Unified conversation state machine for all chat flows."""
    # Core booking flow
    GREETING = "greeting"
    NAME_COLLECTION = "name_collection"
    VEHICLE_DETAILS = "vehicle_details"
    DATE_SELECTION = "date_selection"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"

    # Optional states (unused but kept for future expansion)
    SERVICE_SELECTION = "service_selection"
    TIER_SELECTION = "tier_selection"
    VEHICLE_TYPE = "vehicle_type"
    SLOT_SELECTION = "slot_selection"
    ADDRESS_COLLECTION = "address_collection"

    # Terminal states
    CANCELLED = "cancelled"


class StateTransitionRules:
    """Defines valid state transitions - single source of truth for state machine."""
    VALID_TRANSITIONS = {
        ConversationState.GREETING: [
            ConversationState.NAME_COLLECTION,
            ConversationState.SERVICE_SELECTION,
        ],
        ConversationState.NAME_COLLECTION: [
            ConversationState.VEHICLE_DETAILS,
            ConversationState.SERVICE_SELECTION,
        ],
        ConversationState.SERVICE_SELECTION: [
            ConversationState.NAME_COLLECTION,
            ConversationState.VEHICLE_DETAILS,
        ],
        ConversationState.VEHICLE_DETAILS: [
            ConversationState.DATE_SELECTION,
            ConversationState.CONFIRMATION,  # Allow direct jump to CONFIRMATION on explicit user request
            ConversationState.NAME_COLLECTION,
            ConversationState.SERVICE_SELECTION,
        ],
        ConversationState.DATE_SELECTION: [
            ConversationState.CONFIRMATION,
            ConversationState.VEHICLE_DETAILS,
        ],
        ConversationState.CONFIRMATION: [
            ConversationState.COMPLETED,
            ConversationState.DATE_SELECTION,  # edit
            ConversationState.CANCELLED,
        ],
        ConversationState.COMPLETED: [
            ConversationState.GREETING,
        ],
        ConversationState.CANCELLED: [
            ConversationState.GREETING,
        ],
        # Future states (not actively used)
        ConversationState.TIER_SELECTION: [
            ConversationState.CONFIRMATION,
        ],
        ConversationState.VEHICLE_TYPE: [
            ConversationState.VEHICLE_DETAILS,
        ],
        ConversationState.SLOT_SELECTION: [
            ConversationState.CONFIRMATION,
        ],
        ConversationState.ADDRESS_COLLECTION: [
            ConversationState.CONFIRMATION,
        ],
    }


class Config:
    """Main configuration class."""
    
    # DSPy/LLM Settings
    OLLAMA_BASE_URL = "http://localhost:11434"
    MODEL_NAME = "gemma3:4b"  # Better model for structured outputs (4.3B params)
    MAX_TOKENS = 8000
    TEMPERATURE = 0.3  # Lower for consistency
    
    # Conversation Settings
    MAX_CHAT_HISTORY = 25
    SENTIMENT_CHECK_INTERVAL = 2  # Check sentiment every N messages
    RETROACTIVE_SCAN_LIMIT = 4  # Number of recent messages to scan in retroactive validator (prevents timeout)

    # Confirmation Flow Settings
    CONFIRMATION_AUTO_CONFIRM_ATTEMPTS = 3  # Auto-confirm booking after N silent confirmation attempts

    # CONFIRMATION MODE TOGGLE - Controls when service request is created
    # "CHAT": Create service request immediately when DSPy detects confirmation intent (in /chat endpoint)
    #         User says "yes/confirm" → Service Request created → State moves to COMPLETED
    # "BUTTON": Only create service request when explicit button is clicked (in /api/confirmation endpoint)
    #           User says "yes/confirm" → Stays in CONFIRMATION state → Button click creates Service Request
    #
    # IMPORTANT: In BUTTON mode, /chat endpoint NEVER creates service requests, only /api/confirmation does
    CONFIRMATION_MODE = "CHAT"  # Options: "CHAT" or "BUTTON"

    # Field Completeness Configuration
    # MINIMUM REQUIRED: 8 fields needed to identify user, car, and requirement (mandatory for booking)
    # OPTIONAL ENHANCED: 6 additional fields for better service (service_type, time_slot, notes, tier, address, etc.)
    # TOTAL POSSIBLE: 14 fields (8 required + 6 optional)
    REQUIRED_FIELDS_FOR_BOOKING = 12  # Minimum fields to create a valid booking
    TOTAL_POSSIBLE_FIELDS = 16       # All fields including optional enhancements

    # Field breakdown:
    # REQUIRED (8): first_name, last_name, phone, vehicle_brand, vehicle_model, vehicle_plate, appointment_date, intent/service_type
    # OPTIONAL (6): full_name, time_slot, service_tier, notes, address, special_requests

    # Name Extraction Stopwords - Reject greetings/common responses as customer names
    # Fixes: Prevent "Haan" (Hindi yes), "Hello", "Hi", courtesy phrases etc. from being extracted as first_name
    GREETING_STOPWORDS = {
        # Hindi/Urdu greetings
        "haan", "haji", "han", "haa", "ji", "haanji", "hello ji", "nomoshkar", "namaste",
        # English greetings
        "hello", "hi", "hey", "yes", "yeah", "yep", "ok", "okay", "sure", "fine",
        # Casual responses
        "ok", "okey", "yo", "yup", "yaar", "dost", "sirji",
        # Courtesy/Thanking phrases - CRITICAL: Prevent these from being extracted as names
        "shukriya", "shukriya ji", "thank you", "thanks", "thankyou", "thank", "thx",
        "dhanyavaad", "bahut acha", "bahut achha", "achha", "acha", "great", "perfect",
        "done", "good", "nice", "wonderful", "excellent", "super", "awesome",
        # Common endings
        "bye", "goodbye", "tata", "cheerio", "see you", "later"
    }
    
    # Sentiment Thresholds
    SENTIMENT_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "proceed": {
            "interest": 5.0,
            "anger": 6.0,
            "disgust": 3.0,
            "boredom": 5.0,
        },
        "engage": {
            "interest": 5.0,
        },
        "disengage": {
            "anger": 8.0,
            "disgust": 8.0,
            "boredom": 9.0,
        }
    }
    
    # Service Information (for LLM context)
    SERVICES = {
        "wash": "Interior and Exterior Car wash",
        "polishing": "Interior and Exterior Car Polish",
        "detailing": "Interior and Exterior Car Detailing"
    }
    
    VEHICLE_TYPES = ["Hatchback", "Sedan", "SUV", "EV", "Luxury"]

    # Time Slot Configuration - Computable time objects for scheduling
    # Working hours: 6 AM to 6 PM (06:00 to 18:00)
    # 3 configurable slots with minimum 1-hour gaps (no overlaps)
    WORKING_HOURS_START = time(6, 0)    # 6:00 AM
    WORKING_HOURS_END = time(18, 0)     # 6:00 PM

    TIME_SLOTS = {
        "early_morning": {
            "label": "Early Morning",
            "start": time(6, 0),        # 6:00 AM
            "end": time(9, 0),          # 9:00 AM (3-hour window)
            "description": "Early morning service (6 AM - 9 AM)"
        },
        "afternoon": {
            "label": "Afternoon",
            "start": time(10, 0),       # 10:00 AM (1-hour gap from early morning)
            "end": time(13, 0),         # 1:00 PM (3-hour window)
            "description": "Afternoon service (10 AM - 1 PM)"
        },
        "evening": {
            "label": "Evening",
            "start": time(14, 0),       # 2:00 PM (1-hour gap from afternoon)
            "end": time(18, 0),         # 6:00 PM (4-hour window, until closing)
            "description": "Evening service (2 PM - 6 PM)"
        }
    }

    # Company Info
    COMPANY_NAME = "Yawlit Car Wash"
    COMPANY_DESCRIPTION = "Premium car care and carwash  services with professional detailing"


# Global config instance
config = Config()
