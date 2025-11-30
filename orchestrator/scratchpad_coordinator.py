"""
Scratchpad Coordinator - Manages scratchpad updates during data collection.

Single Responsibility: Update scratchpad based on extracted data and state.
Reason to change: Scratchpad update logic changes.

Handles both REQUIRED and OPTIONAL fields with overwrite protection:
- REQUIRED: first_name, last_name, phone, vehicle_brand, vehicle_model, vehicle_plate, appointment_date
- OPTIONAL: service_type, service_tier, vehicle_type, time_slot, notes, address

Protection logic:
1. Don't overwrite explicit mentions with inferred values
2. Track extraction method (explicit vs inferred vs fallback)
3. Log all field updates for audit trail
"""
import logging
from typing import Dict, Any
from config import ConversationState
from booking.scratchpad import ScratchpadManager

logger = logging.getLogger(__name__)


class ScratchpadCoordinator:
    """
    Coordinates scratchpad updates based on extracted data and conversation state.

    Follows Single Responsibility Principle (SRP):
    - Only handles scratchpad creation and updates
    - Does NOT handle data extraction or state transitions
    """

    def __init__(self):
        """Initialize scratchpad coordinator with manager storage."""
        self.scratchpad_managers: Dict[str, ScratchpadManager] = {}

    def get_or_create(self, conversation_id: str) -> ScratchpadManager:
        """
        Get existing scratchpad or create new one for conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            ScratchpadManager instance
        """
        if conversation_id not in self.scratchpad_managers:
            self.scratchpad_managers[conversation_id] = ScratchpadManager(conversation_id)
        return self.scratchpad_managers[conversation_id]

    def update_from_extraction(
        self,
        scratchpad: ScratchpadManager,
        state: ConversationState,
        field_name: str,
        value: Any
    ) -> None:
        """
        Update scratchpad based on extracted data field and current state.

        Args:
            scratchpad: Scratchpad manager instance
            state: Current conversation state
            field_name: Name of extracted field
            value: Extracted value

        Note:
            Maps extracted fields to scratchpad sections based on state:
            - NAME_COLLECTION → customer section
            - VEHICLE_DETAILS → vehicle section
            - DATE_SELECTION → appointment section
        """
        # Map extracted fields to scratchpad sections
        if state == ConversationState.NAME_COLLECTION:
            section = "customer"
            # Map field names
            if field_name in ["first_name", "last_name", "full_name"]:
                scratchpad.add_field(section, field_name, value, "extraction", turn=0)

        elif state == ConversationState.VEHICLE_DETAILS:
            section = "vehicle"
            # Map vehicle fields
            field_mapping = {
                "vehicle_brand": "brand",
                "vehicle_model": "model",
                "vehicle_plate": "plate"
            }
            scratchpad_field = field_mapping.get(field_name, field_name)
            scratchpad.add_field(section, scratchpad_field, value, "extraction", turn=0)

        elif state == ConversationState.DATE_SELECTION:
            section = "appointment"
            field_mapping = {
                "appointment_date": "date"
            }
            scratchpad_field = field_mapping.get(field_name, field_name)
            scratchpad.add_field(section, scratchpad_field, value, "extraction", turn=0)

    def add_optional_fields(
        self,
        scratchpad: ScratchpadManager,
        optional_data: Dict[str, Any]
    ) -> None:
        """
        Add optional/enhanced fields to scratchpad with overwrite protection.

        Optional fields include: service_type, service_tier, vehicle_type, time_slot, notes, address

        Protection logic:
        - Don't overwrite explicit mentions with inferred values
        - Track extraction method for audit trail
        - Log all updates

        Args:
            scratchpad: Scratchpad manager instance
            optional_data: Dict of optional fields extracted
        """
        # Map optional fields to appropriate scratchpad sections
        optional_field_mapping = {
            # Appointment section fields
            "service_type": ("appointment", "service_type"),
            "service_tier": ("appointment", "service_tier"),
            "time_slot": ("appointment", "time_slot"),
            "notes": ("appointment", "notes"),
            # Vehicle section fields
            "vehicle_type": ("vehicle", "vehicle_type"),
            # Customer section fields (for address if needed)
            "address": ("customer", "address"),
        }

        for field_name, value in optional_data.items():
            # Skip metadata fields (e.g., service_type_method)
            if field_name.endswith("_method"):
                continue

            if field_name not in optional_field_mapping:
                logger.debug(f"⚠️  Unknown optional field: {field_name}, skipping")
                continue

            section, scratchpad_field = optional_field_mapping[field_name]
            extraction_method = optional_data.get(f"{field_name}_method", "explicit")

            # Get existing field to check for overwrite protection
            existing_field = scratchpad.get_field(section, scratchpad_field)

            if existing_field and existing_field.value:
                # Check if we're trying to overwrite an explicit value with inferred
                existing_method = existing_field.extraction_method or "explicit"

                if existing_method == "explicit" and extraction_method == "inferred":
                    logger.info(f"⏭️  PROTECTION: Not overwriting explicit '{field_name}' with inferred value")
                    continue

                # Overwriting with same or better confidence
                logger.info(f"♻️  UPDATING: '{field_name}' ({extraction_method}) overwriting previous value")

            # Add the field with extraction method
            scratchpad.add_field(
                section,
                scratchpad_field,
                value,
                source="extraction",
                turn=0,
                extraction_method=extraction_method
            )
            logger.info(f"✅ Added optional field: {field_name}={value} ({extraction_method})")

    def update_optional_field(
        self,
        scratchpad: ScratchpadManager,
        field_name: str,
        new_value: Any,
        allow_overwrite: bool = False
    ) -> bool:
        """
        Update a single optional field with protection.

        Args:
            scratchpad: Scratchpad manager instance
            field_name: Name of field to update
            new_value: New value
            allow_overwrite: Force overwrite even if protection rules apply

        Returns:
            True if update succeeded, False if blocked by protection
        """
        optional_field_mapping = {
            "service_type": ("appointment", "service_type"),
            "service_tier": ("appointment", "service_tier"),
            "time_slot": ("appointment", "time_slot"),
            "notes": ("appointment", "notes"),
            "vehicle_type": ("vehicle", "vehicle_type"),
            "address": ("customer", "address"),
        }

        if field_name not in optional_field_mapping:
            logger.warning(f"❌ Unknown optional field: {field_name}")
            return False

        section, scratchpad_field = optional_field_mapping[field_name]
        existing_field = scratchpad.get_field(section, scratchpad_field)

        # Apply protection unless explicitly allowed
        if existing_field and existing_field.value and not allow_overwrite:
            logger.info(f"⏭️  UPDATE BLOCKED: '{field_name}' already has value, use allow_overwrite=True to force")
            return False

        scratchpad.update_field(section, scratchpad_field, new_value)
        logger.info(f"✅ Updated optional field: {field_name}={new_value}")
        return True

    def delete_optional_field(
        self,
        scratchpad: ScratchpadManager,
        field_name: str
    ) -> bool:
        """
        Delete an optional field from scratchpad.

        Args:
            scratchpad: Scratchpad manager instance
            field_name: Name of field to delete

        Returns:
            True if deletion succeeded
        """
        optional_field_mapping = {
            "service_type": ("appointment", "service_type"),
            "service_tier": ("appointment", "service_tier"),
            "time_slot": ("appointment", "time_slot"),
            "notes": ("appointment", "notes"),
            "vehicle_type": ("vehicle", "vehicle_type"),
            "address": ("customer", "address"),
        }

        if field_name not in optional_field_mapping:
            logger.warning(f"❌ Unknown optional field: {field_name}")
            return False

        section, scratchpad_field = optional_field_mapping[field_name]
        deleted = scratchpad.delete_field(section, scratchpad_field)

        if deleted:
            logger.info(f"✅ Deleted optional field: {field_name}")
        else:
            logger.debug(f"ℹ️  Optional field not found or already deleted: {field_name}")

        return deleted