"""BookingFlowManager: High-level orchestration of all Phase 2 components."""

from typing import Tuple, Optional
from config import ConversationState
from conversation_manager import ConversationManager
from booking.scratchpad import ScratchpadManager
from booking.confirmation import ConfirmationGenerator
from booking.booking_detector import BookingIntentDetector
from booking.confirmation_handler import ConfirmationHandler, ConfirmationAction
from booking.service_request import ServiceRequestBuilder, ServiceRequest


class BookingFlowManager:
    """Orchestrates entire booking flow with unified state management."""

    def __init__(self, conversation_id: str, conversation_manager: ConversationManager = None, scratchpad_coordinator=None, typo_detector=None):
        self.conversation_id = conversation_id
        # CRITICAL FIX: Use scratchpad from coordinator if provided (shared with /chat endpoint)
        # Otherwise create fresh scratchpad (for standalone booking flows)
        if scratchpad_coordinator:
            self.scratchpad = scratchpad_coordinator.get_or_create(conversation_id)
        else:
            self.scratchpad = ScratchpadManager(conversation_id)
        # Use injected ConversationManager or create new one
        self.conversation_manager = conversation_manager or ConversationManager()
        self.handler = ConfirmationHandler(self.scratchpad, typo_detector=typo_detector)
        self.typo_detector = typo_detector

    def process_for_booking(self, user_message: str, extracted_data: dict,
                           intent=None, action_param: str = None) -> Tuple[str, Optional[ServiceRequest]]:
        """
        Main entry point: process user message through booking flow.
        Uses unified ConversationState instead of separate BookingStateMachine.

        Args:
            user_message: User's message text
            extracted_data: Extracted data dict
            intent: User's intent
            action_param: Optional explicit action from confirmation button (confirm/edit/cancel)

        Returns:
            (response_message, service_request_if_confirmed or None)
        """
        # Get current state from unified ConversationManager
        context = self.conversation_manager.get_or_create(self.conversation_id)
        current_state = context.state

        # CRITICAL DEBUG: Log state at entry
        import logging
        logger = logging.getLogger(__name__)
        logger.critical(f"🔍 process_for_booking ENTRY: conversation_id={self.conversation_id}, current_state={current_state}, action_param={action_param}, scratchpad_id={self.scratchpad.conversation_id}, scratchpad_completeness={self.scratchpad.get_completeness()}")

        # Step 1: Add extracted data to scratchpad
        self._add_extracted_data(extracted_data)

        # Step 2: Check if booking intent detected
        should_confirm = BookingIntentDetector.should_trigger_confirmation(
            user_message, intent, current_state.value
        )

        if should_confirm and current_state != ConversationState.CONFIRMATION:
            # Transition to confirmation in unified state machine
            self.conversation_manager.update_state(self.conversation_id, ConversationState.CONFIRMATION)
            summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)
            # Store confirmation message for typo detection
            self.handler.set_confirmation_message(summary)
            return summary, None

        # Step 3: Handle confirmation actions (if in confirmation state)
        if current_state == ConversationState.CONFIRMATION:
            # CRITICAL FIX: Use explicit action from API if provided (from /api/confirmation)
            # Otherwise, detect from user message (from chat API)
            if action_param:
                # Convert string action to ConfirmationAction enum
                action_lower = action_param.lower()
                if action_lower == "confirm":
                    action = ConfirmationAction.CONFIRM
                elif action_lower == "edit":
                    action = ConfirmationAction.EDIT
                elif action_lower == "cancel":
                    action = ConfirmationAction.CANCEL
                else:
                    action = ConfirmationAction.INVALID
            elif self.typo_detector:
                # Use typo detection if available
                action, typo_result = self.handler.detect_action_with_typo_check(user_message)

                # If typo detected, return suggestion
                if action == ConfirmationAction.TYPO_DETECTED and typo_result:
                    return typo_result["suggestion"], None
            else:
                action = self.handler.detect_action(user_message)

            if action == ConfirmationAction.CONFIRM:
                # Build service request and move to COMPLETED in unified state machine
                service_request = ServiceRequestBuilder.build(
                    self.scratchpad, self.conversation_id
                )

                # FOOLPROOF: Log the service request creation
                import logging
                logger = logging.getLogger(__name__)
                logger.critical(f"✅✅✅ SERVICE REQUEST CREATED: ID={service_request.service_request_id}, conversation_id={self.conversation_id}")

                # Update unified state to COMPLETED (fixes the bug!)
                self.conversation_manager.update_state(
                    self.conversation_id,
                    ConversationState.COMPLETED,
                    reason="User confirmed booking"
                )

                # FOOLPROOF: Store service_request_id in conversation metadata for recovery
                context = self.conversation_manager.get_or_create(self.conversation_id)
                context.metadata['service_request_id'] = service_request.service_request_id
                context.metadata['booking_confirmed_at'] = __import__('datetime').datetime.now().isoformat()

                return (f"Booking confirmed! Reference: {service_request.service_request_id}",
                        service_request)

            elif action == ConfirmationAction.EDIT:
                # Update scratchpad and re-show form
                # Stay in CONFIRMATION state while editing
                field_ref = self.handler.parse_edit_instruction(user_message)
                if field_ref:
                    # Extract value after field reference
                    parts = user_message.lower().split(field_ref, 1)
                    if len(parts) > 1:
                        new_value = parts[1].strip()
                        self.handler.handle_edit(f"{field_ref} {new_value}")
                summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)
                return summary, None

            elif action == ConfirmationAction.CANCEL:
                # Cancel booking - move to CANCELLED in unified state machine
                msg = self.handler.handle_cancel()
                self.conversation_manager.update_state(
                    self.conversation_id,
                    ConversationState.CANCELLED,
                    reason="User cancelled booking"
                )
                return msg, None

        # Step 4: Continue data collection (in other states)
        completeness = self.scratchpad.get_completeness()
        return (f"Thanks! Data saved ({completeness}% complete). "
               f"Feel free to continue."), None

    def _add_extracted_data(self, extracted_data: dict) -> None:
        """Add extracted data to scratchpad."""
        if not extracted_data:
            return

        turn = len(self.scratchpad.form.metadata.get("turns", [])) + 1

        for key, value in extracted_data.items():
            if value is None:
                continue

            # Map extracted fields to scratchpad sections
            section_map = {
                "first_name": ("customer", "first_name"),
                "last_name": ("customer", "last_name"),
                "phone": ("customer", "phone"),
                "email": ("customer", "email"),
                "vehicle_brand": ("vehicle", "brand"),
                "vehicle_model": ("vehicle", "model"),
                "appointment_date": ("appointment", "date"),
                "service_type": ("appointment", "service_type"),
            }

            if key in section_map:
                section, field_name = section_map[key]
                self.scratchpad.add_field(
                    section, field_name, value,
                    source="direct_extraction",
                    turn=turn,
                    confidence=0.85
                )

    def get_scratchpad(self) -> ScratchpadManager:
        """Get current scratchpad."""
        return self.scratchpad

    def get_state(self) -> ConversationState:
        """Get current unified conversation state."""
        return self.conversation_manager.get_or_create(self.conversation_id).state

    def is_complete(self) -> bool:
        """Check if booking is complete."""
        return self.get_state() == ConversationState.COMPLETED

    def reset(self) -> None:
        """Reset flow (for cancellation or new booking)."""
        self.scratchpad.clear_all()
        self.conversation_manager.update_state(
            self.conversation_id,
            ConversationState.GREETING,
            reason="Reset to start new booking"
        )
