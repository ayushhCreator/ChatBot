"""ServiceRequest: Build backend booking request from confirmed scratchpad."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from booking.scratchpad import ScratchpadManager


class CollectionSource(BaseModel):
    """Track where a field came from."""
    field_name: str
    source: str
    turn: Optional[int] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None


class ServiceRequest(BaseModel):
    """Final booking record sent to backend."""
    service_request_id: str = Field(default_factory=lambda: f"SR-{uuid4().hex[:8].upper()}")
    conversation_id: str

    customer: Dict[str, Any] = Field(default_factory=dict)
    vehicle: Dict[str, Any] = Field(default_factory=dict)
    appointment: Dict[str, Any] = Field(default_factory=dict)

    collection_sources: List[CollectionSource] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.now)
    confirmed_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="confirmed")


class ServiceRequestBuilder:
    """Build ServiceRequest from scratchpad."""

    @staticmethod
    def build(scratchpad: ScratchpadManager, conversation_id: str) -> ServiceRequest:
        """
        Transform scratchpad (collection) → ServiceRequest (database record).

        Returns:
            ServiceRequest ready for API POST
        """
        # Extract data from each section
        customer_data = ServiceRequestBuilder._extract_section(scratchpad, "customer")
        vehicle_data = ServiceRequestBuilder._extract_section(scratchpad, "vehicle")
        appointment_data = ServiceRequestBuilder._extract_section(scratchpad, "appointment")

        # Build audit trail
        sources = ServiceRequestBuilder._build_sources(scratchpad)

        return ServiceRequest(
            conversation_id=conversation_id,
            customer=customer_data,
            vehicle=vehicle_data,
            appointment=appointment_data,
            collection_sources=sources,
            confirmed_at=datetime.now(),
            status="confirmed"
        )

    @staticmethod
    def _extract_section(scratchpad: ScratchpadManager, section: str) -> Dict[str, Any]:
        """Extract values from scratchpad section."""
        data = {}
        section_dict = scratchpad.get_section(section)

        for field_name, field_entry in section_dict.items():
            if field_entry.value is not None:
                data[field_name] = field_entry.value

        return data

    @staticmethod
    def _build_sources(scratchpad: ScratchpadManager) -> List[CollectionSource]:
        """Build audit trail from scratchpad metadata."""
        sources = []
        form = scratchpad.form

        for section_name in ["customer", "vehicle", "appointment"]:
            section = getattr(form, section_name)
            for field_name, field_entry in section.items():
                if field_entry.value is not None:
                    sources.append(CollectionSource(
                        field_name=f"{section_name}.{field_name}",
                        source=field_entry.source or "unknown",
                        turn=field_entry.turn,
                        confidence=field_entry.confidence,
                        extraction_method=field_entry.extraction_method
                    ))

        return sources

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ServiceRequest:
        """Create ServiceRequest from dict."""
        return ServiceRequest(**data)

    @staticmethod
    def to_dict(request: ServiceRequest) -> Dict[str, Any]:
        """Convert ServiceRequest to dict."""
        return request.model_dump(mode="json")
