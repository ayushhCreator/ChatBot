"""ScratchpadManager: Single source of truth for collected booking data."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
import json
from uuid import uuid4


class FieldEntry(BaseModel):
    """Single scraped field with metadata."""
    value: Optional[Any] = None
    source: Optional[str] = None
    turn: Optional[int] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    timestamp: Optional[datetime] = None

    # RACE CONDITION FIX: Edit tracking for turn-based conflict resolution
    edit_source: Optional[str] = None  # "user_input" | "user_edit" | "retroactive" | "initial_entry"
    previous_value: Optional[Any] = None  # For undo capability
    edited_at: Optional[datetime] = None  # Explicit edit timestamp (for ordering within same turn)


class ScratchpadForm(BaseModel):
    """Three-section scratchpad for booking data."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    customer: Dict[str, FieldEntry] = Field(default_factory=dict)
    vehicle: Dict[str, FieldEntry] = Field(default_factory=dict)
    appointment: Dict[str, FieldEntry] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScratchpadManager:
    """CRUD + completeness tracking for scratchpad."""

    def __init__(self, conversation_id: Optional[str] = None):
        self.form = ScratchpadForm()
        self.conversation_id = conversation_id or str(uuid4())
        self.created_at = datetime.now()
        self.form.metadata = {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "data_completeness": 0.0
        }

    def add_field(self, section: str, field_name: str, value: Any, source: str,
                  turn: int, confidence: float = 1.0, extraction_method: str = "user",
                  edit_source: str = "initial_entry") -> bool:
        """Add or update field with turn-based conflict resolution.

        RACE CONDITION FIX:
        - Accept new value if: new_turn > existing_turn (newer data always wins)
        - Reject new value if: new_turn <= existing_turn (preserve existing)
        - Per-conversation isolation: Each conversation_id has independent scratchpad

        Args:
            edit_source: "user_input" | "user_edit" | "retroactive" | "initial_entry"
        """
        import logging
        logger = logging.getLogger(__name__)

        if section not in ["customer", "vehicle", "appointment"]:
            return False

        # Skip invalid values
        if value is None or str(value).lower() in ["unknown", "none", ""]:
            return False

        section_dict = getattr(self.form, section)
        existing_entry = section_dict.get(field_name)

        # CRITICAL: Turn-based conflict resolution
        if existing_entry and existing_entry.turn is not None:
            # Newer turn always wins
            if turn <= existing_entry.turn:
                logger.debug(f"⏭️  SKIP: {section}.{field_name} turn {turn} <= existing {existing_entry.turn}")
                return False

            # Store previous value for undo
            previous_value = existing_entry.value
        else:
            previous_value = None

        # Update or create field with edit tracking
        section_dict[field_name] = FieldEntry(
            value=value,
            source=source,
            turn=turn,
            confidence=confidence,
            extraction_method=extraction_method,
            timestamp=datetime.now(),
            edit_source=edit_source,
            previous_value=previous_value,
            edited_at=datetime.now()
        )
        self._update_completeness()
        logger.debug(f"✅ FIELD SET: {section}.{field_name}={value} (turn={turn}, source={edit_source})")
        return True

    def get_field(self, section: str, field_name: str) -> Optional[FieldEntry]:
        """Get field entry with metadata."""
        if section not in ["customer", "vehicle", "appointment"]:
            return None
        return getattr(self.form, section).get(field_name)

    def get_section(self, section: str) -> Dict[str, FieldEntry]:
        """Get entire section."""
        if section not in ["customer", "vehicle", "appointment"]:
            return {}
        return getattr(self.form, section)

    def get_all_fields(self) -> Dict:
        """Get all fields with metadata."""
        return {
            "customer": dict(self.form.customer),
            "vehicle": dict(self.form.vehicle),
            "appointment": dict(self.form.appointment),
            "metadata": self.form.metadata
        }

    def update_field(self, section: str, field_name: str, new_value: Any) -> bool:
        """Update field value."""
        if not self.get_field(section, field_name):
            return False
        getattr(self.form, section)[field_name].value = new_value
        self._update_completeness()
        return True

    def delete_field(self, section: str, field_name: str) -> bool:
        """Remove field."""
        section_dict = getattr(self.form, section, {})
        if field_name in section_dict:
            del section_dict[field_name]
            self._update_completeness()
            return True
        return False

    def clear_all(self) -> None:
        """Clear scratchpad."""
        self.form.customer.clear()
        self.form.vehicle.clear()
        self.form.appointment.clear()
        self.form.metadata["data_completeness"] = 0.0

    def _update_completeness(self) -> None:
        """Recalculate completeness % with distinction between required and optional fields."""
        from config import config
        import logging
        logger = logging.getLogger(__name__)

        # Count filled fields across all sections
        # IMPORTANT: Don't count fields with "Unknown" or placeholder values as filled
        filled = sum(len([v for v in getattr(self.form, s).values()
                         if v.value and str(v.value).lower() not in ["unknown", "none", ""]])
                     for s in ["customer", "vehicle", "appointment"])

        # REQUIRED FIELDS (8): Minimum to identify user, car, and requirement
        # first_name, last_name, phone, vehicle_brand, vehicle_model, vehicle_plate, appointment_date, intent
        required_fields = ["first_name", "last_name", "phone"]  # customer
        required_fields += ["brand", "model", "plate"]           # vehicle
        required_fields += ["date"]                              # appointment
        # Note: intent/service_type is captured separately

        # Count how many required fields are filled
        # IMPORTANT: Don't count fields with "Unknown" or placeholder values as filled
        filled_required = 0
        for section in ["customer", "vehicle", "appointment"]:
            section_data = getattr(self.form, section)
            for field_name in required_fields:
                if field_name in section_data and section_data[field_name].value:
                    # Check if value is not a placeholder
                    value_str = str(section_data[field_name].value).lower()
                    if value_str not in ["unknown", "none", ""]:
                        filled_required += 1

        # Calculate both metrics
        required_for_booking = config.REQUIRED_FIELDS_FOR_BOOKING
        total_possible = config.TOTAL_POSSIBLE_FIELDS

        # Completeness is based on TOTAL POSSIBLE fields (for UI progress)
        completeness_pct = round((filled / total_possible) * 100, 1)

        # Cap completeness at 100% to prevent validation errors
        if completeness_pct > 100.0:
            completeness_pct = 100.0
            logger.warning(f"⚠️  SCRATCHPAD: Capped completeness at 100% (calculated {round((filled / total_possible) * 100, 1)}%, filled={filled}/{total_possible})")

        # Check if minimum booking requirements are met
        is_bookable = filled_required >= (required_for_booking - 1)  # -1 because intent is separate

        self.form.metadata["data_completeness"] = completeness_pct
        self.form.metadata["is_bookable"] = is_bookable
        self.form.metadata["filled_required_fields"] = filled_required

        if is_bookable:
            logger.info(f"✅ BOOKING READY: {filled_required} required fields filled, completeness={completeness_pct}%")

    def get_completeness(self) -> float:
        """Get completeness percentage."""
        return self.form.metadata.get("data_completeness", 0.0)

    def is_complete(self, required: Optional[Dict[str, list]] = None) -> bool:
        """Check if required fields present."""
        if not required:
            required = {"customer": ["first_name", "phone"],
                       "vehicle": ["brand", "model"],
                       "appointment": ["date", "service_type"]}
        for section, fields in required.items():
            for field in fields:
                if field not in getattr(self.form, section) or \
                   getattr(self.form, section)[field].value is None:
                    return False
                # IMPORTANT: Don't count placeholder values as complete
                value_str = str(getattr(self.form, section)[field].value).lower()
                if value_str in ["unknown", "none", ""]:
                    return False
        return True

    def set_time_slot(self, validated_time_slot: Any) -> bool:
        """
        Set time_slot from ValidatedTimeSlot object.

        Handles both ValidatedTimeSlot objects and simple slot names.

        Args:
            validated_time_slot: ValidatedTimeSlot object or slot name string

        Returns:
            True if successfully set, False otherwise
        """
        from models import ValidatedTimeSlot
        import logging

        logger = logging.getLogger(__name__)

        if validated_time_slot is None:
            return False

        try:
            # If it's a ValidatedTimeSlot object, extract the slot name
            if isinstance(validated_time_slot, ValidatedTimeSlot):
                slot_name = validated_time_slot.slot_name.value
                slot_label = validated_time_slot.label
                confidence = validated_time_slot.metadata.confidence
                extraction_method = validated_time_slot.metadata.extraction_method

                success = self.add_field(
                    section="appointment",
                    field_name="time_slot",
                    value=slot_name,
                    source=f"ValidatedTimeSlot:{slot_label}",
                    turn=0,
                    confidence=confidence,
                    extraction_method=extraction_method
                )

                if success:
                    logger.info(f"✅ TIME SLOT SET: {slot_label} ({slot_name})")
                return success

            # If it's a string, validate and set directly
            elif isinstance(validated_time_slot, str):
                from config import config

                if validated_time_slot not in config.TIME_SLOTS:
                    logger.warning(f"⚠️  INVALID TIME SLOT: '{validated_time_slot}'")
                    return False

                slot_label = config.TIME_SLOTS[validated_time_slot]["label"]
                success = self.add_field(
                    section="appointment",
                    field_name="time_slot",
                    value=validated_time_slot,
                    source=f"config.TIME_SLOTS:{slot_label}",
                    turn=0,
                    confidence=1.0,
                    extraction_method="rule_based"
                )

                if success:
                    logger.info(f"✅ TIME SLOT SET: {slot_label} ({validated_time_slot})")
                return success

            else:
                logger.warning(f"❌ INVALID TIME SLOT TYPE: {type(validated_time_slot)}")
                return False

        except Exception as e:
            logger.error(f"❌ FAILED TO SET TIME SLOT: {type(e).__name__}: {e}")
            return False

    def get_time_slot(self) -> Optional[str]:
        """
        Get time_slot from appointment section.

        Returns:
            Slot name (early_morning, afternoon, evening) or None
        """
        field = self.get_field("appointment", "time_slot")
        return field.value if field else None

    def get_time_slot_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed time_slot information from config.

        Returns:
            Dict with label, start, end, description or None if not set
        """
        from config import config

        slot_name = self.get_time_slot()
        if not slot_name or slot_name not in config.TIME_SLOTS:
            return None

        return config.TIME_SLOTS[slot_name]

    def export_json(self) -> str:
        """Export as JSON."""
        return json.dumps({
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.form.metadata,
            "customer": {k: v.model_dump() for k, v in self.form.customer.items()},
            "vehicle": {k: v.model_dump() for k, v in self.form.vehicle.items()},
            "appointment": {k: v.model_dump() for k, v in self.form.appointment.items()}
        }, default=str)

    def __repr__(self) -> str:
        return f"ScratchpadManager(id={self.conversation_id[:8]}..., {self.get_completeness()}%)"