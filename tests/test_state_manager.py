"""Tests for BookingStateMachine."""

import pytest
from booking import BookingState, BookingStateMachine


class TestBookingStateMachine:
    """Test state machine transitions."""

    def test_initial_state(self):
        """Test initial state is greeting."""
        machine = BookingStateMachine()
        assert machine.get_current_state() == BookingState.GREETING

    def test_greeting_to_data_collection(self):
        """Test valid transition."""
        machine = BookingStateMachine()
        assert machine.can_transition(BookingState.DATA_COLLECTION)
        assert machine.transition(BookingState.DATA_COLLECTION)
        assert machine.get_current_state() == BookingState.DATA_COLLECTION

    def test_data_collection_to_confirmation(self):
        """Test data collection to confirmation."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        assert machine.can_transition(BookingState.CONFIRMATION)
        assert machine.transition(BookingState.CONFIRMATION)
        assert machine.get_current_state() == BookingState.CONFIRMATION

    def test_confirmation_to_booking(self):
        """Test confirmation to booking."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        assert machine.transition(BookingState.BOOKING)
        assert machine.get_current_state() == BookingState.BOOKING

    def test_booking_to_completion(self):
        """Test booking completion."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        machine.transition(BookingState.BOOKING)
        assert machine.transition(BookingState.COMPLETION)
        assert machine.is_booking_complete()

    def test_confirmation_edit_loop(self):
        """Test edit action returns to data collection."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        assert machine.can_transition(BookingState.DATA_COLLECTION)
        assert machine.transition(BookingState.DATA_COLLECTION)

    def test_invalid_transition_blocked(self):
        """Test invalid transition is blocked."""
        machine = BookingStateMachine()
        # Can't go straight from greeting to confirmation
        assert not machine.can_transition(BookingState.CONFIRMATION)
        assert not machine.transition(BookingState.CONFIRMATION)

    def test_cancel_from_confirmation(self):
        """Test cancellation from confirmation."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        assert machine.transition(BookingState.CANCELLED)
        assert machine.is_cancelled()

    def test_reset(self):
        """Test reset returns to greeting."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        machine.reset()
        assert machine.get_current_state() == BookingState.GREETING
        assert len(machine.get_history()) == 1

    def test_history_tracking(self):
        """Test state transition history."""
        machine = BookingStateMachine()
        machine.transition(BookingState.DATA_COLLECTION)
        machine.transition(BookingState.CONFIRMATION)
        history = machine.get_history()
        assert len(history) == 3
        assert history[0] == BookingState.GREETING
        assert history[1] == BookingState.DATA_COLLECTION
        assert history[2] == BookingState.CONFIRMATION

    def test_string_representation(self):
        """Test string representation."""
        machine = BookingStateMachine()
        s = str(machine)
        assert "greeting" in s.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
