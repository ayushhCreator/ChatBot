"""Tests for ServiceRequest and ServiceRequestBuilder."""

import pytest
from booking import (
    ScratchpadManager, ServiceRequest, ServiceRequestBuilder
)


class TestServiceRequest:
    """Test ServiceRequest model."""

    def test_create_service_request(self):
        """Test creating service request."""
        request = ServiceRequest(conversation_id="conv-123")
        assert request.service_request_id.startswith("SR-")
        assert request.conversation_id == "conv-123"
        assert request.status == "confirmed"

    def test_service_request_has_audit_trail(self):
        """Test audit trail in service request."""
        request = ServiceRequest(conversation_id="conv-123")
        assert hasattr(request, "collection_sources")
        assert isinstance(request.collection_sources, list)


class TestServiceRequestBuilder:
    """Test ServiceRequestBuilder."""

    def setup_method(self):
        """Setup for each test."""
        self.scratchpad = ScratchpadManager("conv-123")

    def test_build_from_full_scratchpad(self):
        """Test building request from full scratchpad."""
        # Add full data
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        self.scratchpad.add_field("customer", "phone", "555-1234", "direct", 2)
        self.scratchpad.add_field("vehicle", "brand", "Honda", "direct", 3)
        self.scratchpad.add_field("appointment", "date", "2024-12-15", "direct", 4)

        request = ServiceRequestBuilder.build(self.scratchpad, "conv-123")

        assert request.conversation_id == "conv-123"
        assert request.customer["first_name"] == "John"
        assert request.customer["phone"] == "555-1234"
        assert request.vehicle["brand"] == "Honda"
        assert request.appointment["date"] == "2024-12-15"

    def test_build_from_partial_scratchpad(self):
        """Test building with partial data."""
        self.scratchpad.add_field("customer", "first_name", "Jane", "direct", 1)
        request = ServiceRequestBuilder.build(self.scratchpad, "conv-123")

        assert request.customer["first_name"] == "Jane"
        assert len(request.vehicle) == 0  # No vehicle data

    def test_audit_trail_generation(self):
        """Test audit trail is generated."""
        self.scratchpad.add_field(
            "customer", "first_name", "John",
            "direct_extraction", 1, 0.95, "dspy"
        )
        request = ServiceRequestBuilder.build(self.scratchpad, "conv-123")

        assert len(request.collection_sources) > 0
        source = request.collection_sources[0]
        assert source.field_name == "customer.first_name"
        assert source.source == "direct_extraction"
        assert source.confidence == 0.95

    def test_service_request_has_timestamps(self):
        """Test timestamps are set."""
        request = ServiceRequestBuilder.build(self.scratchpad, "conv-123")
        assert request.created_at is not None
        assert request.confirmed_at is not None

    def test_to_dict_conversion(self):
        """Test converting to dict."""
        request = ServiceRequest(conversation_id="conv-123")
        data = ServiceRequestBuilder.to_dict(request)
        assert isinstance(data, dict)
        assert data["conversation_id"] == "conv-123"

    def test_from_dict_conversion(self):
        """Test creating from dict."""
        data = {
            "conversation_id": "conv-123",
            "customer": {"name": "John"},
            "vehicle": {},
            "appointment": {},
            "collection_sources": [],
            "status": "confirmed"
        }
        request = ServiceRequestBuilder.from_dict(data)
        assert request.conversation_id == "conv-123"

    def test_extract_section(self):
        """Test section extraction."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        self.scratchpad.add_field("customer", "phone", "555-1234", "direct", 2)

        customer = ServiceRequestBuilder._extract_section(self.scratchpad, "customer")
        assert customer["first_name"] == "John"
        assert customer["phone"] == "555-1234"

    def test_empty_values_excluded(self):
        """Test that None values are excluded."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        request = ServiceRequestBuilder.build(self.scratchpad, "conv-123")
        # Should not include None values
        assert "phone" not in request.customer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
