"""
Unit test for IntentClassifier DSPy module.
Tests intent classification with different types of user messages.
"""

import sys
from typing import Dict, Any

# Import required modules
try:
    from modules import IntentClassifier
    from history_utils import empty_dspy_history, get_default_history
    from dspy_config import ensure_configured
except ImportError:
    # Try alternative import path
    from modules import IntentClassifier
    from history_utils import empty_dspy_history
    from dspy_config import ensure_configured


# Test configuration
TEST_CASES = [
    {
        "id": 1,
        "message": "What do you charge for a car wash?",
        "expected_intent": "inquire",
        "description": "Pricing inquiry"
    },
    {
        "id": 2,
        "message": "I want to book a wash for tomorrow",
        "expected_intent": "book",
        "description": "Booking intent"
    },
    {
        "id": 3,
        "message": "Your service damaged my car paint",
        "expected_intent": "complaint",
        "description": "Complaint intent"
    }
]


def print_separator():
    """Print visual separator."""
    print("=" * 80)


def print_test_header():
    """Print test header."""
    print_separator()
    print("INTENT CLASSIFIER UNIT TEST")
    print("Testing IntentClassifier DSPy Module with ollama/qwen3:8b")
    print_separator()
    print()


def print_test_case_header(test_case: Dict[str, Any]):
    """Print test case information."""
    print(f"Test Case {test_case['id']}: {test_case['description']}")
    print(f"Message: \"{test_case['message']}\"")
    print(f"Expected Intent: {test_case['expected_intent']}")


def print_result(test_case: Dict[str, Any], result: Any, passed: bool):
    """Print test result."""
    print(f"Classified Intent: {result.intent_class}")
    print(f"Reasoning: {result.reasoning}")

    if passed:
        print("Status: PASS ✓")
    else:
        print(f"Status: FAIL ✗ (Expected: {test_case['expected_intent']}, Got: {result.intent_class})")
    print()


def run_test():
    """Execute the IntentClassifier test."""
    print_test_header()

    # Test results tracking
    total_tests = len(TEST_CASES)
    passed_tests = 0
    failed_tests = 0
    test_results = []

    try:
        # Step 1: Configure DSPy
        print("Step 1: Configuring DSPy...")
        ensure_configured()
        print("✓ DSPy configured successfully with ollama/qwen3:8b")
        print()

        # Step 2: Instantiate IntentClassifier
        print("Step 2: Instantiating IntentClassifier...")
        classifier = IntentClassifier()
        print("✓ IntentClassifier instantiated successfully")
        print()

        # Step 3: Create mock conversation history
        print("Step 3: Creating mock conversation history...")
        conversation_history = empty_dspy_history()
        print("✓ Empty conversation history created")
        print()

        print_separator()
        print("RUNNING TEST CASES")
        print_separator()
        print()

        # Step 4: Test each message
        for test_case in TEST_CASES:
            try:
                print_test_case_header(test_case)

                # Call the classifier
                result = classifier(
                    conversation_history=conversation_history,
                    current_message=test_case['message']
                )

                # Verify result has intent_class field
                if not hasattr(result, 'intent_class'):
                    print("Status: FAIL ✗ (Missing intent_class field)")
                    print(f"Result fields: {dir(result)}")
                    failed_tests += 1
                    test_results.append({
                        'test_case': test_case,
                        'passed': False,
                        'error': 'Missing intent_class field'
                    })
                    print()
                    continue

                # Verify intent_class value matches expected
                classified_intent = result.intent_class.lower().strip()
                expected_intent = test_case['expected_intent'].lower().strip()
                passed = classified_intent == expected_intent

                if passed:
                    passed_tests += 1
                else:
                    failed_tests += 1

                test_results.append({
                    'test_case': test_case,
                    'result': result,
                    'passed': passed
                })

                print_result(test_case, result, passed)

            except Exception as e:
                print(f"Status: FAIL ✗ (Exception: {str(e)})")
                print()
                failed_tests += 1
                test_results.append({
                    'test_case': test_case,
                    'passed': False,
                    'error': str(e)
                })

        # Print summary
        print_separator()
        print("TEST SUMMARY")
        print_separator()
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()

        # Print detailed failures if any
        if failed_tests > 0:
            print("FAILED TEST DETAILS:")
            print_separator()
            for result in test_results:
                if not result['passed']:
                    test_case = result['test_case']
                    print(f"Test Case {test_case['id']}: {test_case['description']}")
                    print(f"Message: \"{test_case['message']}\"")
                    print(f"Expected: {test_case['expected_intent']}")

                    if 'error' in result:
                        print(f"Error: {result['error']}")
                    elif 'result' in result:
                        print(f"Got: {result['result'].intent_class}")
                    print()

        # Final verdict
        print_separator()
        if passed_tests >= 2:
            print("OVERALL RESULT: PASS (2+ of 3 messages classified correctly)")
        else:
            print("OVERALL RESULT: FAIL (Less than 2 of 3 messages classified correctly)")
        print_separator()

        return passed_tests >= 2

    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        print(f"Error Type: {type(e).__name__}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        print_separator()
        print("OVERALL RESULT: FAIL (Critical exception occurred)")
        print_separator()
        return False


if __name__ == "__main__":
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)