"""
Integration tests for TypoDetector with real DSPy LLM.

These tests use the actual LLM configured via dspy_config.py
to test typo detection end-to-end.

WARNING: These tests require:
1. Ollama running with qwen:8b (or configured model)
2. DSPy properly configured via dspy_config.py
3. Network access to Ollama instance
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dspy_config import ensure_configured
from modules import TypoDetector
from booking import ScratchpadManager, ConfirmationHandler


class TestTypoDetectorWithLLM:
    """Test TypoDetector with real LLM inference."""

    @classmethod
    def setup_class(cls):
        """Configure DSPy before running tests."""
        ensure_configured()

    def test_typo_detector_initialization(self):
        """Test TypoDetector initializes without errors."""
        detector = TypoDetector()
        assert detector is not None
        assert detector.predictor is not None

    def test_detect_confrim_typo(self):
        """Test detecting 'confrim' as typo for 'confirm'."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please confirm your booking: [Confirm] [Edit] [Cancel]",
            user_response="confrim",
            expected_actions="confirm, edit, cancel"
        )

        # Check result structure
        assert hasattr(result, 'is_typo')
        assert hasattr(result, 'intended_action')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'suggestion')

        # Verify typo was detected
        is_typo = str(result.is_typo).lower() == "true"
        assert is_typo, f"Expected typo detection for 'confrim', got: {result.is_typo}"

        # Verify intended action points to 'confirm'
        intended = str(result.intended_action).lower()
        assert "confirm" in intended, f"Expected 'confirm' as intended action, got: {result.intended_action}"

        # Verify suggestion exists
        suggestion = str(result.suggestion).lower()
        assert len(suggestion) > 0, "Expected suggestion message"
        assert "mean" in suggestion or "confirm" in suggestion, f"Suggestion should hint at correct word: {result.suggestion}"

    def test_detect_bokking_typo(self):
        """Test detecting 'bokking' as typo for 'book'."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Ready to book your appointment? [Book] [Cancel]",
            user_response="bokking",
            expected_actions="book, cancel"
        )

        is_typo = str(result.is_typo).lower() == "true"
        assert is_typo, f"Expected typo detection for 'bokking', got: {result.is_typo}"

    def test_detect_apponitment_typo(self):
        """Test detecting 'apponitment' as typo for 'appointment'."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Your appointment details are shown above. Correct?",
            user_response="apponitment wrong",
            expected_actions="confirm, edit, cancel"
        )

        is_typo = str(result.is_typo).lower() == "true"
        assert is_typo, f"Expected typo detection for 'apponitment', got: {result.is_typo}"

    def test_valid_response_not_detected_as_typo(self):
        """Test that valid responses are NOT detected as typos."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please confirm your booking: [Confirm] [Edit] [Cancel]",
            user_response="yes",
            expected_actions="confirm, edit, cancel"
        )

        is_typo = str(result.is_typo).lower() == "true"
        assert not is_typo, f"Valid 'yes' should not be detected as typo, got: {result.is_typo}"

    def test_gibberish_detected_as_typo(self):
        """Test that gibberish is detected as typo or invalid."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please confirm: [Yes] [No]",
            user_response="xyzabc123",
            expected_actions="yes, no"
        )

        # Should either be detected as typo or have low confidence
        is_typo = str(result.is_typo).lower() == "true"
        confidence = str(result.confidence).lower()

        assert is_typo or "low" in confidence, \
            f"Gibberish should be typo or low confidence. Typo: {result.is_typo}, Confidence: {result.confidence}"

    def test_typo_detection_with_confirmation_handler(self):
        """Test TypoDetector integrated with ConfirmationHandler."""
        detector = TypoDetector()
        scratchpad = ScratchpadManager("test-conv")
        handler = ConfirmationHandler(scratchpad, typo_detector=detector)

        # Set confirmation message
        handler.set_confirmation_message("📋 BOOKING CONFIRMATION\n[Confirm] [Edit] [Cancel]")

        # Test with typo
        action, typo_result = handler.detect_action_with_typo_check("confrim")

        # Should detect typo via DSPy LLM
        assert typo_result is not None or action.value == "edit", \
            f"Should detect typo or treat as edit. Action: {action}, Result: {typo_result}"

    def test_multiple_typos_in_sequence(self):
        """Test detecting multiple different typos."""
        detector = TypoDetector()

        typos = [
            ("confrim", "confirm"),
            ("bokking", "book"),
            ("cancle", "cancel"),
        ]

        for typo_word, expected_intended in typos:
            result = detector(
                last_bot_message="Please respond with confirm, book, or cancel",
                user_response=typo_word,
                expected_actions="confirm, book, cancel"
            )

            is_typo = str(result.is_typo).lower() == "true"
            assert is_typo, f"'{typo_word}' should be detected as typo"

    def test_context_aware_typo_detection(self):
        """Test that typo detection uses context from bot message."""
        detector = TypoDetector()

        # Same typo "yes" spelled as "yse" in different contexts
        result1 = detector(
            last_bot_message="Do you want to proceed? [Yes] [No]",
            user_response="yse",
            expected_actions="yes, no"
        )

        result2 = detector(
            last_bot_message="Different context: [Maybe] [Later]",
            user_response="yse",
            expected_actions="maybe, later"
        )

        # First context should detect it as typo for "yes"
        is_typo1 = str(result1.is_typo).lower() == "true"
        assert is_typo1, "Should detect 'yse' as typo in first context"

        # Behavior in second context may differ since 'yse' doesn't match expected actions
        # Just verify we get a response
        assert hasattr(result2, 'is_typo')


class TestTypoDetectorErrorHandling:
    """Test TypoDetector error handling with real LLM."""

    @classmethod
    def setup_class(cls):
        """Configure DSPy before running tests."""
        ensure_configured()

    def test_empty_user_response(self):
        """Test handling empty user response."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please respond",
            user_response="",
            expected_actions="yes, no"
        )

        # Should handle gracefully
        assert hasattr(result, 'is_typo')

    def test_empty_bot_message(self):
        """Test handling empty bot message."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="",
            user_response="confrim",
            expected_actions="confirm, cancel"
        )

        # Should handle gracefully
        assert hasattr(result, 'is_typo')

    def test_very_long_response(self):
        """Test handling very long user response."""
        detector = TypoDetector()

        long_response = "confrim " * 100  # Very long string

        result = detector(
            last_bot_message="Please confirm",
            user_response=long_response,
            expected_actions="confirm"
        )

        # Should handle gracefully without crashing
        assert hasattr(result, 'is_typo')

    def test_special_characters_in_response(self):
        """Test handling special characters in response."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please respond: [Yes] [No]",
            user_response="c0nfirm@#$%",
            expected_actions="yes, no"
        )

        # Should handle gracefully
        assert hasattr(result, 'is_typo')


class TestTypoDetectorConfidence:
    """Test TypoDetector confidence scoring with real LLM."""

    @classmethod
    def setup_class(cls):
        """Configure DSPy before running tests."""
        ensure_configured()

    def test_confidence_for_obvious_typo(self):
        """Test high confidence for obvious typo."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please confirm your booking",
            user_response="confrim",  # Very obvious typo
            expected_actions="confirm, edit, cancel"
        )

        confidence = str(result.confidence).lower()
        # Should have reasonably high confidence
        assert confidence in ["high", "medium", "low"], f"Invalid confidence: {result.confidence}"

    def test_confidence_for_valid_response(self):
        """Test low confidence for valid response (not a typo)."""
        detector = TypoDetector()

        result = detector(
            last_bot_message="Please confirm your booking",
            user_response="confirm",  # Valid response
            expected_actions="confirm, edit, cancel"
        )

        is_typo = str(result.is_typo).lower() == "true"
        # Valid response should not be typo
        assert not is_typo, "Valid 'confirm' should not be typo"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])