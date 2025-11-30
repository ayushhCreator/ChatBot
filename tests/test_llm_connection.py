"""
Test script to verify LLM is actually being called.
"""
import dspy
from dspy_config import dspy_configurator
from modules import SentimentAnalyzer, NameExtractor, VehicleDetailsExtractor, DateParser
from datetime import datetime


def test_dspy_direct():
    """Test DSPy LLM connection directly."""
    print("\n" + "="*60)
    print("TESTING DIRECT DSPY LLM CONNECTION")
    print("="*60)
    
    dspy_configurator.configure()
    
    # Get the configured LM
    lm = dspy.settings.lm
    print(f"\nConfigured LM: {lm}")
    print(f"Model: {lm.model if hasattr(lm, 'model') else 'Unknown'}")
    
    # Test direct LLM call
    print("\n--- Testing Direct LLM Call ---")
    try:
        response = lm("Say 'Hello from LLM' in exactly 5 words")
        print(f"LLM Response: {response}")
        print("✓ Direct LLM call successful")
        return True
    except Exception as e:
        print(f"✗ Direct LLM call failed: {e}")
        return False


def test_sentiment_analyzer_llm():
    """Test if SentimentAnalyzer actually calls LLM."""
    print("\n" + "="*60)
    print("TESTING SENTIMENT ANALYZER LLM USAGE")
    print("="*60)
    
    dspy_configurator.configure()
    
    analyzer = SentimentAnalyzer()
    
    print(f"\nPredictor type: {type(analyzer.predictor)}")
    
    print("\n--- Calling Sentiment Analyzer ---")
    try:
        result = analyzer(
            conversation_history="User: Hi, I want to book a car wash ",
            current_message="Yes, I would like to know more!"
        )
        
        print(f"\nResult type: {type(result)}")
        print(f"Interest Score: {result.interest_score}")
        print(f"Anger Score: {result.anger_score}")
        print(f"Reasoning: {result.reasoning}")
        print("\n✓ Sentiment analyzer called LLM successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Sentiment analyzer failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_name_extractor_llm():
    """Test if NameExtractor actually calls LLM."""
    print("\n" + "="*60)
    print("TESTING NAME EXTRACTOR LLM USAGE")
    print("="*60)
    
    dspy_configurator.configure()
    
    extractor = NameExtractor()
    
    print(f"\nPredictor type: {type(extractor.predictor)}")
    
    print("\n--- Calling Name Extractor ---")
    try:
        result = extractor(user_message="Hii, I am Ayush Raj")
        
        print(f"\nResult type: {type(result)}")
        print(f"First Name: {result.first_name}")
        print(f"Last Name: {result.last_name}")
        print(f"Confidence: {result.confidence}")
        print("\n✓ Name extractor called LLM successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Name extractor failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vehicle_extractor_llm():
    """Test if VehicleDetailsExtractor actually calls LLM."""
    print("\n" + "="*60)
    print("TESTING VEHICLE EXTRACTOR LLM USAGE")
    print("="*60)
    
    dspy_configurator.configure()
    
    extractor = VehicleDetailsExtractor()
    
    print(f"\nPredictor type: {type(extractor.predictor)}")
    
    print("\n--- Calling Vehicle Extractor ---")
    try:
        result = extractor(user_message="I Drive a Honda Civic with plate MH12AB1234")
        
        print(f"\nResult type: {type(result)}")
        print(f"Brand: {result.brand}")
        print(f"Model: {result.model}")
        print(f"Plate: {result.number_plate}")
        print("\n✓ Vehicle extractor called LLM successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Vehicle extractor failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_date_parser_llm():
    """Test if DateParser actually calls LLM."""
    print("\n" + "="*60)
    print("TESTING DATE PARSER LLM USAGE")
    print("="*60)
    
    dspy_configurator.configure()
    
    parser = DateParser()
    
    print(f"\nPredictor type: {type(parser.predictor)}")
    
    print("\n--- Calling Date Parser ---")
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        result = parser(
            user_message="I want it tomorrow",
            current_date=current_date
        )
        
        print(f"\nResult type: {type(result)}")
        print(f"Parsed Date: {result.parsed_date}")
        print(f"Confidence: {result.confidence}")
        print("\n✓ Date parser called LLM successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Date parser failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all LLM connection tests."""
    print("\n" + "="*60)
    print("LLM CONNECTION VERIFICATION TESTS")
    print("="*60)
    print("\nThis will verify if the system actually calls the LLM")
    print("or just has it configured but unused.\n")
    
    results = {}
    
    try:
        results['direct'] = test_dspy_direct()
        results['sentiment'] = test_sentiment_analyzer_llm()
        results['name'] = test_name_extractor_llm()
        results['vehicle'] = test_vehicle_extractor_llm()
        results['date'] = test_date_parser_llm()
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{test_name.upper()}: {status}")
        
        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n✓ ALL TESTS PASSED - LLM IS BEING CALLED")
        else:
            print(f"\n✗ {total - passed} TESTS FAILED")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
