"""
Optional Fields Extractor - Extracts enhanced/optional fields for better service.

CRITICAL DISTINCTION:
- REQUIRED fields: first_name, last_name, phone, vehicle_brand, vehicle_model, vehicle_plate, appointment_date
- OPTIONAL fields: service_type, service_tier, vehicle_type, time_slot, notes, address

Optional fields can be:
1. Extracted explicitly from user messages (e.g., "premium package")
2. Inferred from context (e.g., vehicle_type from vehicle_model)
3. Left blank and filled manually during follow-up

This extractor handles CRUD operations with protection against overwrites.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Standardized service types."""
    WASH = "wash"
    POLISH = "polish"
    DETAILING = "detailing"
    COATING = "coating"
    UNKNOWN = "unknown"


class ServiceTier(str, Enum):
    """Service tier levels."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"
    UNKNOWN = "unknown"


class VehicleType(str, Enum):
    """Vehicle type classifications."""
    HATCHBACK = "hatchback"
    SEDAN = "sedan"
    SUV = "suv"
    EV = "ev"
    LUXURY = "luxury"
    TRUCK = "truck"
    VAN = "van"
    UNKNOWN = "unknown"


class OptionalFieldsExtractor:
    """
    Extracts optional/enhanced fields for better service personalization.

    Key features:
    - Extraction priority: Explicit mention > Inference > Leave blank
    - Protection against overwrites: Don't overwrite explicit with inferred
    - Scratchpad integration: Stores with confidence levels and extraction method
    """

    # Vehicle model to type mapping (inference logic)
    VEHICLE_TYPE_MAPPING = {
        # Hatchbacks
        "swift": VehicleType.HATCHBACK,
        "celerio": VehicleType.HATCHBACK,
        "baleno": VehicleType.HATCHBACK,
        "i10": VehicleType.HATCHBACK,
        "alto": VehicleType.HATCHBACK,
        "tiago": VehicleType.HATCHBACK,
        "wagon r": VehicleType.HATCHBACK,

        # Sedans
        "maruti": VehicleType.SEDAN,
        "ciaz": VehicleType.SEDAN,
        "dzire": VehicleType.SEDAN,
        "city": VehicleType.SEDAN,
        "civic": VehicleType.SEDAN,
        "accord": VehicleType.SEDAN,
        "camry": VehicleType.SEDAN,
        "altis": VehicleType.SEDAN,

        # SUVs
        "brezza": VehicleType.SUV,
        "creta": VehicleType.SUV,
        "xuv500": VehicleType.SUV,
        "scorpio": VehicleType.SUV,
        "fortuner": VehicleType.SUV,
        "innova": VehicleType.SUV,
        "safari": VehicleType.SUV,

        # EVs
        "tata nexon ev": VehicleType.EV,
        "mahindra e2o": VehicleType.EV,
        "tesla": VehicleType.EV,

        # Luxury
        "bmw": VehicleType.LUXURY,
        "audi": VehicleType.LUXURY,
        "mercedes": VehicleType.LUXURY,
        "porsche": VehicleType.LUXURY,
    }

    # Service keywords mapping
    SERVICE_TYPE_KEYWORDS = {
        "wash": ServiceType.WASH,
        "cleaning": ServiceType.WASH,
        "car wash": ServiceType.WASH,
        "polish": ServiceType.POLISH,
        "polishing": ServiceType.POLISH,
        "wax": ServiceType.POLISH,
        "detail": ServiceType.DETAILING,
        "detailing": ServiceType.DETAILING,
        "deep clean": ServiceType.DETAILING,
        "coating": ServiceType.COATING,
        "ceramic coating": ServiceType.COATING,
    }

    SERVICE_TIER_KEYWORDS = {
        "basic": ServiceTier.BASIC,
        "standard": ServiceTier.STANDARD,
        "regular": ServiceTier.STANDARD,
        "premium": ServiceTier.PREMIUM,
        "luxury": ServiceTier.LUXURY,
        "deluxe": ServiceTier.LUXURY,
    }

    def __init__(self):
        """Initialize the optional fields extractor."""
        pass

    def extract_optional_fields(
        self,
        user_message: str,
        current_state: str,
        existing_data: Optional[Dict[str, Any]] = None,
        only_explicit: bool = False
    ) -> Dict[str, Any]:
        """
        Extract optional fields from user message - NON-BLOCKING and flexible.

        IMPORTANT: This extractor is NOT greedy:
        - Does NOT extract vehicle_type via inference (only explicit mentions)
        - Only extracts if user explicitly mentions or already provided
        - Returns empty dict if nothing is explicitly mentioned
        - Used for enrichment ONLY, never blocks booking

        Args:
            user_message: User's raw message
            current_state: Current conversation state
            existing_data: Existing scratchpad data (to avoid overwrites)
            only_explicit: If True, ONLY extract if explicitly mentioned (for confirmation phase)

        Returns:
            Dict of extracted optional fields with metadata (can be empty)
        """
        existing_data = existing_data or {}
        extracted = {}

        # Extract service type ONLY if explicitly mentioned
        service_type = self._extract_service_type(user_message)
        if service_type and service_type != ServiceType.UNKNOWN:
            if self._is_explicit_mention(user_message, "service"):
                if "service_type" not in existing_data:
                    extracted["service_type"] = service_type.value
                    extracted["service_type_method"] = "explicit"
                    logger.info(f"✅ Extracted service_type: {service_type.value}")

        # Extract service tier ONLY if explicitly mentioned
        service_tier = self._extract_service_tier(user_message)
        if service_tier and service_tier != ServiceTier.UNKNOWN:
            if self._is_explicit_mention(user_message, "tier"):
                if "service_tier" not in existing_data:
                    extracted["service_tier"] = service_tier.value
                    extracted["service_tier_method"] = "explicit"
                    logger.info(f"✅ Extracted service_tier: {service_tier.value}")

        # Extract vehicle type ONLY if explicitly mentioned (NOT inferred)
        if self._is_explicit_mention(user_message, "vehicle type"):
            vehicle_type = self._extract_vehicle_type(user_message, existing_data)
            if vehicle_type and vehicle_type != VehicleType.UNKNOWN:
                if "vehicle_type" not in existing_data:
                    extracted["vehicle_type"] = vehicle_type.value
                    extracted["vehicle_type_method"] = "explicit"
                    logger.info(f"✅ Extracted vehicle_type: {vehicle_type.value} (explicit only)")

        # Extract time slot preferences ONLY if explicitly mentioned
        time_slot = self._extract_time_slot(user_message)
        if time_slot:
            if self._is_explicit_mention(user_message, "time"):
                if "time_slot" not in existing_data:
                    extracted["time_slot"] = time_slot
                    extracted["time_slot_method"] = "explicit"
                    logger.info(f"✅ Extracted time_slot: {time_slot}")

        # Extract special notes/requests ONLY if explicitly mentioned
        notes = self._extract_notes(user_message)
        if notes:
            # For notes, always append unless explicitly replacing
            existing_notes = existing_data.get("notes", "")
            if existing_notes:
                extracted["notes"] = f"{existing_notes}; {notes}"
            else:
                extracted["notes"] = notes
            extracted["notes_method"] = "explicit"
            logger.info(f"✅ Extracted notes: {notes[:50]}...")

        if not extracted:
            logger.debug(f"ℹ️  NO optional fields extracted (not explicitly mentioned in message)")

        return extracted

    def _extract_service_type(self, user_message: str) -> ServiceType:
        """Extract service type from message."""
        message_lower = user_message.lower()
        for keyword, service in self.SERVICE_TYPE_KEYWORDS.items():
            if keyword in message_lower:
                return service
        return ServiceType.UNKNOWN

    def _extract_service_tier(self, user_message: str) -> ServiceTier:
        """Extract service tier from message."""
        message_lower = user_message.lower()
        for keyword, tier in self.SERVICE_TIER_KEYWORDS.items():
            if keyword in message_lower:
                return tier
        return ServiceTier.UNKNOWN

    def _extract_vehicle_type(
        self,
        user_message: str,
        existing_data: Dict[str, Any]
    ) -> VehicleType:
        """
        Extract vehicle type: explicitly or inferred from vehicle_model.

        Priority:
        1. Explicit mention in user message (e.g., "I have an SUV")
        2. Infer from vehicle_model in existing_data
        3. Return UNKNOWN
        """
        message_lower = user_message.lower()

        # Check for explicit vehicle type mentions
        for vehicle_type in VehicleType:
            if vehicle_type.value in message_lower:
                return vehicle_type

        # Try to infer from vehicle model in existing data
        vehicle_model = existing_data.get("vehicle_model", "").lower()
        if vehicle_model:
            for model_keyword, vehicle_type in self.VEHICLE_TYPE_MAPPING.items():
                if model_keyword in vehicle_model:
                    return vehicle_type

        return VehicleType.UNKNOWN

    def _extract_time_slot(self, user_message: str) -> Optional[str]:
        """
        Extract preferred time slot from message.

        Returns valid slot names from config.TIME_SLOTS:
        - early_morning: 6 AM - 9 AM
        - afternoon: 10 AM - 1 PM
        - evening: 2 PM - 6 PM
        """
        from config import config

        message_lower = user_message.lower()

        # Map user keywords to configured time slots
        # These keywords match the TIME_SLOTS keys in config.py
        time_keywords = {
            "early morning": "early_morning",
            "morning": "early_morning",           # Common synonym for early morning
            "afternoon": "afternoon",
            "lunch": "afternoon",                 # Afternoon includes lunch hours
            "evening": "evening",
            "night": "evening",                   # Evening extends into night
        }

        for keyword, slot_name in time_keywords.items():
            if keyword in message_lower:
                # Validate that this slot is configured
                if slot_name in config.TIME_SLOTS:
                    return slot_name
                else:
                    logger.warning(f"⚠️  TIME SLOT: '{slot_name}' not in config.TIME_SLOTS")

        return None

    def _extract_notes(self, user_message: str) -> Optional[str]:
        """Extract special requests/notes from message."""
        # Look for common phrases indicating special requests
        special_phrases = [
            "need extra",
            "please make sure",
            "special request",
            "allergy to",
            "prefer",
            "avoid",
            "sensitive",
        ]

        message_lower = user_message.lower()
        for phrase in special_phrases:
            if phrase in message_lower:
                # Extract the relevant part (simplified - could be improved)
                idx = message_lower.find(phrase)
                # Return the sentence containing the phrase
                sentences = user_message.split(".")
                for sentence in sentences:
                    if phrase in sentence.lower():
                        return sentence.strip()

        return None

    def _is_explicit_mention(self, user_message: str, field_type: str) -> bool:
        """
        Check if field is explicitly mentioned vs inferred.

        Examples:
        - "I have a premium package" -> explicit service_tier
        - "My car is an SUV" -> explicit vehicle_type
        """
        message_lower = user_message.lower()

        explicit_patterns = {
            "service": ["service", "package", "plan"],
            "tier": ["basic", "standard", "premium", "luxury"],
            "vehicle type": ["hatchback", "sedan", "suv", "ev"],
            "time": ["morning", "afternoon", "evening", "time", "slot"],
        }

        patterns = explicit_patterns.get(field_type, [])
        return any(pattern in message_lower for pattern in patterns)