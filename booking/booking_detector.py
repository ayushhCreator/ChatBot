"""BookingIntentDetector: Detect when user is ready to book."""

# Trigger words that indicate booking readiness
CONFIRMATION_TRIGGERS = [
    "confirm", "book", "booking", "schedule", "appointment",
    "reserve", "proceed", "checkout", "finalize", "let's go",
    "yes", "correct", "go ahead", "accept", "ok let"
]


class BookingIntentDetector:
    """Detect booking intent from user message."""

    @staticmethod
    def should_trigger_confirmation(user_message: str, intent=None, current_state: str = "") -> bool:
        """
        Determine if confirmation should be triggered.

        Three levels of detection:
        1. Primary: Direct trigger words in message
        2. Secondary: Intent classified as booking
        3. Tertiary: Current state is confirmation
        """
        message_lower = user_message.lower().strip()

        # Primary: Check for trigger words
        if BookingIntentDetector._has_trigger_words(message_lower):
            return True

        # Secondary: Check intent classification (from Phase 1)
        if intent and hasattr(intent, 'intent_class') and intent.intent_class == "book":
            return True

        # Tertiary: Check if already in confirmation state
        if current_state == "confirmation":
            return True

        return False

    @staticmethod
    def _has_trigger_words(message: str) -> bool:
        """Check if message contains booking trigger words."""
        words = message.split()

        # Check for direct triggers
        for trigger in CONFIRMATION_TRIGGERS:
            if trigger in message:
                return True

        # Check for "confirm" variations
        for word in words:
            if word in ["confirm", "confirmed", "confirming"]:
                return True

        return False

    @staticmethod
    def get_confidence(user_message: str, intent=None) -> float:
        """
        Get confidence score for booking intent (0.0-1.0).

        0.9-1.0: Direct trigger words
        0.7-0.8: Intent is booking
        """
        message_lower = user_message.lower()

        # Direct trigger words: highest confidence
        if BookingIntentDetector._has_trigger_words(message_lower):
            return 0.95

        # Intent classification from Phase 1
        if intent and hasattr(intent, 'intent_class') and intent.intent_class == "book":
            return 0.75

        return 0.0