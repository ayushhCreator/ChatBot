"""BookingStateMachine: Track conversation state through booking flow."""

from enum import Enum


class BookingState(str, Enum):
    """Possible states in booking conversation."""
    GREETING = "greeting"
    DATA_COLLECTION = "data_collection"
    CONFIRMATION = "confirmation"
    BOOKING = "booking"
    COMPLETION = "completion"
    CANCELLED = "cancelled"


class BookingStateMachine:
    """State machine for booking flow."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        BookingState.GREETING: [BookingState.DATA_COLLECTION],
        BookingState.DATA_COLLECTION: [BookingState.CONFIRMATION, BookingState.DATA_COLLECTION],
        BookingState.CONFIRMATION: [
            BookingState.BOOKING,
            BookingState.DATA_COLLECTION,  # edit action
            BookingState.CANCELLED
        ],
        BookingState.BOOKING: [BookingState.COMPLETION, BookingState.CANCELLED],
        BookingState.COMPLETION: [BookingState.GREETING],
        BookingState.CANCELLED: [BookingState.GREETING],
    }

    def __init__(self, initial_state: BookingState = BookingState.GREETING):
        self.current_state = initial_state
        self.history = [initial_state]

    def can_transition(self, to_state: BookingState) -> bool:
        """Check if transition from current to target state is valid."""
        if self.current_state not in self.VALID_TRANSITIONS:
            return False
        allowed = self.VALID_TRANSITIONS[self.current_state]
        return to_state in allowed

    def transition(self, new_state: BookingState) -> bool:
        """Transition to new state if valid."""
        if not self.can_transition(new_state):
            return False
        self.current_state = new_state
        self.history.append(new_state)
        return True

    def get_current_state(self) -> BookingState:
        """Get current state."""
        return self.current_state

    def get_history(self) -> list:
        """Get state transition history."""
        return self.history.copy()

    def reset(self) -> None:
        """Reset to greeting state."""
        self.current_state = BookingState.GREETING
        self.history = [BookingState.GREETING]

    def is_booking_complete(self) -> bool:
        """Check if booking is completed."""
        return self.current_state == BookingState.COMPLETION

    def is_cancelled(self) -> bool:
        """Check if booking was cancelled."""
        return self.current_state == BookingState.CANCELLED

    def __str__(self) -> str:
        return f"BookingStateMachine(state={self.current_state.value})"
