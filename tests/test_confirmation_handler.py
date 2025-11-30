"""Tests for ConfirmationHandler."""

import pytest
from booking import ScratchpadManager, ConfirmationHandler, ConfirmationAction


class MockTypoDetectorResult:
    """Mock typo detector result."""
    def __init__(self, is_typo, intended_action, confidence, suggestion):
        self.is_typo = is_typo
        self.intended_action = intended_action
        self.confidence = confidence
        self.suggestion = suggestion


class MockTypoDetector:
    """Mock typo detector for testing."""
    def __init__(self, return_typo=False, intended="confirm"):
        self.return_typo = return_typo
        self.intended = intended
        self.called_with = None

    def __call__(self, last_bot_message="", user_response="", expected_actions=""):
        self.called_with = {
            "last_bot_message": last_bot_message,
            "user_response": user_response,
            "expected_actions": expected_actions
        }
        if self.return_typo:
            return MockTypoDetectorResult(
                is_typo="true",
                intended_action=self.intended,
                confidence="high",
                suggestion=f"Did you mean '{self.intended}'?"
            )
        return MockTypoDetectorResult(
            is_typo="false",
            intended_action="",
            confidence="low",
            suggestion=""
        )


class TestConfirmationHandler:
    """Test confirmation action handling."""

    def setup_method(self):
        """Setup for each test."""
        self.scratchpad = ScratchpadManager()
        self.handler = ConfirmationHandler(self.scratchpad)

    def test_detect_confirm_yes(self):
        """Test detecting confirm action."""
        action = self.handler.detect_action("yes")
        assert action == ConfirmationAction.CONFIRM

    def test_detect_confirm_variations(self):
        """Test various confirm phrases."""
        for phrase in ["correct", "proceed", "ok", "go"]:
            action = self.handler.detect_action(phrase)
            assert action == ConfirmationAction.CONFIRM

    def test_detect_cancel(self):
        """Test detecting cancel action."""
        action = self.handler.detect_action("cancel")
        assert action == ConfirmationAction.CANCEL

    def test_detect_cancel_variations(self):
        """Test various cancel phrases."""
        for phrase in ["no", "nevermind", "abort", "nope"]:
            action = self.handler.detect_action(phrase)
            assert action == ConfirmationAction.CANCEL

    def test_detect_edit(self):
        """Test detecting edit action."""
        action = self.handler.detect_action("edit name")
        assert action == ConfirmationAction.EDIT

    def test_detect_edit_variations(self):
        """Test various edit phrases."""
        for phrase in ["change date", "fix phone", "update email"]:
            action = self.handler.detect_action(phrase)
            assert action == ConfirmationAction.EDIT

    def test_handle_confirm(self):
        """Test confirm handler."""
        result = self.handler.handle_confirm()
        assert result is True

    def test_handle_edit_name(self):
        """Test editing name field."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        result = self.handler.handle_edit("name Jane")
        assert result is not None
        assert result[0] == "customer"
        assert result[1] == "first_name"
        assert result[2] == "Jane"
        assert self.scratchpad.get_field("customer", "first_name").value == "Jane"

    def test_handle_edit_date(self):
        """Test editing date field."""
        result = self.handler.handle_edit("date 2024-12-25")
        assert result is not None
        assert result[0] == "appointment"
        assert result[2] == "2024-12-25"

    def test_handle_edit_phone(self):
        """Test editing phone field."""
        result = self.handler.handle_edit("phone 555-9999")
        assert result is not None
        assert result[0] == "customer"
        assert result[1] == "phone"

    def test_handle_edit_invalid_field(self):
        """Test editing invalid field."""
        result = self.handler.handle_edit("invalid_field value")
        assert result is None

    def test_handle_cancel(self):
        """Test cancel handler."""
        self.scratchpad.add_field("customer", "first_name", "John", "direct", 1)
        msg = self.handler.handle_cancel()
        assert "cancelled" in msg.lower()
        assert len(self.scratchpad.get_section("customer")) == 0

    def test_parse_edit_instruction_name(self):
        """Test parsing edit instruction."""
        field = self.handler.parse_edit_instruction("edit my name")
        assert field == "name"

    def test_parse_edit_instruction_phone(self):
        """Test parsing phone edit."""
        field = self.handler.parse_edit_instruction("change phone number")
        assert field == "phone"

    def test_parse_edit_instruction_date(self):
        """Test parsing date edit."""
        field = self.handler.parse_edit_instruction("fix appointment date")
        assert field == "date"

    def test_parse_edit_instruction_not_found(self):
        """Test parsing non-field edit."""
        field = self.handler.parse_edit_instruction("edit something")
        assert field is None


class TestTypoDetection:
    """Test typo detection in confirmation handler."""

    def setup_method(self):
        """Setup for each test."""
        self.scratchpad = ScratchpadManager()

    def test_typo_detection_with_typo(self):
        """Test typo detection identifies typo."""
        mock_detector = MockTypoDetector(return_typo=True, intended="confirm")
        handler = ConfirmationHandler(self.scratchpad, typo_detector=mock_detector)

        # Set confirmation message
        handler.set_confirmation_message("Please confirm your booking")

        # Test typo input
        action, typo_result = handler.detect_action_with_typo_check("confrim")

        assert action == ConfirmationAction.TYPO_DETECTED
        assert typo_result is not None
        assert typo_result["is_typo"] is True
        assert typo_result["intended_action"] == "confirm"
        assert "Did you mean" in typo_result["suggestion"]

    def test_typo_detection_no_typo(self):
        """Test typo detection with valid input."""
        mock_detector = MockTypoDetector(return_typo=False)
        handler = ConfirmationHandler(self.scratchpad, typo_detector=mock_detector)

        handler.set_confirmation_message("Please confirm your booking")

        # Test valid input
        action, typo_result = handler.detect_action_with_typo_check("yes")

        assert action == ConfirmationAction.CONFIRM
        assert typo_result is None

    def test_typo_detection_without_confirmation_message(self):
        """Test typo detection skips when no confirmation shown."""
        mock_detector = MockTypoDetector(return_typo=True)
        handler = ConfirmationHandler(self.scratchpad, typo_detector=mock_detector)

        # No confirmation message set
        action, typo_result = handler.detect_action_with_typo_check("confrim")

        # Should fallback to normal detection
        assert action == ConfirmationAction.EDIT
        assert typo_result is None

    def test_typo_detection_without_detector(self):
        """Test graceful handling when no detector provided."""
        handler = ConfirmationHandler(self.scratchpad, typo_detector=None)

        handler.set_confirmation_message("Please confirm your booking")
        action, typo_result = handler.detect_action_with_typo_check("confrim")

        # Should fallback to normal detection
        assert action == ConfirmationAction.EDIT
        assert typo_result is None

    def test_set_confirmation_message(self):
        """Test setting confirmation message."""
        handler = ConfirmationHandler(self.scratchpad)

        msg = "📋 BOOKING CONFIRMATION [Edit] [Confirm] [Cancel]"
        handler.set_confirmation_message(msg)

        assert handler.last_confirmation_message == msg

    def test_typo_detection_common_typos(self):
        """Test detection of common typos."""
        test_cases = [
            ("confrim", "confirm"),
            ("bokking", "book"),
            ("cancle", "cancel"),
        ]

        for typo, intended in test_cases:
            mock_detector = MockTypoDetector(return_typo=True, intended=intended)
            handler = ConfirmationHandler(self.scratchpad, typo_detector=mock_detector)
            handler.set_confirmation_message("Please respond")

            action, typo_result = handler.detect_action_with_typo_check(typo)

            assert action == ConfirmationAction.TYPO_DETECTED
            assert typo_result["intended_action"] == intended

    def test_typo_detection_valid_one_word_answers(self):
        """Test that valid one-word answers are NOT detected as typos."""
        valid_answers = ["yes", "no", "ok"]

        for answer in valid_answers:
            mock_detector = MockTypoDetector(return_typo=False)
            handler = ConfirmationHandler(self.scratchpad, typo_detector=mock_detector)
            handler.set_confirmation_message("Please respond")

            action, typo_result = handler.detect_action_with_typo_check(answer)

            # Should be detected as normal action, not typo
            assert action in [ConfirmationAction.CONFIRM, ConfirmationAction.CANCEL]
            assert typo_result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
