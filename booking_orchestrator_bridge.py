"""Bridge: Integrate Phase 2 booking flow with Phase 1 orchestrator."""

from typing import Optional, Tuple
from conversation_manager import ConversationManager
from booking.booking_flow_integration import BookingFlowManager
from booking.service_request import ServiceRequest
from models import ValidatedIntent


class BookingOrchestrationBridge:
    """Adapter connecting chatbot orchestrator to booking flow with unified state."""

    def __init__(self, conversation_manager: Optional[ConversationManager] = None, scratchpad_coordinator=None):
        self.booking_manager: Optional[BookingFlowManager] = None
        # Use injected ConversationManager (shared with /chat endpoint) or create new
        self.conversation_manager = conversation_manager or ConversationManager()
        # Use injected ScratchpadCoordinator (shared with /chat endpoint) or create new
        self.scratchpad_coordinator = scratchpad_coordinator

    def initialize_booking(self, conversation_id: str) -> None:
        """Start new booking flow with unified state management."""
        self.booking_manager = BookingFlowManager(
            conversation_id,
            conversation_manager=self.conversation_manager,
            scratchpad_coordinator=self.scratchpad_coordinator
        )

    def process_booking_turn(
        self,
        user_message: str,
        extracted_data: dict,
        intent: Optional[ValidatedIntent] = None,
        action: Optional[str] = None
    ) -> Tuple[str, Optional[ServiceRequest]]:
        """
        Process user message through booking flow.

        Args:
            user_message: User's message text
            extracted_data: Extracted data from message
            intent: User's intent
            action: Explicit action from confirmation button (confirm/edit/cancel)

        Returns:
            (response_message, service_request_if_confirmed)
        """
        if not self.booking_manager:
            return "Unable to process booking.", None

        return self.booking_manager.process_for_booking(
            user_message, extracted_data, intent, action
        )

    def should_use_booking_flow(self, intent: Optional[ValidatedIntent]) -> bool:
        """Check if message should trigger booking flow."""
        if not intent:
            return False
        # Check if intent is booking-related
        return hasattr(intent, 'intent_class') and intent.intent_class == "book"

    def is_in_booking_flow(self) -> bool:
        """Check if currently in active booking flow."""
        return self.booking_manager is not None

    def get_booking_state(self) -> Optional[str]:
        """Get current booking state."""
        if not self.booking_manager:
            return None
        return self.booking_manager.get_state().value

    def reset_booking_flow(self) -> None:
        """Reset booking flow (for cancellation)."""
        if self.booking_manager:
            self.booking_manager.reset()
            self.booking_manager = None

    def complete_booking_flow(self) -> Optional[ServiceRequest]:
        """Get completed service request."""
        if not self.booking_manager:
            return None
        if self.booking_manager.is_complete():
            return self.booking_manager.scratchpad
        return None
