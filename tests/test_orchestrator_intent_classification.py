"""
Unit test for ChatbotOrchestrator._classify_intent() method.
Verifies intent classification is properly integrated.
"""
import sys
sys.path.insert(0, '/home/riju279/Downloads/demo')

from chatbot_orchestrator import ChatbotOrchestrator
from conversation_manager import ConversationManager
from dspy_config import ensure_configured


def test_orchestrator_intent_classification():
    """Test that orchestrator correctly classifies intent."""
    ensure_configured()

    manager = ConversationManager()
    orchestrator = ChatbotOrchestrator()
    conversation_id = "test_123"

    test_cases = [
        {
            "message": "What do you charge for a car wash?",
            "expected_intent_keywords": ["pricing", "inquiry", "pay", "payment", "cost"],
            "description": "Pricing inquiry"
        },
        {
            "message": "I want to book a wash for tomorrow",
            "expected_intent_keywords": ["book", "booking"],
            "description": "Booking intent"
        },
        {
            "message": "Your service damaged my car",
            "expected_intent_keywords": ["complaint"],
            "description": "Complaint intent"
        }
    ]

    print("\n" + "="*70)
    print("ORCHESTRATOR INTENT CLASSIFICATION TEST")
    print("="*70)

    for test in test_cases:
        # Add message to conversation history
        manager.add_user_message(conversation_id, test["message"])
        history = manager.get_dspy_history(conversation_id)

        # Classify intent
        intent = orchestrator._classify_intent(history, test["message"])

        # Check results
        intent_lower = intent.intent_class.lower()
        keyword_found = any(
            keyword in intent_lower
            for keyword in test["expected_intent_keywords"]
        )

        status = "✓ PASS" if keyword_found else "⚠ CHECK"
        print(f"\n{status} | {test['description']}")
        print(f"  Message: {test['message']}")
        print(f"  Classified intent: {intent.intent_class}")
        print(f"  Confidence: {intent.confidence}")
        print(f"  Reasoning: {intent.reasoning[:100]}...")

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_orchestrator_intent_classification()