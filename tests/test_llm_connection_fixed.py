"""
Fixed test script that properly uses dspy.History via conversation_manager.

KEY FIX: Uses conversation_manager.get_dspy_history() to provide proper
dspy.History objects instead of passing strings.
"""
import dspy
from datetime import datetime
from dspy_config import dspy_configurator
from modules import SentimentAnalyzer, NameExtractor, VehicleDetailsExtractor, DateParser
from conversation_manager import ConversationManager


def test_dspy_direct():
    """Test DSPy LLM connection directly."""
    print("\n" + "="*60)
    print("TESTING DIRECT DSPY LLM CONNECTION")
    print("="*60)

    dspy_configurator.configure()
    lm = dspy.settings.lm
    print(f"\nConfigured LM: {lm.model if hasattr(lm, 'model') else 'Unknown'}")

    try:
        response = lm("Say 'Hello from LLM' in exactly 5 words")
        print(f"LLM Response: {response}")
        print("✓ Direct LLM call successful")
        return True
    except Exception as e:
        print(f"✗ Direct LLM call failed: {e}")
        return False


def test_sentiment_analyzer_llm():
    """Test SentimentAnalyzer with proper dspy.History."""
    print("\n" + "="*60)
    print("TESTING SENTIMENT ANALYZER")
    print("="*60)

    dspy_configurator.configure()
    conv_manager = ConversationManager()
    conv_id = "test_sentiment_001"

    msg1 = "Hi, I want to book a car wash"
    msg2 = "Welcome! What service interests you?"
    msg3 = "Yes, I would like to know more!"

    conv_manager.add_user_message(conv_id, msg1)
    conv_manager.add_assistant_message(conv_id, msg2)
    conv_manager.add_user_message(conv_id, msg3)

    print("\nConversation Context:")
    print(f"  User: {msg1}")
    print(f"  Assistant: {msg2}")
    print(f"  User: {msg3}")
    print(f"  Analyzing sentiment for: '{msg3}'")

    history = conv_manager.get_dspy_history(conv_id)
    analyzer = SentimentAnalyzer()

    try:
        result = analyzer(
            conversation_history=history,
            current_message=msg3
        )
        print("\nSentiment Analysis Result:")
        print(f"  Interest: {result.interest_score}/10")
        print(f"  Anger: {result.anger_score}/10")
        print(f"  Disgust: {result.disgust_score}/10")
        print("✓ Sentiment analyzer successful")
        return True
    except Exception as e:
        print(f"✗ Sentiment analyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_name_extractor_llm():
    """Test NameExtractor with proper dspy.History."""
    print("\n" + "="*60)
    print("TESTING NAME EXTRACTOR")
    print("="*60)

    dspy_configurator.configure()
    conv_manager = ConversationManager()
    conv_id = "test_name_001"

    user_input = "Hii, I am Ayush Raj"
    conv_manager.add_assistant_message(conv_id, "What's your name?")
    conv_manager.add_user_message(conv_id, user_input)

    print(f"\nUser Input: '{user_input}'")

    history = conv_manager.get_dspy_history(conv_id)
    extractor = NameExtractor()

    try:
        result = extractor(
            conversation_history=history,
            user_message=user_input
        )
        print("\nExtraction Result:")
        print(f"  First Name: {result.first_name}")
        print(f"  Last Name: {result.last_name}")
        print(f"  Confidence: {result.confidence}")
        print("✓ Name extractor successful")
        return True
    except Exception as e:
        print(f"✗ Name extractor failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vehicle_extractor_llm():
    """Test VehicleDetailsExtractor with proper dspy.History."""
    print("\n" + "="*60)
    print("TESTING VEHICLE EXTRACTOR")
    print("="*60)

    dspy_configurator.configure()
    conv_manager = ConversationManager()
    conv_id = "test_vehicle_001"

    user_input = "I Drive a Honda Civic with plate MH12AB1234"
    conv_manager.add_assistant_message(conv_id, "Tell me about your vehicle")
    conv_manager.add_user_message(conv_id, user_input)

    print(f"\nUser Input: '{user_input}'")

    history = conv_manager.get_dspy_history(conv_id)
    extractor = VehicleDetailsExtractor()

    try:
        result = extractor(
            conversation_history=history,
            user_message=user_input
        )
        print("\nExtraction Result:")
        print(f"  Brand: {result.brand}")
        print(f"  Model: {result.model}")
        print(f"  Plate: {result.number_plate}")
        print("✓ Vehicle extractor successful")
        return True
    except Exception as e:
        print(f"✗ Vehicle extractor failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_parser_llm():
    """Test DateParser with proper dspy.History."""
    print("\n" + "="*60)
    print("TESTING DATE PARSER")
    print("="*60)

    dspy_configurator.configure()
    conv_manager = ConversationManager()
    conv_id = "test_date_001"

    user_input = "I want it tomorrow"
    current_date = datetime.now().strftime("%Y-%m-%d")

    conv_manager.add_assistant_message(conv_id, "When would you like to book?")
    conv_manager.add_user_message(conv_id, user_input)

    print(f"\nUser Input: '{user_input}'")
    print(f"Current Date: {current_date}")

    history = conv_manager.get_dspy_history(conv_id)
    parser = DateParser()

    try:
        result = parser(
            conversation_history=history,
            user_message=user_input,
            current_date=current_date
        )
        print("\nParsing Result:")
        print(f"  Parsed Date: {result.parsed_date}")
        print(f"  Confidence: {result.confidence}")
        print("✓ Date parser successful")
        return True
    except Exception as e:
        print(f"✗ Date parser failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LLM CONNECTION TESTS (FIXED)")
    print("="*60)
    print("\nNow using proper dspy.History via conversation_manager")

    results = {
        'direct': test_dspy_direct(),
        'sentiment': test_sentiment_analyzer_llm(),
        'name': test_name_extractor_llm(),
        'vehicle': test_vehicle_extractor_llm(),
        'date': test_date_parser_llm(),
    }

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.upper()}: {status}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - LLM IS BEING CALLED CORRECTLY")
    else:
        print(f"\n✗ {total - passed} TESTS FAILED")


if __name__ == "__main__":
    main()