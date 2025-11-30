"""
Unit test to validate SentimentAnalysisSignature definition.
Tests that all 5 sentiment dimensions are correctly defined.
"""

from signatures import SentimentAnalysisSignature


def test_sentiment_signature():
    """Test that SentimentAnalysisSignature has all required fields."""

    print("=" * 80)
    print("TESTING: SentimentAnalysisSignature")
    print("=" * 80)

    # Print signature name and docstring
    print(f"\nSignature Name: {SentimentAnalysisSignature.__name__}")
    print(f"Docstring: {SentimentAnalysisSignature.__doc__}")

    # Get the signature's fields
    sig = SentimentAnalysisSignature

    # Print input fields
    print("\n" + "=" * 80)
    print("INPUT FIELDS:")
    print("=" * 80)

    input_fields = {}
    if hasattr(sig, '__fields__'):
        for field_name, field_info in sig.__fields__.items():
            if not field_name.startswith('_'):
                # Check if it's an input field (not in output_fields)
                if not hasattr(sig, 'output_fields') or field_name not in getattr(sig, 'output_fields', []):
                    input_fields[field_name] = field_info
                    print(f"\n  {field_name}:")
                    print(f"    Type: {field_info.annotation if hasattr(field_info, 'annotation') else 'N/A'}")
                    if hasattr(field_info, 'description'):
                        print(f"    Description: {field_info.description}")

    # Alternative way to get fields from DSPy signature
    if hasattr(sig, 'input_fields'):
        print("\n  Input fields from signature.input_fields:")
        for field_name in sig.input_fields:
            print(f"    - {field_name}")

    # Print output fields
    print("\n" + "=" * 80)
    print("OUTPUT FIELDS:")
    print("=" * 80)

    output_fields = {}
    expected_sentiment_dimensions = [
        'interest_score',
        'anger_score',
        'disgust_score',
        'boredom_score',
        'neutral_score'
    ]

    # Try to get output fields from the signature
    if hasattr(sig, 'output_fields'):
        output_field_names = sig.output_fields
        print(f"\n  Output field names: {output_field_names}")

        for field_name in output_field_names:
            output_fields[field_name] = field_name
            print(f"\n  {field_name}:")

            # Try to get field info
            if hasattr(sig, '__fields__') and field_name in sig.__fields__:
                field_info = sig.__fields__[field_name]
                print(f"    Type: {field_info.annotation if hasattr(field_info, 'annotation') else 'N/A'}")
                if hasattr(field_info, 'description'):
                    print(f"    Description: {field_info.description}")

    # Inspect the actual signature definition more directly
    print("\n" + "=" * 80)
    print("DIRECT SIGNATURE INSPECTION:")
    print("=" * 80)

    # Get annotations
    if hasattr(sig, '__annotations__'):
        print("\n  Annotations:")
        for field_name, field_type in sig.__annotations__.items():
            print(f"    {field_name}: {field_type}")

    # Check for dspy.OutputField or dspy.InputField
    print("\n  Class attributes:")
    for attr_name in dir(sig):
        if not attr_name.startswith('_'):
            attr = getattr(sig, attr_name, None)
            if attr is not None and not callable(attr):
                print(f"    {attr_name}: {type(attr)} = {attr}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS:")
    print("=" * 80)

    # Count output fields
    output_field_count = len(output_fields) if output_fields else 0
    print(f"\n  Total output fields found: {output_field_count}")
    print("  Expected: 6 (5 sentiment dimensions + reasoning)")

    # Check for each sentiment dimension
    missing_dimensions = []
    found_dimensions = []

    for dimension in expected_sentiment_dimensions:
        if dimension in output_fields or (hasattr(sig, 'output_fields') and dimension in sig.output_fields):
            found_dimensions.append(dimension)
            print(f"\n  ✓ {dimension}: FOUND")
        else:
            missing_dimensions.append(dimension)
            print(f"\n  ✗ {dimension}: MISSING")

    # Check for reasoning field
    if 'reasoning' in output_fields or (hasattr(sig, 'output_fields') and 'reasoning' in sig.output_fields):
        print("\n  ✓ reasoning: FOUND")
    else:
        print("\n  ✗ reasoning: MISSING")

    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT:")
    print("=" * 80)

    if len(missing_dimensions) == 0 and len(found_dimensions) == 5:
        print("\n  ✓✓✓ PASS ✓✓✓")
        print("  All 5 sentiment dimensions are correctly defined!")
        return True
    else:
        print("\n  ✗✗✗ FAIL ✗✗✗")
        print(f"  Found {len(found_dimensions)}/5 sentiment dimensions")
        if missing_dimensions:
            print(f"  Missing dimensions: {', '.join(missing_dimensions)}")
        return False


if __name__ == "__main__":
    try:
        result = test_sentiment_signature()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        exit(1)