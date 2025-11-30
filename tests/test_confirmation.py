"""Tests for ConfirmationGenerator."""

import pytest
from booking.scratchpad import ScratchpadManager
from booking.confirmation import ConfirmationGenerator


class TestConfirmationGenerator:
    """Test confirmation message generation."""

    def setup_method(self):
        """Create fresh scratchpad for each test."""
        self.scratchpad = ScratchpadManager()

    def test_generate_summary_full_data(self):
        """Test summary with all fields filled."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        self.scratchpad.add_field("customer", "last_name", "Smith", "direct", 1)
        self.scratchpad.add_field("customer", "phone", "555-1234", "direct", 2)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct", 3)
        self.scratchpad.add_field("vehicle", "model", "Civic", "direct", 3)
        self.scratchpad.add_field("appointment", "date", "2024-12-15", "direct", 4)
        self.scratchpad.add_field("appointment", "service_type", "Oil Change", "direct", 4)

        summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)

        assert "BOOKING CONFIRMATION" in summary
        assert "John Smith" in summary
        assert "555-1234" in summary
        assert "Honda Civic" in summary
        assert "2024-12-15" in summary
        assert "Oil Change" in summary

    def test_generate_summary_partial_data(self):
        """Test summary with some fields missing."""
        self.scratchpad.add_field("customer", "first_name", "Jane", "direct", 1)
        self.scratchpad.add_field("customer", "phone", "555-5678", "direct", 1)

        summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)

        assert "Jane" in summary
        assert "555-5678" in summary
        assert "VEHICLE DETAILS" not in summary  # No vehicle data

    def test_generate_summary_empty(self):
        """Test summary with no data."""
        summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)

        assert "BOOKING CONFIRMATION" in summary
        assert "[Edit] [Confirm] [Cancel]" in summary

    def test_generate_with_sources(self):
        """Test detailed summary with sources."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1, 0.95)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "retroactive_extraction", 3, 0.87)

        summary = ConfirmationGenerator.generate_with_sources(self.scratchpad.form)

        assert "John" in summary
        assert "95%" in summary
        assert "direct_extraction" in summary
        assert "Honda" in summary
        assert "87%" in summary
        assert "retroactive_extraction" in summary

    def test_is_empty_true(self):
        """Test is_empty returns True for empty scratchpad."""
        assert ConfirmationGenerator.is_empty(self.scratchpad.form) is True

    def test_is_empty_false(self):
        """Test is_empty returns False when data present."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        assert ConfirmationGenerator.is_empty(self.scratchpad.form) is False

    def test_formatting(self):
        """Test formatting includes expected emojis and structure."""
        self.scratchpad.add_field("customer", "first_name", "Test", "direct", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct", 1)
        self.scratchpad.add_field("appointment", "date", "2024-12-15", "direct", 1)

        summary = ConfirmationGenerator.generate_summary(self.scratchpad.form)

        assert "📋" in summary  # Header emoji
        assert "👤" in summary  # Customer emoji
        assert "🚗" in summary  # Vehicle emoji
        assert "📅" in summary  # Appointment emoji
        assert "═" in summary   # Separator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
