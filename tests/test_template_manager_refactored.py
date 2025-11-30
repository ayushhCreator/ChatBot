"""
Unit test for refactored template_manager with intent-aware decision logic.
Verifies that intent parameter is accepted and properly prioritized.
"""
import sys
sys.path.insert(0, '/home/riju279/Downloads/demo')

from example.template_manager import TemplateManager, ResponseMode


def test_intent_aware_template_decision():
    """Test intent-first decision logic in template_manager."""
    manager = TemplateManager()

    test_cases = [
        {
            "name": "Pricing Inquiry",
            "intent": "pricing",
            "sentiment_interest": 8.0,  # High interest shouldn't override intent
            "sentiment_anger": 1.0,
            "expected_mode": ResponseMode.TEMPLATE_ONLY,
            "expected_template": "pricing"
        },
        {
            "name": "Catalog Request",
            "intent": "catalog",
            "sentiment_interest": 5.0,
            "sentiment_anger": 1.0,
            "expected_mode": ResponseMode.TEMPLATE_ONLY,
            "expected_template": "catalog"
        },
        {
            "name": "Booking Intent",
            "intent": "booking",
            "sentiment_interest": 6.0,
            "sentiment_anger": 1.0,
            "expected_mode": ResponseMode.TEMPLATE_ONLY,
            "expected_template": "plans"
        },
        {
            "name": "General Inquiry (LLM only)",
            "intent": "general_inquiry",
            "sentiment_interest": 7.0,  # High interest shouldn't push template
            "sentiment_anger": 1.0,
            "expected_mode": ResponseMode.LLM_ONLY,
            "expected_template": ""
        },
        {
            "name": "Complaint (no template)",
            "intent": "complaint",
            "sentiment_interest": 1.0,
            "sentiment_anger": 9.0,
            "expected_mode": ResponseMode.LLM_ONLY,
            "expected_template": ""
        },
        {
            "name": "Small Talk with high anger",
            "intent": "small_talk",
            "sentiment_interest": 5.0,
            "sentiment_anger": 7.0,
            "expected_mode": ResponseMode.LLM_ONLY,
            "expected_template": ""
        },
        {
            "name": "Reschedule with disgust",
            "intent": "reschedule",
            "sentiment_interest": 5.0,
            "sentiment_anger": 2.0,
            "sentiment_disgust": 7.0,
            "expected_mode": ResponseMode.LLM_ONLY,
            "expected_template": ""
        }
    ]

    print("\n" + "="*70)
    print("INTENT-AWARE TEMPLATE DECISION TESTS")
    print("="*70)

    passed = 0
    failed = 0

    for test in test_cases:
        mode, template = manager.decide_response_mode(
            user_message="Test message",
            intent=test["intent"],
            sentiment_interest=test["sentiment_interest"],
            sentiment_anger=test["sentiment_anger"],
            sentiment_disgust=test.get("sentiment_disgust", 1.0),
            sentiment_boredom=test.get("sentiment_boredom", 1.0),
            current_state="greeting"
        )

        mode_match = mode == test["expected_mode"]
        template_match = template == test["expected_template"]
        test_passed = mode_match and template_match

        status = "✓ PASS" if test_passed else "❌ FAIL"
        print(f"\n{status} | {test['name']}")
        print(f"  Intent: {test['intent']}")
        print(f"  Sentiment: interest={test['sentiment_interest']}, anger={test['sentiment_anger']}")
        if "sentiment_disgust" in test:
            print(f"            disgust={test['sentiment_disgust']}")
        print(f"  Expected: {test['expected_mode'].value} template='{test['expected_template']}'")
        print(f"  Got:      {mode.value} template='{template}'")

        if test_passed:
            passed += 1
        else:
            failed += 1
            if not mode_match:
                print(f"  ❌ Mode mismatch: expected {test['expected_mode'].value}, got {mode.value}")
            if not template_match:
                print(f"  ❌ Template mismatch: expected '{test['expected_template']}', got '{template}'")

    print("\n" + "="*70)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED (Total: {len(test_cases)})")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = test_intent_aware_template_decision()
    sys.exit(0 if success else 1)