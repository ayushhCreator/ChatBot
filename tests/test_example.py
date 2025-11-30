"""
Example usage and testing script for the intelligent chatbot.
"""
from ..config import ConversationState
from ..chatbot_orchestrator import ChatbotOrchestrator
from dspy_config import dspy_configurator


def test_sentiment_analysis():
    """Test sentiment analysis."""
    print("\n" + "="*50)
    print("TESTING SENTIMENT ANALYSIS")
    print("="*50)
    
    orchestrator = ChatbotOrchestrator()
    conv_id = "test_conv_1"
    
    # Simulate interested customer
    messages = [
        ("Hi, I want to book a car wash", ConversationState.GREETING),
        ("Yes, I'm very interested!", ConversationState.SERVICE_SELECTION),
    ]
    
    for msg, state in messages:
        result = orchestrator.process_message(conv_id, msg, state)
        print(f"\nUser: {msg}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Should Proceed: {result.should_proceed}")


def test_name_extraction():
    """Test name extraction."""
    print("\n" + "="*50)
    print("TESTING NAME EXTRACTION")
    print("="*50)
    
    orchestrator = ChatbotOrchestrator()
    conv_id = "test_conv_2"
    
    # Test various name formats
    test_messages = [
        "My name is Hrijul Dey",
        "I'm Ayush Raj",
        "Call me Abhishek Kabir",
        "You can call me Bodhi Singh"
    ]
    
    for msg in test_messages:
        result = orchestrator.process_message(
            conv_id,
            msg,
            ConversationState.NAME_COLLECTION
        )
        print(f"\nUser: {msg}")
        print(f"Extracted: {result.extracted_data}")
        print(f"Response: {result.message}")


def test_vehicle_extraction():
    """Test vehicle details extraction."""
    print("\n" + "="*50)
    print("TESTING VEHICLE EXTRACTION")
    print("="*50)
    
    orchestrator = ChatbotOrchestrator()
    conv_id = "test_conv_3"
    
    # Test vehicle details
    test_messages = [
        "I have a Tata Punch with plate number MH12AB1234",
        "It's a Mahindra Thar, plate is DL04C5678",
        "My car is Maruti Suzuki, number KA05ML9012",
        "I drive a Hyundai Creta, plate TN10XY3456"
    ]
    
    for msg in test_messages:
        result = orchestrator.process_message(
            conv_id,
            msg,
            ConversationState.VEHICLE_DETAILS
        )
        print(f"\nUser: {msg}")
        print(f"Extracted: {result.extracted_data}")


def test_date_parsing():
    """Test date parsing."""
    print("\n" + "="*50)
    print("TESTING DATE PARSING")
    print("="*50)
    
    orchestrator = ChatbotOrchestrator()
    conv_id = "test_conv_4"
    
    # Test date expressions
    test_messages = [
        "I want it Day After Tomorrow",
        "How about next Friday?",
        "Can we do it Today Evening?",
        "Next Wednesday works for me"
    ]
    
    for msg in test_messages:
        result = orchestrator.process_message(
            conv_id,
            msg,
            ConversationState.DATE_SELECTION
        )
        print(f"\nUser: {msg}")
        print(f"Extracted: {result.extracted_data}")


def main():
    """Run all tests."""
    print("\nInitializing DSPy with Ollama...")
    dspy_configurator.configure()
    print("Configuration complete!\n")
    
    print("\nNOTE: Make sure Ollama is running with llama3.2:3b model")
    print("Run: ollama pull llama3.2:3b\n")
    
    try:
        test_sentiment_analysis()
        test_name_extraction()
        test_vehicle_extraction()
        test_date_parsing()
        
        print("\n" + "="*50)
        print("ALL TESTS COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("\nMake sure:")
        print("1. Ollama is running (ollama serve)")
        print("2. Model is pulled (ollama pull llama3.2:3b)")


if __name__ == "__main__":
    main()
