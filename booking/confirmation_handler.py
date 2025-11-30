"""ConfirmationHandler: Handle user actions on confirmation screen."""

from enum import Enum
from typing import Optional, Tuple, Dict, Any
from booking.scratchpad import ScratchpadManager


class ConfirmationAction(str, Enum):
    """Possible actions at confirmation screen."""
    CONFIRM = "confirm"
    EDIT = "edit"
    CANCEL = "cancel"
    INVALID = "invalid"
    TYPO_DETECTED = "typo_detected"


class ConfirmationHandler:
    """Handle confirmation screen interactions with typo detection."""

    def __init__(self, scratchpad: ScratchpadManager, typo_detector=None):
        self.scratchpad = scratchpad
        self.typo_detector = typo_detector
        self.last_confirmation_message = ""

    def detect_action(self, user_input: str) -> ConfirmationAction:
        """
        Detect user action from input.

        Returns:
            ConfirmationAction: CONFIRM, EDIT, CANCEL, or INVALID
        """
        user_lower = user_input.lower().strip()

        # Confirmation triggers
        confirm_words = ["yes", "confirm", "confirmed", "correct", "proceed", "ok", "go"]
        if any(word in user_lower for word in confirm_words):
            return ConfirmationAction.CONFIRM

        # Cancellation triggers
        cancel_words = ["cancel", "no", "stop", "abort", "nevermind", "nope"]
        if any(word in user_lower for word in cancel_words):
            return ConfirmationAction.CANCEL

        # Edit detection: "edit X" or "change Y" or "fix Z"
        edit_words = ["edit", "change", "fix", "update", "modify", "correct"]
        if any(word in user_lower for word in edit_words):
            return ConfirmationAction.EDIT

        # Default to edit for ambiguous input (allows recovery)
        if user_lower and len(user_lower) > 2:
            return ConfirmationAction.EDIT

        return ConfirmationAction.INVALID

    def handle_confirm(self) -> bool:
        """Handle confirmation action. Returns success."""
        return True

    def handle_edit(self, field_spec: str) -> Optional[Tuple[str, str, str]]:
        """Parse field spec and update scratchpad."""
        parts = field_spec.strip().split(maxsplit=2)
        if len(parts) < 2:
            return None

        field_ref = parts[0].lower()
        new_value = " ".join(parts[1:])

        field_map = {
            "name": ("customer", "first_name"),
            "first": ("customer", "first_name"),
            "last": ("customer", "last_name"),
            "phone": ("customer", "phone"),
            "email": ("customer", "email"),
            "vehicle": ("vehicle", "brand"),
            "brand": ("vehicle", "brand"),
            "model": ("vehicle", "model"),
            "date": ("appointment", "date"),
            "service": ("appointment", "service_type"),
        }

        if field_ref not in field_map:
            return None

        section, field_name = field_map[field_ref]
        self.scratchpad.update_field(section, field_name, new_value)
        return (section, field_name, new_value)

    def handle_cancel(self) -> str:
        """
        Handle cancellation. Clear scratchpad and return message.

        Returns:
            Friendly cancellation message
        """
        self.scratchpad.clear_all()
        return (
            "Booking cancelled. No problem! "
            "Feel free to reach out anytime if you change your mind. 😊"
        )

    def parse_edit_instruction(self, user_input: str) -> Optional[str]:
        """
        Extract the field to edit from user input.

        Examples:
            "edit name" → "name"
            "change the date" → "date"
            "fix phone number" → "phone"

        Returns:
            Field name or None
        """
        user_lower = user_input.lower()

        # Common field mentions
        fields = ["name", "phone", "email", "date", "service", "time",
                  "vehicle", "brand", "model", "plate", "color", "year"]

        for field in fields:
            if field in user_lower:
                return field

        return None

    def detect_action_with_typo_check(self, user_input: str) -> Tuple[ConfirmationAction, Optional[Dict[str, Any]]]:
        """
        Detect action with typo detection.

        Only runs typo detection when:
        - A confirmation message was shown (service card with buttons)
        - User response doesn't match known actions EXACTLY
        - typo_detector is available

        Returns:
            (action, typo_result)
            - action: ConfirmationAction
            - typo_result: Dict with is_typo, intended_action, suggestion (if typo detected)
        """
        # If we have typo detector and confirmation message, check typos FIRST
        if self.typo_detector and self.last_confirmation_message:
            try:
                result = self.typo_detector(
                    last_bot_message=self.last_confirmation_message,
                    user_response=user_input,
                    expected_actions="confirm, edit, cancel, yes, no"
                )

                # Parse result
                is_typo = str(result.is_typo).lower() == "true"
                if is_typo:
                    return (ConfirmationAction.TYPO_DETECTED, {
                        "is_typo": True,
                        "intended_action": result.intended_action,
                        "confidence": result.confidence,
                        "suggestion": result.suggestion
                    })

            except Exception:
                # If typo detection fails, fallback to normal detection
                pass

        # If no typo detected, use normal action detection
        action = self.detect_action(user_input)
        return (action, None)

    def set_confirmation_message(self, message: str):
        """Store the last confirmation message shown to user."""
        self.last_confirmation_message = message