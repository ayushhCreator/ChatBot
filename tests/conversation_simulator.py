"""
Conversation Simulator - Simulates realistic customer conversations with mood swings and negotiation tactics.
"""
import httpx
import time
import random
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

API_BASE_URL = "http://localhost:8002"

# 25 Dialog Lists for controlled randomness
DIALOGS = {
    1: ["Hi", "Hello", "Hey there", "Good morning", "Namaste"],
    2: ["I need a car wash", "Looking for car cleaning", "Want to book a service", "My car is dirty"],
    3: ["I'm Rahul", "Name is Priya Sharma", "Call me Arjun", "I'm Sneha Patel", "Amit here"],
    4: ["What do you charge?", "How much?", "Prices?", "What's the cost?", "Tell me rates"],
    5: ["That's expensive!", "Too costly", "Can you give discount?", "That's too much", "Competitors charge less"],
    6: ["I saw cheaper rates elsewhere", "My friend got 20% off", "Can you match their price?", "This is overpriced"],
    7: ["Okay fine, what services?", "What do you offer?", "Tell me options", "What's included?"],
    8: ["I want the basic wash", "Premium detailing please", "Just polishing", "Full service"],
    9: ["I have a Honda City", "It's a Maruti Swift", "Tata Nexon", "Hyundai Creta", "BMW X5"],
    10: ["Plate number MH12AB1234", "Number is DL04C5678", "KA05ML9012", "TN10XY3456"],
    11: ["When are you available?", "What slots do you have?", "Can you do it tomorrow?", "I need it today"],
    12: ["Tomorrow works", "Next Monday", "This Friday", "Day after tomorrow"],
    13: ["Wait, I'm not sure", "Let me think", "This is confusing", "Too many questions"],
    14: ["Why do you need all this info?", "This is taking too long", "Can't we just book?", "Simplify this"],
    15: ["I'm getting frustrated", "This is annoying", "Why so complicated?", "I don't have time"],
    16: ["Maybe I should go elsewhere", "Your competitor is easier", "This is too much hassle"],
    17: ["Actually, tell me more", "Okay I'm interested", "Fine, continue", "Let's proceed"],
    18: ["What makes you different?", "Why should I choose you?", "Any guarantees?", "Reviews?"],
    19: ["Hmm, sounds okay", "I guess that works", "Not bad", "Acceptable"],
    20: ["Can I get a discount?", "Any offers running?", "First time customer discount?", "Loyalty program?"],
    21: ["Alright, let's book", "Okay I'm convinced", "Fine, go ahead", "Let's do this"],
    22: ["Wait, one more thing", "Actually I have a question", "Before we confirm", "Hold on"],
    23: ["What's your cancellation policy?", "Can I reschedule?", "What if I'm late?", "Payment options?"],
    24: ["Okay confirmed", "Book it", "Yes, finalize", "Let's go ahead"],
    25: ["Thanks", "Great", "See you then", "Perfect", "Goodbye"]
}

MOODS = ["happy", "skeptical", "angry", "bored", "interested", "frustrated", "neutral"]

STATE_SEQUENCE = [
    "greeting", "greeting", "name_collection", "service_selection", "service_selection",
    "tier_selection", "tier_selection", "tier_selection", "vehicle_details", "vehicle_details",
    "date_selection", "date_selection", "service_selection", "tier_selection", "service_selection",
    "date_selection", "service_selection", "tier_selection", "tier_selection", "confirmation",
    "confirmation", "confirmation", "confirmation", "confirmation", "completed"
]


@dataclass
class ConversationMetrics:
    """Track conversation metrics."""
    turn_number: int = 0
    total_latency: float = 0.0
    turn_latencies: List[float] = field(default_factory=list)
    extracted_data_count: int = 0
    sentiment_checks: int = 0
    state_transitions: List[str] = field(default_factory=list)
    
    def add_turn(self, latency: float, state: str):
        self.turn_number += 1
        self.total_latency += latency
        self.turn_latencies.append(latency)
        self.state_transitions.append(state)


class ConversationSimulator:
    """Simulates realistic customer conversations."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=1200.0)
    
    def generate_customer_message(self, turn: int) -> tuple[str, str]:
        """Generate customer message for given turn."""
        dialog_key = min(turn + 1, 25)
        message = random.choice(DIALOGS[dialog_key])
        mood = random.choice(MOODS)
        return message, mood
    
    def call_chatbot(self, conv_id: str, message: str, state: str) -> Dict[str, Any]:
        """Call chatbot API and measure latency."""
        start = time.time()
        
        try:
            response = self.client.post(
                "/chat",
                json={
                    "conversation_id": conv_id,
                    "user_message": message,
                    "current_state": state
                }
            )
            latency = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "latency": latency,
                    "response": data.get("message", ""),
                    "sentiment": data.get("sentiment"),
                    "extracted_data": data.get("extracted_data"),
                    "should_proceed": data.get("should_proceed", True),
                    "suggestions": data.get("suggestions")
                }
            else:
                return {
                    "success": False,
                    "latency": latency,
                    "error": response.text
                }
        except Exception as e:
            latency = time.time() - start
            return {
                "success": False,
                "latency": latency,
                "error": str(e)
            }
    
    def format_metadata(self, turn: int, mood: str, state: str, result: Dict, metrics: ConversationMetrics) -> str:
        """Format metadata in clean table format."""
        sentiment = result.get('sentiment', {})
        extracted = result.get('extracted_data', {})
        suggestions = result.get('suggestions', {})
        
        # Sentiment emoji
        sentiment_emoji = "😐"
        if sentiment:
            if sentiment.get('anger', 0) >= 7:
                sentiment_emoji = "😠"
            elif sentiment.get('interest', 0) >= 7:
                sentiment_emoji = "😊"
            elif sentiment.get('boredom', 0) >= 7:
                sentiment_emoji = "😴"
        
        metadata = f"""
┌─ 🤖 CHATBOT THINKING (Turn {turn + 1}) ──────────────────────────────────────────────────────
│
│ 🎯 State: {state:<25} 🎭 Mood: {mood:<15} {sentiment_emoji}
│ ⏱️  Latency: {result['latency']:.3f}s (Avg: {metrics.total_latency / metrics.turn_number:.3f}s)
│ ✅ Proceed: {result.get('should_proceed', True)}
│
│ 📊 SENTIMENT: Interest={sentiment.get('interest', '-') if sentiment else 'N/A':<4} Anger={sentiment.get('anger', '-') if sentiment else 'N/A':<4} Disgust={sentiment.get('disgust', '-') if sentiment else 'N/A':<4} Boredom={sentiment.get('boredom', '-') if sentiment else 'N/A':<4} Neutral={sentiment.get('neutral', '-') if sentiment else 'N/A':<4}
│ 📦 EXTRACTED: {str(extracted) if extracted else 'None'}
│ 💡 ACTIONS: {'Sentiment✓' if sentiment else 'Sentiment✗'}  {'Extract✓' if extracted else 'Extract✗'}  {'Engage' if suggestions.get('add_engagement') else 'Normal'}
│
└─────────────────────────────────────────────────────────────────────────────────────────
"""
        return metadata
    
    def run_conversation(self, conv_id: str, max_turns: int = 25) -> ConversationMetrics:
        """Run a single conversation simulation."""
        metrics = ConversationMetrics()
        
        print(f"\n{'='*80}")
        print(f"🎭 CONVERSATION #{conv_id.split('_')[-1]}")
        print(f"{'='*80}")
        
        for turn in range(max_turns):
            # Generate customer message
            message, mood = self.generate_customer_message(turn)
            state = STATE_SEQUENCE[turn]
            
            # Customer message with mood emoji
            mood_emoji = {"happy": "😊", "angry": "😠", "frustrated": "😤", 
                         "bored": "😴", "interested": "🤔", "skeptical": "🤨", "neutral": "😐"}
            print(f"\n👤 Customer [{mood_emoji.get(mood, '😐')} {mood}]: {message}")
            
            # Call chatbot
            result = self.call_chatbot(conv_id, message, state)
            
            if not result["success"]:
                print(f"   ❌ Error: {result.get('error')}")
                continue
            
            # Update metrics
            metrics.add_turn(result["latency"], state)
            if result.get("extracted_data"):
                metrics.extracted_data_count += 1
            if result.get("sentiment"):
                metrics.sentiment_checks += 1
            
            # Display chatbot response
            print(f"🤖 Chatbot: {result['response']}")
            
            # Display metadata
            metadata = self.format_metadata(turn, mood, state, result, metrics)
            print(metadata)
            
            # Check if should stop
            if not result.get("should_proceed", True):
                print("\n⚠️  ALERT: Customer frustration detected. Conversation paused.\n")
                break
            
            # Small delay for readability
            time.sleep(0.1)
        
        return metrics
    
    def print_summary(self, conv_id: str, metrics: ConversationMetrics):
        """Print conversation summary."""
        print(f"\n{'='*80}")
        print("📊 CONVERSATION SUMMARY")
        print(f"{'='*80}")
        print(f"  Turns: {metrics.turn_number:<3}  |  Total Time: {metrics.total_latency:.2f}s  |  Avg: {metrics.total_latency / metrics.turn_number:.3f}s")
        print(f"  Min: {min(metrics.turn_latencies):.3f}s  |  Max: {max(metrics.turn_latencies):.3f}s")
        print(f"  Extractions: {metrics.extracted_data_count}  |  Sentiment Checks: {metrics.sentiment_checks}")
        print(f"{'='*80}\n")
    
    def run_multiple_simulations(self, num_simulations: int = 4):
        """Run multiple conversation simulations."""
        print(f"\n{'#'*80}")
        print(f"🚀 RUNNING {num_simulations} CONVERSATION SIMULATIONS")
        print(f"{'#'*80}")
        
        all_metrics = []
        
        for i in range(num_simulations):
            conv_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i+1}"
            metrics = self.run_conversation(conv_id, max_turns=25)
            all_metrics.append(metrics)
            self.print_summary(conv_id, metrics)
            
            if i < num_simulations - 1:
                print(f"\n{'─'*80}\n")
                time.sleep(0.3)
        
        # Overall summary
        self.print_overall_summary(all_metrics)
    
    def print_overall_summary(self, all_metrics: List[ConversationMetrics]):
        """Print overall summary across all simulations."""
        total_turns = sum(m.turn_number for m in all_metrics)
        total_latency = sum(m.total_latency for m in all_metrics)
        total_extractions = sum(m.extracted_data_count for m in all_metrics)
        total_sentiment_checks = sum(m.sentiment_checks for m in all_metrics)
        
        all_latencies = []
        for m in all_metrics:
            all_latencies.extend(m.turn_latencies)
        
        print(f"\n{'#'*80}")
        print(f"🎯 OVERALL SUMMARY - {len(all_metrics)} CONVERSATIONS")
        print(f"{'#'*80}")
        print("\n  📈 PERFORMANCE METRICS:")
        print(f"     Total Turns: {total_turns}")
        print(f"     Total Time: {total_latency:.2f}s")
        print(f"     Avg per Turn: {total_latency / total_turns:.3f}s")
        print(f"     Range: {min(all_latencies):.3f}s - {max(all_latencies):.3f}s")
        print("\n  🎯 INTELLIGENCE METRICS:")
        print(f"     Data Extractions: {total_extractions}")
        print(f"     Sentiment Checks: {total_sentiment_checks}")
        print(f"     Success Rate: {(total_extractions / total_turns * 100):.1f}%")
        print(f"\n{'#'*80}\n")


def main():
    """Main entry point."""
    print("\n🎬 Conversation Simulator Starting...\n")
    
    # Check if API is running
    try:
        response = httpx.get(f"{API_BASE_URL}/", timeout=1200.0)
        if response.status_code != 200:
            print("❌ API is not responding. Please start the FastAPI server first:")
            print("   cd src && uvicorn main:app --host 0.0.0.0 --port 8002")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API at {API_BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Please start the FastAPI server first:")
        print("   cd src && uvicorn main:app --host 0.0.0.0 --port 8002")
        return
    
    print("✅ API is running. Starting simulations...\n")
    
    simulator = ConversationSimulator()
    simulator.run_multiple_simulations(num_simulations=4)
    
    print("\n✅ All simulations completed!\n")


if __name__ == "__main__":
    main()