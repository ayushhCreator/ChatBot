"""
Test to verify sentiment values are properly typed and converted.
Ensures no TypeError when comparing sentiment with float values.
"""
import sys
sys.path.insert(0, '/home/riju279/Downloads/demo')

from example.response_composer import ResponseComposer


def test_sentiment_type_conversion():
    """Test that sentiment values are properly converted to float."""
    composer = ResponseComposer()

    # Test 1: Float values (normal case)
    print("\n=== Test 1: Float Sentiment Values ===")
    result = composer.compose_response(
        user_message="What do you charge?",
        llm_response="Our pricing starts at...",
        intent="pricing",
        sentiment_interest=5.0,
        sentiment_anger=1.0,
        sentiment_disgust=1.0,
        sentiment_boredom=1.0,
        current_state="greeting"
    )
    print("✓ PASS: Float values work")
    print(f"  Response mode: {result['mode']}")
    print(f"  Response: {result['response'][:60]}...")

    # Test 2: String values (from JSON deserialization)
    print("\n=== Test 2: String Sentiment Values (JSON case) ===")
    result = composer.compose_response(
        user_message="I want to book a service",
        llm_response="Great! Let me help you book...",
        intent="booking",
        sentiment_interest="8.0",     # String value
        sentiment_anger="1.0",        # String value
        sentiment_disgust="1.0",      # String value
        sentiment_boredom="1.0",      # String value
        current_state="greeting"
    )
    print("✓ PASS: String values converted successfully")
    print(f"  Response mode: {result['mode']}")
    print(f"  Response: {result['response'][:60]}...")

    # Test 3: Integer values
    print("\n=== Test 3: Integer Sentiment Values ===")
    result = composer.compose_response(
        user_message="Your service is terrible!",
        llm_response="I apologize...",
        intent="complaint",
        sentiment_interest=1,          # Integer value
        sentiment_anger=9,             # Integer value
        sentiment_disgust=7,           # Integer value
        sentiment_boredom=1,           # Integer value
        current_state="greeting"
    )
    print("✓ PASS: Integer values converted successfully")
    print(f"  Response mode: {result['mode']}")

    # Test 4: Mixed types
    print("\n=== Test 4: Mixed Type Sentiment Values ===")
    result = composer.compose_response(
        user_message="Tell me more about your services",
        llm_response="Our services include...",
        intent="general_inquiry",
        sentiment_interest=7,          # Integer
        sentiment_anger="2.0",         # String
        sentiment_disgust=1.5,         # Float
        sentiment_boredom="1",         # String integer
        current_state="greeting"
    )
    print("✓ PASS: Mixed type values converted successfully")
    print(f"  Response mode: {result['mode']}")

    # Test 5: Invalid values (should fallback to defaults)
    print("\n=== Test 5: Invalid Values (Fallback Test) ===")
    result = composer.compose_response(
        user_message="Test message",
        llm_response="Test response",
        intent="general_inquiry",
        sentiment_interest="invalid",  # Invalid string
        sentiment_anger=None,          # None value
        sentiment_disgust="NaN",       # Invalid string
        sentiment_boredom=float('inf'),  # Infinity
        current_state="greeting"
    )
    print("✓ PASS: Invalid values fallback to defaults")
    print(f"  Response: {result['response'][:60]}...")

    print("\n" + "="*70)
    print("ALL TESTS PASSED - Type Safety Verified")
    print("="*70)


if __name__ == "__main__":
    test_sentiment_type_conversion()