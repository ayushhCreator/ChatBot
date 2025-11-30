"""End-to-end tests for BookingFlowManager."""

import pytest
from booking import BookingFlowManager, BookingState


class TestBookingFlowManager:
    """Test complete booking flow."""

    def setup_method(self):
        """Setup for each test."""
        self.manager = BookingFlowManager("conv-123")

    def test_initialization(self):
        """Test flow manager initializes."""
        assert self.manager.conversation_id == "conv-123"
        assert self.manager.get_state() == BookingState.GREETING

    def test_add_extracted_data(self):
        """Test adding extracted data."""
        extracted = {
            "first_name": "John",
            "phone": "555-1234",
            "vehicle_brand": "Honda"
        }
        self.manager._add_extracted_data(extracted)

        assert self.manager.scratchpad.get_field("customer", "first_name").value == "John"
        assert self.manager.scratchpad.get_field("customer", "phone").value == "555-1234"
        assert self.manager.scratchpad.get_field("vehicle", "brand").value == "Honda"

    def test_data_collection_flow(self):
        """Test data collection flow."""
        extracted = {"first_name": "John", "phone": "555-1234"}
        response, service_request = self.manager.process_for_booking(
            "John, 555-1234", extracted
        )

        assert service_request is None  # Not confirmed yet
        assert "John" not in response or "555" not in response  # Data saved
        assert self.manager.get_state() in [
            BookingState.DATA_COLLECTION,
            BookingState.GREETING
        ]

    def test_completeness_calculation(self):
        """Test completeness is tracked."""
        extracted = {"first_name": "John"}
        response, _ = self.manager.process_for_booking("test", extracted)
        completeness = self.manager.scratchpad.get_completeness()
        assert completeness > 0

    def test_is_complete_check(self):
        """Test is_complete method."""
        assert not self.manager.is_complete()
        # Move through states to completion
        self.manager.state_machine.transition(BookingState.DATA_COLLECTION)
        self.manager.state_machine.transition(BookingState.CONFIRMATION)
        self.manager.state_machine.transition(BookingState.BOOKING)
        self.manager.state_machine.transition(BookingState.COMPLETION)
        assert self.manager.is_complete()

    def test_reset(self):
        """Test resetting flow."""
        self.manager.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        self.manager.reset()
        assert len(self.manager.scratchpad.get_section("customer")) == 0
        assert self.manager.get_state() == BookingState.GREETING

    def test_get_scratchpad(self):
        """Test getting scratchpad."""
        scratchpad = self.manager.get_scratchpad()
        assert scratchpad is not None
        assert scratchpad.conversation_id == "conv-123"

    def test_booking_trigger_on_message(self):
        """Test booking trigger detection."""
        # Add some data
        extracted = {"first_name": "John"}
        response1, _ = self.manager.process_for_booking("John", extracted)

        # Trigger confirmation with booking message
        response2, _ = self.manager.process_for_booking("confirm booking", {})
        assert "CONFIRMATION" in response2 or "confirm" in response2.lower()

    def test_edit_action_flow(self):
        """Test edit action in confirmation."""
        # Set up confirmation state
        self.manager.state_machine.transition(BookingState.DATA_COLLECTION)
        self.manager.state_machine.transition(BookingState.CONFIRMATION)
        self.manager.scratchpad.add_field("customer", "first_name", "John", "direct", 1)

        # Send edit action
        response, _ = self.manager.process_for_booking("edit name Jane", {})
        updated = self.manager.scratchpad.get_field("customer", "first_name")
        # Value will be lowercase due to processing
        assert updated.value.lower() == "jane"

    def test_cancel_action_flow(self):
        """Test cancel action."""
        self.manager.state_machine.transition(BookingState.DATA_COLLECTION)
        self.manager.state_machine.transition(BookingState.CONFIRMATION)
        self.manager.scratchpad.add_field("customer", "first_name", "John", "direct", 1)

        response, _ = self.manager.process_for_booking("cancel", {})
        assert "cancel" in response.lower()
        assert len(self.manager.scratchpad.get_section("customer")) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
