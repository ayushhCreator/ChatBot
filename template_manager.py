"""
Template Manager - Decides when to push templates vs. use LLM chatbot.

Strategy:
- Use templates when user explicitly asks for catalog/pricing/booking
- Use LLM when user asks questions, needs clarification, or shows sentiment
- Balance is key: Don't be silent dumper OR cheeky sales girl
"""

from enum import Enum
from typing import Tuple


class ResponseMode(Enum):
    """Response strategy decision."""
    TEMPLATE_ONLY = "template"      # Just push template, minimal LLM
    LLM_THEN_TEMPLATE = "llm_then"  # Chat first, then template
    TEMPLATE_THEN_LLM = "template_then_llm"  # Template first, offer to chat
    LLM_ONLY = "llm_only"           # Just chat, no template


class TemplateManager:
    """Decide when to use templates vs. LLM responses."""

    # Keywords that trigger TEMPLATE mode
    TEMPLATE_TRIGGERS = {
        "catalog": ["catalog", "services", "menu", "what do you offer"],
        "plans": ["plans", "pricing", "prices", "cost", "how much", "tiers"],
        "booking": ["book", "schedule", "appointment", "reserve"],
        "pricing": ["price", "cost", "rates", "charges"],
    }

    # Keywords that trigger LLM mode (questions, clarifications)
    LLM_TRIGGERS = {
        "question": ["?", "how", "why", "what is", "explain", "tell me"],
        "confusion": ["understand", "confused", "don't know", "help", "guide"],
        "complaint": ["problem", "issue", "complaint", "bad", "poor"],
    }

    def __init__(self):
        self.sentiment_threshold_interested = 7.0
        self.sentiment_threshold_disinterested = 3.0

    def decide_response_mode(
        self,
        user_message: str,
        intent: str = "inquire",
        sentiment_interest: float = 5.0,
        sentiment_anger: float = 1.0,
        sentiment_disgust: float = 1.0,
        sentiment_boredom: float = 1.0,
        current_state: str = "greeting"
    ) -> Tuple[ResponseMode, str]:
        """
        Decide whether to use template or LLM response based on INTENT + SENTIMENT.

        Args:
            user_message: User's input
            intent: Classified intent from DSPy (book, inquire, complaint, small_talk, cancel, reschedule, payment)
            sentiment_interest: Interest score (1-10)
            sentiment_anger: Anger score (1-10)
            sentiment_disgust: Disgust score (1-10)
            sentiment_boredom: Boredom score (1-10)
            current_state: Current conversation state

        Returns:
            (ResponseMode, template_key_if_applicable)
        """
        # Map DSPy intent values to internal template_manager logic
        intent_lower = str(intent).strip().lower()
        intent_mapping = {
            "book": "booking",
            "inquire": "general_inquiry",
            "payment": "pricing",
            "complaint": "complaint",
            "small_talk": "general_inquiry",
            "cancel": "general_inquiry",
            "reschedule": "general_inquiry"
        }
        intent = intent_mapping.get(intent_lower, "general_inquiry")

        # RULE 0: State-aware decision - during data collection, ignore intent, ask for data
        data_collection_states = ["name_collection", "vehicle_details", "date_selection", "vehicle_type", "tier_selection", "slot_selection", "address_collection"]
        if current_state in data_collection_states:
            # During data collection, use LLM to guide user, don't show menus
            return (ResponseMode.LLM_ONLY, "")

        # RULE 1: Intent-Based Decision (Intent OVERRIDES sentiment)
        if intent == "pricing":
            return (ResponseMode.TEMPLATE_ONLY, "pricing")
        elif intent == "catalog":
            return (ResponseMode.TEMPLATE_ONLY, "catalog")
        elif intent == "booking":
            # Only show plans if not in data collection state (handled above)
            return (ResponseMode.TEMPLATE_ONLY, "plans")
        elif intent == "complaint":
            return (ResponseMode.LLM_ONLY, "")
        elif intent == "general_inquiry":
            return (ResponseMode.LLM_ONLY, "")

        # RULE 2: For small_talk & reschedule, use sentiment to adjust tone
        # Don't push templates to angry/disgusted/bored customers
        if sentiment_anger > 6.0 or sentiment_disgust > 6.0:
            return (ResponseMode.LLM_ONLY, "")

        if sentiment_boredom > 7.0:
            return (ResponseMode.LLM_ONLY, "")

        # Default for small_talk/reschedule: Use LLM with empathy
        return (ResponseMode.LLM_THEN_TEMPLATE, "")

    def _check_template_trigger(self, message: str) -> str:
        """Check if message matches template trigger keywords."""
        for template_type, keywords in self.TEMPLATE_TRIGGERS.items():
            if any(keyword in message for keyword in keywords):
                return template_type
        return ""

    def _is_question(self, message: str) -> bool:
        """Check if message is a question."""
        for keywords in self.LLM_TRIGGERS.values():
            if any(keyword in message for keyword in keywords):
                return True
        return False

    def should_send_template(self, mode: ResponseMode) -> bool:
        """Check if template should be sent in this mode."""
        return mode in [
            ResponseMode.TEMPLATE_ONLY,
            ResponseMode.TEMPLATE_THEN_LLM,
            ResponseMode.LLM_THEN_TEMPLATE,
        ]

    def should_send_llm_response(self, mode: ResponseMode) -> bool:
        """Check if LLM response should be sent in this mode."""
        return mode in [
            ResponseMode.LLM_ONLY,
            ResponseMode.LLM_THEN_TEMPLATE,
            ResponseMode.TEMPLATE_THEN_LLM,
        ]