"""
Unit tests for template_manager.decide_response_mode() with intent parameter.
Tests whether intent-aware decision logic is needed.
"""
import sys
sys.path.insert(0, '/home/riju279/Downloads/demo')

from example.template_manager import TemplateManager


def test_template_manager_intent_parameter():
    """Test if decide_response_mode accepts intent parameter."""
    manager = TemplateManager()

    # Test 1: Check current method signature
    print("\n=== Test 1: Current Method Signature ===")
    import inspect
    sig = inspect.signature(manager.decide_response_mode)
    params = list(sig.parameters.keys())
    print(f"Parameters: {params}")

    has_intent = "intent" in params
    print(f"Has 'intent' parameter: {has_intent}")

    if not has_intent:
        print("❌ REFACTOR NEEDED: intent parameter not found")
        print(f"Current parameters: {params}")
    else:
        print("✓ READY: intent parameter exists")

    # Test 2: Current behavior without intent
    print("\n=== Test 2: Current Behavior (Sentiment-Only) ===")

    test_cases = [
        {
            "message": "What do you charge for a car wash?",
            "description": "Pricing inquiry",
            "expected_intent": "pricing"
        },
        {
            "message": "What services do you offer?",
            "description": "Catalog request",
            "expected_intent": "catalog"
        },
        {
            "message": "I want to book a wash for tomorrow",
            "description": "Booking intent",
            "expected_intent": "booking"
        }
    ]

    for test_case in test_cases:
        msg = test_case["message"]
        mode, template_key = manager.decide_response_mode(
            user_message=msg,
            sentiment_interest=5.0,
            sentiment_anger=1.0,
            current_state="greeting"
        )
        print(f"\n{test_case['description']}")
        print(f"  Message: {msg}")
        print(f"  Expected intent: {test_case['expected_intent']}")
        print(f"  Current behavior: ResponseMode={mode.value}, template={template_key}")

    # Test 3: Problem case - high sentiment drives catalog
    print("\n=== Test 3: Problem Case - Sentiment-Driven Behavior ===")
    print("Customer asks 'What do you charge?' with high interest (8.0)")
    mode, template_key = manager.decide_response_mode(
        user_message="What do you charge for a car wash?",
        sentiment_interest=8.0,  # HIGH INTEREST
        sentiment_anger=1.0,
        current_state="greeting"
    )
    print(f"Result: ResponseMode={mode.value}, template={template_key}")
    print("❌ PROBLEM: Shows 'catalog' template despite pricing intent!")
    print("✓ SOLUTION: Need to refactor to accept intent parameter and prioritize it")


if __name__ == "__main__":
    test_template_manager_intent_parameter()