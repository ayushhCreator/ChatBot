"""Tests for ScratchpadManager CRUD operations and metadata tracking."""

import pytest
from booking.scratchpad import ScratchpadManager


class TestScratchpadManager:
    """Test ScratchpadManager CRUD and metadata tracking."""

    def setup_method(self):
        """Create fresh scratchpad for each test."""
        self.scratchpad = ScratchpadManager()

    def test_add_field_customer(self):
        """Test adding customer field."""
        result = self.scratchpad.add_field(
            section="customer",
            field_name="first_name",
            value="John",
            source="direct_extraction",
            turn=1,
            confidence=0.95
        )
        assert result is True

        field = self.scratchpad.get_field("customer", "first_name")
        assert field.value == "John"
        assert field.source == "direct_extraction"
        assert field.turn == 1
        assert field.confidence == 0.95

    def test_add_multiple_fields(self):
        """Test adding fields to different sections."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 2)
        self.scratchpad.add_field("appointment", "date", "2024-12-11", "user_input", 3)

        assert self.scratchpad.get_field("customer", "first_name").value == "John"
        assert self.scratchpad.get_field("vehicle", "brand").value == "Honda"
        assert self.scratchpad.get_field("appointment", "date").value == "2024-12-11"

    def test_update_field(self):
        """Test updating existing field."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        result = self.scratchpad.update_field("customer", "first_name", "Jane")
        assert result is True
        assert self.scratchpad.get_field("customer", "first_name").value == "Jane"

    def test_delete_field(self):
        """Test removing field."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        result = self.scratchpad.delete_field("customer", "first_name")
        assert result is True
        assert self.scratchpad.get_field("customer", "first_name") is None

    def test_clear_section(self):
        """Test clearing entire section."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("customer", "phone", "555-0123", "direct_extraction", 2)

        # Clear using delete (since clear_section removed)
        self.scratchpad.delete_field("customer", "first_name")
        self.scratchpad.delete_field("customer", "phone")
        assert len(self.scratchpad.get_section("customer")) == 0

    def test_clear_all(self):
        """Test clearing entire scratchpad."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 2)

        self.scratchpad.clear_all()
        assert len(self.scratchpad.get_section("customer")) == 0
        assert len(self.scratchpad.get_section("vehicle")) == 0

    def test_invalid_section(self):
        """Test adding to invalid section."""
        result = self.scratchpad.add_field("invalid_section", "field", "value", "source", 1)
        assert result is False

    def test_completeness_calculation(self):
        """Test data completeness percentage."""
        assert self.scratchpad.get_completeness() == 0.0

        # Add 3 fields: 3/13 = 23.1%
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("customer", "phone", "555-0123", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 1)

        completeness = self.scratchpad.get_completeness()
        assert completeness == 23.1  # 3/13 * 100

    def test_is_complete_with_defaults(self):
        """Test completeness check with default required fields."""
        # Initially incomplete
        assert self.scratchpad.is_complete() is False

        # Add required fields
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("customer", "phone", "555-0123", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "model", "Civic", "direct_extraction", 1)
        self.scratchpad.add_field("appointment", "date", "2024-12-11", "direct_extraction", 1)
        self.scratchpad.add_field("appointment", "service_type", "Oil Change", "direct_extraction", 1)

        assert self.scratchpad.is_complete() is True

    def test_is_complete_custom_fields(self):
        """Test completeness check with custom required fields."""
        required = {
            "customer": ["first_name"],
            "vehicle": ["brand"]
        }
        assert self.scratchpad.is_complete(required) is False

        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        assert self.scratchpad.is_complete(required) is False

        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 1)
        assert self.scratchpad.is_complete(required) is True

    def test_export_json(self):
        """Test JSON export."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 2)

        json_str = self.scratchpad.export_json()
        assert "John" in json_str
        assert "Honda" in json_str
        assert "direct_extraction" in json_str

    def test_metadata_tracking(self):
        """Test metadata is properly tracked."""
        assert self.scratchpad.form.metadata["conversation_id"] == self.scratchpad.conversation_id
        assert "created_at" in self.scratchpad.form.metadata
        assert "data_completeness" in self.scratchpad.form.metadata

    def test_field_entry_timestamps(self):
        """Test that field entries have timestamps."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        field = self.scratchpad.get_field("customer", "first_name")
        assert field.timestamp is not None

    def test_get_all_fields(self):
        """Test getting all fields across sections."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct_extraction", 1)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct_extraction", 2)

        all_fields = self.scratchpad.get_all_fields()
        assert "customer" in all_fields
        assert "vehicle" in all_fields
        assert "appointment" in all_fields
        assert "metadata" in all_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])