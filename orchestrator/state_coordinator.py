"""
State Coordinator - Manages conversation state transitions.

Single Responsibility: Determine next state based on extracted data, sentiment, and user input.
Reason to change: State machine logic changes.
"""
import logging
from typing import Dict, Any, Optional
from config import ConversationState, StateTransitionRules
from models import ValidatedSentimentScores

logger = logging.getLogger(__name__)


class StateCoordinator:
    """
    Coordinates state transitions in the conversation flow.

    Follows Single Responsibility Principle (SRP):
    - Only handles state transition logic
    - Does NOT handle data extraction, sentiment analysis, or response generation
    - Uses StateTransitionRules from config as single source of truth
    """

    def can_transition(self, from_state: ConversationState, to_state: ConversationState) -> bool:
        """Check if a state transition is valid."""
        if from_state not in StateTransitionRules.VALID_TRANSITIONS:
            return False
        return to_state in StateTransitionRules.VALID_TRANSITIONS[from_state]

    def determine_next_state(
        self,
        current_state: ConversationState,
        sentiment: Optional[ValidatedSentimentScores],
        extracted_data: Optional[Dict[str, Any]],
        user_message: str,
        all_required_fields_present: bool = False,
        can_advance_from_current_state: bool = True
    ) -> ConversationState:
        """
        Determine next state based on sentiment, extracted data, and required field completion.

        Args:
            current_state: Current conversation state
            sentiment: Validated sentiment scores
            extracted_data: Data extracted from user message
            user_message: Raw user message
            all_required_fields_present: Whether all required CONFIRMATION fields are collected
            can_advance_from_current_state: Whether all required fields for CURRENT state are met

        Returns:
            Next conversation state (validated against StateTransitionRules)
        """
        # If angry/upset, offer help instead of pushing forward
        if sentiment and sentiment.anger > 6.0:
            if self.can_transition(current_state, ConversationState.SERVICE_SELECTION):
                return ConversationState.SERVICE_SELECTION

        # CRITICAL FIX: Check for explicit confirmation keywords BEFORE applying the gate
        # BUT only jump to CONFIRMATION if ALL required fields are present
        # This prevents incomplete bookings while still allowing user intent to override state progression
        confirm_keywords = ["confirm", "yes", "ok", "okay", "book", "proceed", "finalize", "haan", "book now", "let's go", "schedule it"]
        user_explicitly_confirming = any(kw in user_message.lower() for kw in confirm_keywords)

        if user_explicitly_confirming and current_state in [ConversationState.DATE_SELECTION, ConversationState.VEHICLE_DETAILS, ConversationState.NAME_COLLECTION]:
            # User is explicitly requesting confirmation
            # CRITICAL: Only jump if we have ALL required fields for CONFIRMATION
            if all_required_fields_present and self.can_transition(current_state, ConversationState.CONFIRMATION):
                logger.info(f"🚀 EXPLICIT CONFIRMATION: User said '{user_message}' - jumping to CONFIRMATION from {current_state.value}")
                return ConversationState.CONFIRMATION
            elif not all_required_fields_present:
                # User wants to confirm but missing data - stay in current state and let gate handle it
                logger.warning(f"⚠️  EXPLICIT CONFIRMATION ATTEMPTED: User said '{user_message}' but missing required fields - staying in {current_state.value}")
                return current_state

        # CRITICAL GATE: Only allow state advancement if we have all required fields for CURRENT state
        # This prevents skipping states and ensures users can provide data in any order
        if not can_advance_from_current_state:
            logger.warning(f"⛔ GATE: Cannot advance from {current_state.value} - missing required fields")
            return current_state  # Stay in current state until requirements met

        # CRITICAL FIX: If all required fields present AND in CONFIRMATION, check user action
        # This handles both /chat (keyword-based) and /api/confirmation (endpoint-based) flows
        if current_state == ConversationState.CONFIRMATION:
            if all_required_fields_present:
                # Check for explicit cancel keywords
                cancel_keywords = ["cancel", "abort", "discard", "forget"]
                if any(kw in user_message.lower() for kw in cancel_keywords):
                    if self.can_transition(current_state, ConversationState.CANCELLED):
                        return ConversationState.CANCELLED
                # Check for edit keywords
                edit_keywords = ["edit", "change", "update", "correct", "modify"]
                if any(kw in user_message.lower() for kw in edit_keywords):
                    if self.can_transition(current_state, ConversationState.DATE_SELECTION):
                        return ConversationState.DATE_SELECTION
                # CRITICAL FIX: Only transition to COMPLETED if user explicitly confirms
                # Check for confirmation keywords (yes, confirm, okay, book, etc.)
                confirm_keywords = ["yes", "confirm", "ok", "okay", "book", "proceed", "finalize", "haan"]
                if any(kw in user_message.lower() for kw in confirm_keywords):
                    if self.can_transition(current_state, ConversationState.COMPLETED):
                        logger.info(f"✅ CONFIRMATION: User confirmed with '{user_message}' - transitioning to COMPLETED")
                        return ConversationState.COMPLETED
                # If no confirmation keywords, stay in CONFIRMATION state
                logger.warning(f"⏸️  CONFIRMATION: Waiting for user confirmation (message: '{user_message}')")
                return current_state

        # If data extracted, advance state based on data type
        if extracted_data:
            # Name extraction - move to NAME_COLLECTION
            if any(k in extracted_data for k in ["first_name", "full_name"]):
                if current_state in [ConversationState.GREETING, ConversationState.SERVICE_SELECTION]:
                    if self.can_transition(current_state, ConversationState.NAME_COLLECTION):
                        return ConversationState.NAME_COLLECTION

            # Phone extraction - advance from NAME_COLLECTION
            if "phone" in extracted_data:
                if current_state == ConversationState.NAME_COLLECTION:
                    if self.can_transition(current_state, ConversationState.VEHICLE_DETAILS):
                        return ConversationState.VEHICLE_DETAILS

            # Vehicle extraction - move to VEHICLE_DETAILS
            if any(k in extracted_data for k in ["vehicle_brand", "vehicle_model", "vehicle_plate"]):
                if current_state in [ConversationState.NAME_COLLECTION, ConversationState.SERVICE_SELECTION]:
                    if self.can_transition(current_state, ConversationState.VEHICLE_DETAILS):
                        return ConversationState.VEHICLE_DETAILS
                elif current_state == ConversationState.VEHICLE_DETAILS:
                    if self.can_transition(current_state, ConversationState.DATE_SELECTION):
                        return ConversationState.DATE_SELECTION

            # Date extraction - move to DATE_SELECTION or CONFIRMATION
            if "appointment_date" in extracted_data:
                if current_state in [ConversationState.VEHICLE_DETAILS, ConversationState.SERVICE_SELECTION]:
                    if self.can_transition(current_state, ConversationState.DATE_SELECTION):
                        return ConversationState.DATE_SELECTION
                elif current_state == ConversationState.DATE_SELECTION:
                    # Move to CONFIRMATION (actual confirmation happens when user confirms)
                    if self.can_transition(current_state, ConversationState.CONFIRMATION):
                        return ConversationState.CONFIRMATION

            # General progression from NAME_COLLECTION
            if current_state == ConversationState.NAME_COLLECTION:
                if self.can_transition(current_state, ConversationState.VEHICLE_DETAILS):
                    return ConversationState.VEHICLE_DETAILS
            elif current_state == ConversationState.VEHICLE_DETAILS:
                if self.can_transition(current_state, ConversationState.DATE_SELECTION):
                    return ConversationState.DATE_SELECTION
            elif current_state == ConversationState.DATE_SELECTION:
                if self.can_transition(current_state, ConversationState.CONFIRMATION):
                    return ConversationState.CONFIRMATION

        # If user asks about services/pricing, go to service selection (but allow escape)
        service_keywords = ["service", "price", "cost", "offer", "plan", "what do you"]
        if any(kw in user_message.lower() for kw in service_keywords):
            if current_state == ConversationState.GREETING:
                if self.can_transition(current_state, ConversationState.SERVICE_SELECTION):
                    return ConversationState.SERVICE_SELECTION

        # Otherwise stay in current state
        return current_state

    def determine_state_change_reason(
        self,
        user_message: str,
        sentiment: Optional[ValidatedSentimentScores],
        extracted_data: Optional[Dict[str, Any]]
    ) -> str:
        """
        Determine human-readable reason for state change.

        Args:
            user_message: Raw user message
            sentiment: Validated sentiment scores
            extracted_data: Data extracted from user message

        Returns:
            Human-readable reason string
        """
        if extracted_data:
            data_type = list(extracted_data.keys())[0]
            return f"Extracted {data_type} from message"
        if sentiment and sentiment.anger > 6.0:
            return "Customer upset - offering service selection"
        return "User interest detected"