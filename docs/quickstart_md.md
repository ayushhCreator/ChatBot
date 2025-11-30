# Quick Start Guide

Get your intelligent chatbot running in 5 minutes!

## 📋 Prerequisites

- Python 3.8+
- 16GB RAM
- Ollama installed

## 🚀 Installation

### Step 1: Clone and Install

```bash
# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Ollama

```bash
# Install Ollama from https://ollama.ai
# Then:
ollama pull llama3.2:3b

# Start Ollama (in separate terminal)
ollama serve
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Step 4: Test the System

```bash
# Run tests
python test_example.py
```

## 🎯 Basic Usage

### As a Standalone API

```bash
# Start the API server
python main.py

# Server runs at http://localhost:8000
```

### Test with cURL

```bash
# Process a message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "test_123",
    "user_message": "My name is John Doe",
    "current_state": "name_collection"
  }'
```

### Python Integration

```python
from chatbot_orchestrator import ChatbotOrchestrator
from config import ConversationState
from dspy_config import dspy_configurator

# Initialize
dspy_configurator.configure()
orchestrator = ChatbotOrchestrator()

# Process message
result = orchestrator.process_message(
    conversation_id="user_123",
    user_message="My name is Rajesh Kumar",
    current_state=ConversationState.NAME_COLLECTION
)

# Use results
print(result.extracted_data)
# {'first_name': 'Rajesh', 'last_name': 'Kumar', 'full_name': 'Rajesh Kumar'}

print(result.sentiment)
# {'interest': 8.0, 'anger': 1.0, ...}

print(result.should_proceed)
# True
```

## 🔌 Integration Examples

### With Existing pyWA Chatbot

```python
from chatbot_orchestrator import ChatbotOrchestrator
from pywa import WhatsApp

wa = WhatsApp(phone_id="...", token="...")
orchestrator = ChatbotOrchestrator()

@wa.on_message()
def handle_message(client, msg):
    # Process with intelligence
    result = orchestrator.process_message(
        conversation_id=msg.from_user.wa_id,
        user_message=msg.text,
        current_state=get_current_state(msg.from_user.wa_id)
    )
    
    # Use extracted data
    if result.extracted_data:
        save_to_database(result.extracted_data)
    
    # Adapt based on sentiment
    if not result.should_proceed:
        client.send_message(
            to=msg.from_user.wa_id,
            text="I sense frustration. How can I help?"
        )
```

### With FastAPI Webhook

```python
from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(data: dict):
    # Call intelligence layer
    response = requests.post(
        "http://localhost:8000/chat",
        json={
            "conversation_id": data["user_id"],
            "user_message": data["message"],
            "current_state": data["state"]
        }
    )
    
    result = response.json()
    
    # Process result
    return {"extracted": result["extracted_data"]}
```

## 📊 Common Use Cases

### 1. Extract Customer Name

```python
result = orchestrator.process_message(
    conversation_id="user_123",
    user_message="Call me Rajesh",
    current_state=ConversationState.NAME_COLLECTION
)

name = result.extracted_data["full_name"]  # "Rajesh"
```

### 2. Parse Vehicle Details

```python
result = orchestrator.process_message(
    conversation_id="user_123",
    user_message="I have a Honda City with plate MH12AB1234",
    current_state=ConversationState.VEHICLE_DETAILS
)

vehicle = result.extracted_data
# {
#   'vehicle_brand': 'Honda',
#   'vehicle_model': 'City',
#   'vehicle_plate': 'MH12AB1234'
# }
```

### 3. Understand Appointment Date

```python
result = orchestrator.process_message(
    conversation_id="user_123",
    user_message="Let's do it next Monday",
    current_state=ConversationState.DATE_SELECTION
)

date = result.extracted_data["appointment_date"]  # "2024-11-28"
```

### 4. Check Customer Sentiment

```python
result = orchestrator.process_message(
    conversation_id="user_123",
    user_message="This is taking too long!",
    current_state=ConversationState.SERVICE_SELECTION
)

if not result.should_proceed:
    # Customer is frustrated
    send_apology_and_simplify()

if result.sentiment["anger"] > 7:
    # Customer is angry
    escalate_to_human()
```

## ⚙️ Configuration

### Change Model

```python
# In config.py
MODEL_NAME = "phi3:mini"  # Smaller, faster
# or
MODEL_NAME = "llama3:8b"  # Larger, more accurate
```

### Adjust Sentiment Frequency

```python
# In config.py
SENTIMENT_CHECK_INTERVAL = 1  # Check every message
# or
SENTIMENT_CHECK_INTERVAL = 5  # Check every 5 messages
```

### Modify Thresholds

```python
# In config.py
SENTIMENT_THRESHOLDS = {
    "proceed": {
        "interest": 4.0,  # Lower = more lenient
        "anger": 8.0,     # Higher = more tolerant
    }
}
```

## 🐛 Troubleshooting

### Model Not Found
```bash
ollama pull llama3.2:3b
```

### Connection Refused
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start if not running
ollama serve
```

### Slow Performance
```python
# Use smaller model
MODEL_NAME = "phi3:mini"

# Reduce max tokens
MAX_TOKENS = 128
```

### Poor Extraction Quality
```python
# Increase temperature for creativity
TEMPERATURE = 0.5

# Or fine-tune on your data
# See ARCHITECTURE.md for fine-tuning guide
```

## 📚 Next Steps

1. **Read ARCHITECTURE.md** - Understand system design
2. **Check test_example.py** - See more examples
3. **Review pywa_integration.py** - Full WhatsApp integration
4. **Customize config.py** - Adjust to your needs

## 🎓 Learning Resources

### DSPy Tutorials
- [Email Extraction](https://dspy.ai/tutorials/email_extraction/)
- [Conversation History](https://dspy.ai/tutorials/conversation_history/)
- [Customer Service](https://dspy.ai/tutorials/customer_service_agent/)

### Ollama
- [Official Docs](https://ollama.ai/docs)
- [Model Library](https://ollama.ai/library)

## 💡 Tips & Best Practices

### 1. Start Simple
- Begin with sentiment analysis only
- Gradually add data extraction
- Test each component individually

### 2. Monitor Performance
- Log response times
- Track extraction accuracy
- Monitor memory usage

### 3. Iterate Based on Data
- Collect real conversations
- Analyze failure cases
- Fine-tune signatures

### 4. Balance Intelligence vs. Speed
- Not every message needs LLM processing
- Use rule-based for simple cases
- Reserve LLM for ambiguous inputs

### 5. Handle Edge Cases
- Always provide fallbacks
- Validate extracted data
- Gracefully handle errors

## 🤝 Support

If you encounter issues:

1. Check logs for errors
2. Verify Ollama is running
3. Test with `test_example.py`
4. Review ARCHITECTURE.md
5. Check model compatibility

## 🎉 Success Checklist

- [ ] Ollama installed and running
- [ ] Dependencies installed
- [ ] Model pulled (llama3.2:3b)
- [ ] test_example.py runs successfully
- [ ] API server starts without errors
- [ ] Sentiment analysis working
- [ ] Data extraction working
- [ ] Integrated with your bot

You're ready to go! 🚀
