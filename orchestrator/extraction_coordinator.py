"""
Extraction Coordinator - Coordinates data extraction process.

Single Responsibility: Coordinate extraction of user data (name, phone, vehicle, date, intent, typos).
Reason to change: Extraction coordination logic changes.
"""
import dspy
import logging
from typing import Dict, Any, Optional
from config import ConversationState, Config
from data_extractor import DataExtractionService
from models import ValidatedIntent, ExtractionMetadata
from dspy_config import ensure_configured

logger = logging.getLogger(__name__)


class ExtractionCoordinator:
    """
    Coordinates data extraction from user messages.

    Follows Single Responsibility Principle (SRP):
    - Only handles coordination of extraction services
    - Does NOT handle state management, response generation, or scratchpad updates
    """

    def __init__(self):
        """Initialize extraction coordinator with data extractor."""
        self.data_extractor = DataExtractionService()

    def _is_vehicle_brand(self, text: str) -> bool:
        """
        Check if text matches any known vehicle brand from VehicleBrandEnum.

        Uses centralized vehicle brand list from models.py to prevent
        extracting vehicle brands as customer names.

        Example: "Mahindra" or "Honda City" should return True

        Args:
            text: Text to check (e.g., first_name, last_name)

        Returns:
            True if text matches a vehicle brand, False otherwise
        """
        from models import VehicleBrandEnum

        if not text or not text.strip():
            return False

        text_lower = text.lower().strip()

        # Check if text matches any vehicle brand (case-insensitive)
        return any(
            brand.value.lower() in text_lower or text_lower in brand.value.lower()
            for brand in VehicleBrandEnum
        )

    def extract_for_state(
        self,
        state: ConversationState,
        user_message: str,
        history: dspy.History
    ) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data based on current conversation state.

        PHASE 1 BEHAVIOR: Extraction happens in ALL states (not just specific ones).
        This allows the retroactive validator and state machine to work properly.

        IMPORTANT: This method filters history to USER-ONLY messages to prevent
        the LLM from being confused by chatbot's own responses. This prevents
        issues like extracting "now/today/finished" (chatbot's words) as user data.

        Args:
            state: Current conversation state
            user_message: User's raw message
            history: Conversation history (will be filtered to user messages only)

        Returns:
            Dictionary of extracted data or None
        """
        # CRITICAL FIX: Filter history to USER-ONLY messages
        # Prevents LLM from reading chatbot's own responses during data extraction
        # Example: If chatbot says "you are finished", LLM won't extract "finished" as user intent
        from history_utils import filter_dspy_history_to_user_only
        user_only_history = filter_dspy_history_to_user_only(history)

        extracted = {}

        # Try extracting NAME in any state (Phase 1 behavior)
        try:
            name_data = self.data_extractor.extract_name(user_message, user_only_history)
            if name_data:
                # SANITIZATION: Strip quotes and clean DSPy output
                # Fixes: DSPy sometimes returns '""' (quoted empty string) which fails Pydantic validation
                first_name = str(name_data.first_name).strip().strip('"\'')
                last_name = str(name_data.last_name).strip().strip('"\'') if hasattr(name_data, 'last_name') else ""

                # VALIDATION: Reject if extracted name is actually a vehicle brand
                # Fixes ISSUE_NAME_VEHICLE_CONFUSION (e.g., "Mahindra Scorpio" extracted as name)
                if self._is_vehicle_brand(first_name) or self._is_vehicle_brand(last_name):
                    logger.warning(f"❌ Rejected name extraction: '{first_name} {last_name}' matches vehicle brand")
                # VALIDATION: Reject if extracted name is a greeting stopword
                # Fixes: Prevent "Haan" (Hindi yes), "Hello", "Hi" etc. from being extracted as first_name
                elif first_name and first_name.lower() in Config.GREETING_STOPWORDS:
                    logger.warning(f"❌ Rejected name extraction: '{first_name}' is a greeting stopword")
                elif first_name and first_name.lower() not in ["none", "n/a", "unknown"]:
                    extracted["first_name"] = first_name
                    extracted["last_name"] = last_name
                    extracted["full_name"] = f"{first_name} {last_name}".strip()
                    logger.debug(f"✅ Extracted valid name: {extracted['full_name']}")
        except Exception as e:
            logger.debug(f"Name extraction failed: {e}")

        # Try extracting PHONE in any state (Phase 1 behavior)
        # IMPORTANT: Extract phone BEFORE vehicle to avoid confusion with plate numbers
        try:
            phone_data = self.data_extractor.extract_phone(user_message, user_only_history)
            if phone_data:
                phone_number = str(phone_data.phone_number).strip() if phone_data.phone_number else None
                if phone_number and phone_number.lower() not in ["none", "unknown", "n/a"]:
                    extracted["phone"] = phone_number
        except Exception as e:
            logger.debug(f"Phone extraction failed: {e}")

        # Try extracting VEHICLE in any state (Phase 1 behavior)
        try:
            vehicle_data = self.data_extractor.extract_vehicle_details(user_message, user_only_history)
            if vehicle_data:
                brand = str(vehicle_data.brand).strip() if vehicle_data.brand else None
                if brand and brand.lower() not in ["none", "unknown"]:
                    extracted["vehicle_brand"] = brand
                    extracted["vehicle_model"] = str(vehicle_data.model).strip() if vehicle_data.model else "Unknown"
                    extracted["vehicle_plate"] = str(vehicle_data.number_plate).strip() if vehicle_data.number_plate else "Unknown"
        except Exception as e:
            logger.debug(f"Vehicle extraction failed: {e}")

        # Try extracting DATE in any state (Phase 1 behavior)
        # CRITICAL FIX: Prevent chatbot from reading its own words
        # Even with user_only_history filter, DSPy date parser can infer dates from context
        # Solution: Only accept dates if explicitly mentioned in user message
        try:
            date_data = self.data_extractor.parse_date(user_message, user_only_history)
            if date_data:
                date_str = str(date_data.date_str).strip() if date_data.date_str else None
                # VALIDATION: Check if the extracted date keywords are actually in the user message
                # This prevents inference from implicit context like "checking slots" → "today"
                if date_str and date_str.lower() not in ["none", "unknown"]:
                    # Check if user message contains explicit date indicators
                    date_keywords = ["today", "tomorrow", "monday", "tuesday", "wednesday", "thursday",
                                   "friday", "saturday", "sunday", "next", "this", "day", "date",
                                   "time", "slot", "appointment", "when", "schedule", "book",
                                   "january", "february", "march", "april", "may", "june",
                                   "july", "august", "september", "october", "november", "december"]
                    user_msg_lower = user_message.lower()
                    has_date_intent = any(keyword in user_msg_lower for keyword in date_keywords)

                    if has_date_intent:
                        extracted["appointment_date"] = date_str
                    else:
                        logger.debug(f"⏭️  DATE REJECTED: No explicit date keywords in user message: '{user_message}'")
        except Exception as e:
            logger.debug(f"Date extraction failed: {e}")

        # Return extracted data if any, otherwise None
        return extracted if extracted else None

    def classify_intent(self, history: dspy.History, user_message: str) -> ValidatedIntent:
        """
        Classify customer intent (pricing, booking, complaint, etc.).

        Args:
            history: Conversation history
            user_message: User's raw message

        Returns:
            Validated intent with confidence score
        """
        from modules import IntentClassifier

        ensure_configured()
        try:
            classifier = IntentClassifier()
            result = classifier(
                conversation_history=history,
                current_message=user_message
            )
            intent_class = str(result.intent_class).strip().lower()

            # CRITICAL FIX: Strip quotes that DSPy wraps around output
            # DSPy sometimes returns: "'none'" or "'inquire'" with quotes
            intent_class = intent_class.strip('"\'')

            # CRITICAL FIX: Extract ONLY the intent word from DSPy output
            # DSPy sometimes returns: "inquire (since the user...)" or "book (customer wants to...)"
            # We need just the first word: "inquire", "book", "cancel", etc.
            # Split by space/parenthesis and take the first token
            intent_class = intent_class.split()[0] if intent_class.split() else intent_class
            intent_class = intent_class.split('(')[0].strip() if '(' in intent_class else intent_class

            # CRITICAL FIX: Normalize intent - replace hyphens with underscores
            # LLM may return 'small-talk' but validation expects 'small_talk'
            intent_class = intent_class.replace('-', '_')

            return ValidatedIntent(
                intent_class=intent_class,
                confidence=0.8,
                reasoning=str(result.reasoning),
                metadata=ExtractionMetadata(
                    confidence=0.8,
                    extraction_method="dspy",
                    extraction_source=user_message
                )
            )
        except Exception as e:
            logger.warning(f"Intent classification failed: {type(e).__name__}: {e}, defaulting to inquire")
            return ValidatedIntent(
                intent_class="inquire",
                confidence=0.0,
                reasoning="Failed to classify intent, using default",
                metadata=ExtractionMetadata(
                    confidence=0.0,
                    extraction_method="fallback",
                    extraction_source=user_message
                )
            )

    def detect_typos_in_confirmation(
        self,
        extracted_data: Dict[str, Any],
        user_message: str,
        history: dspy.History
    ) -> Optional[Dict[str, str]]:
        """
        Detect typos in extracted data using DSPy TypoDetector module.

        Args:
            extracted_data: Data extracted from user message
            user_message: User's raw message
            history: Conversation history

        Returns:
            Dictionary of field_name -> correction or None
        """
        from modules import TypoDetector

        ensure_configured()
        try:
            typo_detector = TypoDetector()
            corrections = {}

            # Check each extracted field for typos
            for field_name, value in extracted_data.items():
                if isinstance(value, str) and len(value.strip()) > 0:
                    result = typo_detector(
                        input_text=value,
                        conversation_history=history,
                        field_name=field_name
                    )
                    if result and hasattr(result, 'has_typo') and result.has_typo:
                        if hasattr(result, 'correction') and result.correction:
                            corrections[field_name] = result.correction

            return corrections if corrections else None
        except Exception as e:
            logger.debug(f"Typo detection failed: {e}")
            return None

    def detect_typos_in_response(
        self,
        user_message: str,
        history: dspy.History,
        last_bot_message: str = "",
        expected_actions: str = "confirm, edit, cancel"
    ) -> Optional[str]:
        """
        Detect typos in user's response to a template/confirmation card.

        Uses TypoDetector to identify typos and create a friendly correction message.
        If typos are detected, returns "Did you mean...?" message.

        IMPORTANT: Only call this when a template/card was just shown and user is responding.
        Requires last_bot_message to provide context for typo detection.

        Args:
            user_message: User's raw message
            history: Conversation history
            last_bot_message: The last message sent to user (template/card context)
            expected_actions: Comma-separated list of expected action words

        Returns:
            Friendly "Did you mean...?" message if typos detected, None otherwise
        """
        from modules import TypoDetector

        # Guard: Only run if we have a template context
        if not last_bot_message or last_bot_message.strip() == "":
            return None

        ensure_configured()
        try:
            typo_detector = TypoDetector()

            # Detect typos in user's response to the template/card
            result = typo_detector(
                last_bot_message=last_bot_message,
                user_response=user_message,
                expected_actions=expected_actions
            )

            if result:
                # Check if typo was detected
                is_typo = getattr(result, 'is_typo', False)
                if is_typo:
                    intended_action = getattr(result, 'intended_action', '')
                    suggestion = getattr(result, 'suggestion', '')

                    if intended_action and intended_action.lower() not in ["none", "unknown", ""]:
                        # Create friendly "did you mean" message
                        msg = f"Did you mean '{intended_action}'?"
                        if suggestion and suggestion.strip():
                            msg = suggestion  # Use LLM's friendly suggestion if available
                        logger.info(f"🔤 TYPO DETECTED: '{user_message}' → '{intended_action}'")
                        return msg

            return None
        except Exception as e:
            logger.debug(f"Typo detection in response failed: {e}")
            return None

    def validate_time_slot(self, time_slot_name: str) -> bool:
        """
        Validate that a time slot name is valid and configured.

        Args:
            time_slot_name: Slot name (early_morning, afternoon, evening)

        Returns:
            True if valid, False otherwise
        """
        from config import config

        if not time_slot_name or not isinstance(time_slot_name, str):
            return False

        # Check if slot exists in config
        if time_slot_name not in config.TIME_SLOTS:
            logger.warning(f"⚠️  INVALID TIME SLOT: '{time_slot_name}' not in config.TIME_SLOTS")
            return False

        logger.info(f"✅ TIME SLOT VALIDATED: '{time_slot_name}'")
        return True

    def create_validated_time_slot(self, slot_name: str) -> Optional[Any]:
        """
        Create a ValidatedTimeSlot from a slot name.

        Args:
            slot_name: Slot name (early_morning, afternoon, evening)

        Returns:
            ValidatedTimeSlot object or None if invalid
        """
        from config import config
        from models import ValidatedTimeSlot, TimeSlotEnum, ExtractionMetadata
        from datetime import datetime

        if not self.validate_time_slot(slot_name):
            return None

        try:
            slot_config = config.TIME_SLOTS[slot_name]

            validated_slot = ValidatedTimeSlot(
                slot_name=TimeSlotEnum(slot_name),
                start_time=slot_config["start"],
                end_time=slot_config["end"],
                label=slot_config["label"],
                metadata=ExtractionMetadata(
                    confidence=1.0,
                    extraction_method="rule_based",
                    extraction_source=f"config.TIME_SLOTS['{slot_name}']",
                    processing_time_ms=0.0
                )
            )

            logger.info(f"✅ CREATED VALIDATED TIME SLOT: {slot_name} ({slot_config['label']})")
            return validated_slot

        except Exception as e:
            logger.error(f"❌ FAILED TO CREATE TIME SLOT: {type(e).__name__}: {e}")
            return None

    def check_time_slot_gaps(self, slots: list) -> bool:
        """
        Verify that time slots have minimum 1-hour gaps between them.

        Args:
            slots: List of ValidatedTimeSlot objects

        Returns:
            True if all gaps are valid, False otherwise
        """
        from models import ValidatedTimeSlot

        if not slots or len(slots) < 2:
            return True

        # Ensure slots are ValidatedTimeSlot instances
        valid_slots = [s for s in slots if isinstance(s, ValidatedTimeSlot)]
        if len(valid_slots) != len(slots):
            logger.warning("⚠️  SLOT GAP CHECK: Not all slots are ValidatedTimeSlot instances")
            return False

        # Sort by start time
        sorted_slots = sorted(valid_slots, key=lambda s: s.start_time)

        # Check gaps between consecutive slots
        for i in range(len(sorted_slots) - 1):
            current_slot = sorted_slots[i]
            next_slot = sorted_slots[i + 1]

            if not current_slot.has_gap_from(next_slot, min_gap_minutes=60):
                logger.warning(
                    f"⚠️  SLOT GAP VIOLATION: {current_slot.label} (ends {current_slot.end_time}) "
                    f"and {next_slot.label} (starts {next_slot.start_time}) have less than 1-hour gap"
                )
                return False

        logger.info(f"✅ ALL TIME SLOT GAPS VALID: {len(sorted_slots)} slots have proper spacing")
        return True