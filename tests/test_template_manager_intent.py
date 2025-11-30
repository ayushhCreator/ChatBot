#!/usr/bin/env python3
"""
Unit Test: template_manager.decide_response_mode() - Intent Parameter Testing
"""

import inspect
from template_manager import TemplateManager


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def test_method_signature():
    """Examine the method signature."""
    print_section("METHOD SIGNATURE ANALYSIS")

    # Get the method signature
    signature = inspect.signature(TemplateManager.decide_response_mode)

    print("Method: TemplateManager.decide_response_mode()")
    print("\nParameters:")

    required_params = []
    optional_params = []

    for param_name, param in signature.parameters.items():
        if param_name == 'self':
            continue

        if param.default == inspect.Parameter.empty:
            required_params.append(param_name)
            print(f"  - {param_name}: {param.annotation} (REQUIRED)")
        else:
            optional_params.append(param_name)
            default_val = param.default
            print(f"  - {param_name}: {param.annotation} = {default_val} (OPTIONAL)")

    print("\nSummary:")
    print(f"  Required parameters: {required_params}")
    print(f"  Optional parameters: {optional_params}")
    print(f"  Has 'intent' parameter: {'intent' in signature.parameters}")

    return 'intent' in signature.parameters, signature


def test_current_implementation():
    """Test current implementation with various messages."""
    print_section("CURRENT IMPLEMENTATION TESTING")

    manager = TemplateManager()

    test_cases = [
        {
            "name": "Test 1: Pricing Intent",
            "message": "What do you charge?",
            "expected_intent": "pricing",
            "description": "Should detect pricing keywords"
        },
        {
            "name": "Test 2: Catalog Intent",
            "message": "What services do you offer?",
            "expected_intent": "catalog",
            "description": "Should detect catalog/services keywords"
        },
        {
            "name": "Test 3: Booking Intent",
            "message": "I want to book a wash",
            "expected_intent": "booking",
            "description": "Should detect booking keywords"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"{test_case['name']}")
        print(f"  Message: \"{test_case['message']}\"")
        print(f"  Expected Intent: {test_case['expected_intent']}")
        print(f"  Description: {test_case['description']}")

        try:
            # Call with current parameters
            mode, template_key = manager.decide_response_mode(
                user_message=test_case['message']
            )

            print("  ✓ PASS - Method executed successfully")
            print(f"    Response Mode: {mode.value}")
            print(f"    Template Key: '{template_key}'")

            # Check if result matches expected intent
            intent_detected = template_key == test_case['expected_intent']
            print(f"    Intent Detection: {'✓ CORRECT' if intent_detected else '✗ INCORRECT'}")

            results.append({
                "test": test_case['name'],
                "success": True,
                "mode": mode,
                "template_key": template_key,
                "intent_detected": intent_detected
            })

        except Exception as e:
            print(f"  ✗ FAIL - Exception: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })

        print()

    return results


def test_intent_parameter():
    """Test if intent parameter can be passed."""
    print_section("INTENT PARAMETER TESTING")

    manager = TemplateManager()

    print("Attempting to call decide_response_mode() with 'intent' parameter...")
    print()

    test_cases = [
        ("What do you charge?", "pricing"),
        ("What services do you offer?", "catalog"),
        ("I want to book a wash", "booking")
    ]

    intent_param_works = True

    for message, intent in test_cases:
        print(f"Test: message=\"{message}\", intent=\"{intent}\"")

        try:
            # Try passing intent parameter
            mode, template_key = manager.decide_response_mode(
                user_message=message,
                intent=intent  # THIS IS THE KEY TEST
            )
            print("  ✓ SUCCESS - Intent parameter accepted")
            print(f"    Mode: {mode.value}, Template: '{template_key}'")

        except TypeError as e:
            print("  ✗ FAILED - Intent parameter NOT accepted")
            print(f"    Error: {e}")
            intent_param_works = False

        print()

    return intent_param_works


def generate_report(has_intent_param: bool, test_results: list, intent_param_works: bool):
    """Generate final report."""
    print_section("FINAL REPORT")

    print("Current Implementation Status:")
    print(f"  1. Method signature has 'intent' parameter: {'YES' if has_intent_param else 'NO'}")
    print(f"  2. Intent parameter is functional: {'YES' if intent_param_works else 'NO'}")

    print("\nTest Results Summary:")
    for result in test_results:
        if result['success']:
            status = "✓ PASS" if result['intent_detected'] else "⚠ PARTIAL"
            print(f"  {status} - {result['test']}")
            print(f"        Mode: {result['mode'].value}, Template: '{result['template_key']}'")
        else:
            print(f"  ✗ FAIL - {result['test']}: {result['error']}")

    print("\nCurrent Behavior Analysis:")
    print("  The decide_response_mode() method currently:")
    print("    - Uses keyword matching to detect intent from message content")
    print("    - Returns template_key based on matched keywords")
    print("    - Does NOT accept explicit 'intent' parameter")

    print("\nRefactor Status:")
    if has_intent_param and intent_param_works:
        print("  ✓ READY FOR INTENT LOGIC")
        print("    The method accepts 'intent' parameter and can be enhanced")
        print("    with intent-driven logic.")
    else:
        print("  ⚠ REFACTOR NEEDED")
        print("    The method does NOT accept 'intent' parameter.")
        print("    Refactoring required to add:")
        print("      - 'intent' parameter to method signature")
        print("      - Intent-driven decision logic")
        print("      - Integration with IntentClassifier")


def main():
    """Run all tests and generate report."""
    print_section("TEMPLATE MANAGER INTENT TESTING")
    print("Testing: TemplateManager.decide_response_mode()")
    print("Purpose: Check if method accepts 'intent' parameter and uses intent-aware logic")

    # Test 1: Check method signature
    has_intent_param, signature = test_method_signature()

    # Test 2: Test current implementation
    test_results = test_current_implementation()

    # Test 3: Try passing intent parameter
    intent_param_works = test_intent_parameter()

    # Generate final report
    generate_report(has_intent_param, test_results, intent_param_works)

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
