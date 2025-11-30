# Intelligent Car Wash Chatbot with DSPy

An intelligent layer built with DSPy and Ollama that adds sentiment analysis, empathy, and smart data extraction to your existing rule-based WhatsApp chatbot.

## 🎯 Features

- **Multi-dimensional Sentiment Analysis**: Tracks interest, anger, disgust, boredom, and neutral states (1-10 scale)
- **Smart Data Extraction**: Extracts names, vehicle details, and dates from unstructured user messages
- **Adaptive Conversation Flow**: Modifies responses based on customer sentiment
- **Cost-Efficient**: Designed to run on 2-3B parameter models on CPU (16GB RAM)
- **Hallucination-Free**: Minimizes LLM usage to reduce costs and hallucinations

## 📁 Project Structure

```
├── config.py                    # Configuration and settings
├── dspy_config.py              # DSPy LLM initialization
├── signatures.py               # DSPy signatures for tasks
├── modules.py                  # DSPy modules/predictors
├── sentiment_analyzer.py       # Sentiment analysis service
├── data_extractor.py           # Data extraction service
├── conversation_manager.py     # Chat history management
├── chatbot_orchestrator.py     # Main orchestrator
├── main.py                     # FastAPI integration
├── test_example.py             # Usage examples
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Setup Ollama

```bash
# Install Ollama (https://ollama.ai)
# Then pull the model
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

### 3. Test the System

```bash
python test_example.py
```

### 4. Run the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📊 API Endpoints

### 1. Process Chat Message
```bash
POST /chat
{
  "conversation_id": "user_12345",
  "user_message": "My name is John Doe",
  "current_state": "name_collection"
}
```

**Response:**
```json
{
  "message": "Got it! Nice to meet you, John Doe!",
  "should_proceed": true,
  "extracted_data": {
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe"
  },
  "sentiment": {
    "interest": 8.0,
    "anger": 1.0,
    "disgust": 1.0,
    "boredom": 2.0,
    "neutral": 3.0
  },
  "suggestions": {
    "modify_response_tone": false,
    "add_engagement": true,
    "simplify_flow": false,
    "offer_help": false
  }
}
```

### 2. Analyze Sentiment Only
```bash
POST /sentiment
{
  "conversation_id": "user_12345",
  "user_message": "I'm really frustrated with this"
}
```

### 3. Extract Data Only
```bash
POST /extract
{
  "user_message": "I have a Honda City with plate MH12AB1234",
  "extraction_type": "vehicle"
}
```

## 🔧 Integration with Existing pyWA Chatbot

### Example Integration

```python
from pywa import WhatsApp
from chatbot_orchestrator import ChatbotOrchestrator
from config import ConversationState

# Initialize
wa = WhatsApp(...)
orchestrator = ChatbotOrchestrator()

@wa.on_message()
def handle_message(client, message):
    # Get current state from your rule-based system
    current_state = get_current_state(message.from_user.phone)
    
    # Process with intelligent layer
    result = orchestrator.process_message(
        conversation_id=message.from_user.phone,
        user_message=message.text,
        current_state=current_state
    )
    
    # Use extracted data
    if result.extracted_data:
        # Store in your system
        save_user_data(result.extracted_data)
    
    # Adapt based on sentiment
    if not result.should_proceed:
        # Customer is frustrated - simplify flow
        send_simplified_message(client, message)
    elif result.suggestions["add_engagement"]:
        # Customer is interested - add personality
        send_engaging_message(client, message)
    else:
        # Continue normal flow
        send_normal_message(client, message)
```

## 🎨 Conversation States

The system supports these conversation states:
- `greeting` - Initial greeting
- `name_collection` - Collecting customer name
- `service_selection` - Service category selection
- `tier_selection` - Service tier selection
- `vehicle_type` - Vehicle type selection
- `vehicle_details` - Vehicle brand/model/plate
- `date_selection` - Appointment date
- `slot_selection` - Time slot selection
- `address_collection` - Address details
- `confirmation` - Final confirmation
- `completed` - Booking completed

## 📈 Sentiment Decision Logic

### Should Proceed?
- **YES** if: Interest ≥ 5 AND (Anger < 7 AND Disgust < 7 AND Boredom < 7)
- **NO** if: Anger ≥ 7 OR Disgust ≥ 7 OR Boredom ≥ 7

### Needs Engagement?
- **YES** if: Interest ≥ 7

### Should Disengage?
- **YES** if: Anger ≥ 7 OR Disgust ≥ 7 OR Boredom ≥ 8

## 🔄 Data Extraction Examples

### Name Extraction
```python
Input: "My name is Rajesh Kumar"
Output: {
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "full_name": "Rajesh Kumar"
}
```

### Vehicle Extraction
```python
Input: "I have a Honda City with plate MH12AB1234"
Output: {
  "vehicle_brand": "Honda",
  "vehicle_model": "City",
  "vehicle_plate": "MH12AB1234"
}
```

### Date Parsing
```python
Input: "Let's do it next Monday"
Output: {
  "appointment_date": "2024-11-28"
}
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Model settings
MODEL_NAME = "llama3.2:3b"
MAX_TOKENS = 256
TEMPERATURE = 0.3

# Conversation settings
MAX_CHAT_HISTORY = 25
SENTIMENT_CHECK_INTERVAL = 2  # Check every N messages

# Sentiment thresholds
SENTIMENT_THRESHOLDS = {
    "proceed": {"interest": 5.0, "anger": 7.0, ...},
    ...
}
```

## 🎯 Performance Optimization

### CPU Optimization
- Uses 2-3B parameter models (llama3.2:3b)
- Minimal token generation (256 max)
- Checks sentiment every 2 messages (configurable)
- Caps chat history to 25 messages

### Cost Reduction
- LLM only called when needed
- Fallback to rule-based parsing
- Batch operations where possible

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Model Not Found
```bash
# Pull the model
ollama pull llama3.2:3b

# List available models
ollama list
```

### Memory Issues
```bash
# Use smaller model
MODEL_NAME = "llama3.2:3b"  # or "phi3:mini"

# Reduce max tokens
MAX_TOKENS = 128
```

## 📚 References

This implementation is inspired by:
- [DSPy Email Extraction](https://dspy.ai/tutorials/email_extraction/)
- [DSPy Conversation History](https://dspy.ai/tutorials/conversation_history/)
- [DSPy Customer Service Agent](https://dspy.ai/tutorials/customer_service_agent/)
- [DSPy Classification](https://dspy.ai/tutorials/classification_finetuning/)

## 📝 License

MIT License - Feel free to use and modify for your needs.

## 🤝 Contributing

Contributions welcome! Please follow the single responsibility principle and keep files under 100 lines where possible.
