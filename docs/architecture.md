# System Architecture

## Overview

The intelligent chatbot system adds a DSPy-powered intelligence layer on top of your existing rule-based WhatsApp chatbot. It provides sentiment analysis, data extraction, and adaptive conversation flow without disrupting your current implementation.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                WhatsApp User                         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              pyWA (WhatsApp API)                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         Your Existing Rule-Based Chatbot             │
│  (Handles: Templates, Flow Control, ERPNext)         │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          Intelligence Layer (This System)            │
│  ┌─────────────────────────────────────────────┐    │
│  │   ChatbotOrchestrator (Main Coordinator)    │    │
│  └──────────┬──────────────────────────────────┘    │
│             │                                         │
│  ┌──────────┴────────────┬───────────────────┐      │
│  ▼                       ▼                    ▼      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐   │
│  │  Sentiment   │  │     Data      │  │  Conv.  │   │
│  │  Analyzer    │  │  Extractor    │  │ Manager │   │
│  └──────────────┘  └──────────────┘  └─────────┘   │
│         │                  │                │        │
│         └──────────┬───────┴────────────────┘        │
│                    ▼                                  │
│         ┌──────────────────────┐                     │
│         │   DSPy + Ollama LLM  │                     │
│         └──────────────────────┘                     │
└─────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Configuration Layer (`config.py`)
- **Purpose**: Centralized configuration management
- **Responsibility**: Define constants, thresholds, and system settings
- **Key Elements**:
  - Sentiment thresholds
  - Conversation states
  - Model parameters

### 2. DSPy Configuration (`dspy_config.py`)
- **Purpose**: Initialize and manage DSPy with Ollama
- **Responsibility**: Configure LLM connection
- **Key Features**:
  - Singleton pattern for configuration
  - Ollama connection management
  - Model initialization

### 3. Signatures (`signatures.py`)
- **Purpose**: Define input/output contracts for LLM tasks
- **Responsibility**: Structured prompting via DSPy signatures
- **Signatures Defined**:
  - `SentimentAnalysisSignature`: Multi-dimensional sentiment
  - `NameExtractionSignature`: Extract customer names
  - `VehicleDetailsExtractionSignature`: Parse vehicle info
  - `DateParsingSignature`: Natural language date parsing
  - `ResponseGenerationSignature`: Empathetic responses

### 4. Modules (`modules.py`)
- **Purpose**: Implement DSPy predictors
- **Responsibility**: Execute LLM tasks using signatures
- **Modules**:
  - `SentimentAnalyzer`: Analyze emotions
  - `NameExtractor`: Extract names
  - `VehicleDetailsExtractor`: Extract vehicle data
  - `DateParser`: Parse dates
  - `EmpathyResponseGenerator`: Generate responses

### 5. Sentiment Analyzer (`sentiment_analyzer.py`)
- **Purpose**: Sentiment analysis service
- **Responsibility**: 
  - Analyze customer emotions
  - Determine conversation flow decisions
  - Provide actionable sentiment scores
- **Key Methods**:
  - `analyze()`: Main sentiment analysis
  - `should_proceed()`: Decision logic
  - `needs_engagement()`: Engagement check
  - `should_disengage()`: Back-off check

### 6. Data Extractor (`data_extractor.py`)
- **Purpose**: Extract structured data from unstructured text
- **Responsibility**:
  - Parse names, vehicles, dates from natural language
  - Provide fallback rule-based parsing
  - Validate extracted data
- **Key Methods**:
  - `extract_name()`: Name extraction
  - `extract_vehicle_details()`: Vehicle parsing
  - `parse_date()`: Date parsing
  - `fallback_date_parsing()`: Rule-based fallback

### 7. Conversation Manager (`conversation_manager.py`)
- **Purpose**: Manage conversation state and history
- **Responsibility**:
  - Track message history (capped at 25)
  - Store user data
  - Maintain conversation state
- **Key Features**:
  - Per-conversation history
  - State management
  - Data persistence

### 8. Chatbot Orchestrator (`chatbot_orchestrator.py`)
- **Purpose**: Main coordinator for all components
- **Responsibility**:
  - Coordinate sentiment analysis
  - Trigger data extraction based on state
  - Generate suggestions for flow adaptation
  - Return unified response
- **Workflow**:
  1. Receive user message + state
  2. Update conversation history
  3. Analyze sentiment (every N messages)
  4. Extract data based on state
  5. Generate suggestions
  6. Return complete response

### 9. FastAPI Integration (`main.py`)
- **Purpose**: REST API for integration
- **Responsibility**:
  - Expose chatbot functionality via HTTP
  - Handle requests from external systems
- **Endpoints**:
  - `POST /chat`: Main processing endpoint
  - `POST /sentiment`: Sentiment analysis only
  - `POST /extract`: Data extraction only

### 10. pyWA Integration (`pywa_integration.py`)
- **Purpose**: Example WhatsApp integration
- **Responsibility**:
  - Show how to integrate with existing pyWA bot
  - Handle WhatsApp-specific logic
  - Demonstrate adaptive responses

## Data Flow

### Processing a User Message

```
1. User sends message via WhatsApp
   ↓
2. pyWA receives message
   ↓
3. Your rule-based bot determines current state
   ↓
4. Intelligence layer receives:
   - conversation_id
   - user_message
   - current_state
   ↓
5. ConversationManager updates history
   ↓
6. (Every N messages) SentimentAnalyzer analyzes sentiment
   ↓
7. DataExtractor extracts relevant data based on state
   ↓
8. Orchestrator generates suggestions
   ↓
9. Response returned with:
   - extracted_data
   - sentiment_scores
   - should_proceed flag
   - suggestions
   ↓
10. Your bot adapts flow based on response
    ↓
11. Message sent back to user
```

## Key Design Decisions

### 1. Minimal LLM Calls
- **Why**: Reduce costs and hallucinations
- **How**: 
  - Check sentiment every N messages (default: 2)
  - Only extract data when needed based on state
  - Use rule-based fallbacks

### 2. State-Based Processing
- **Why**: Efficient context management
- **How**: 
  - Only extract relevant data for current state
  - Reduce prompt complexity
  - Focused LLM tasks

### 3. Sentiment-Driven Flow
- **Why**: Adaptive, empathetic conversations
- **How**:
  - Multi-dimensional scoring
  - Clear thresholds for decisions
  - Actionable suggestions

### 4. Modular Architecture
- **Why**: Maintainability and testability
- **How**:
  - Single responsibility per module
  - ~100 lines per file
  - Clear interfaces

### 5. Fallback Mechanisms
- **Why**: Reliability even if LLM fails
- **How**:
  - Rule-based date parsing
  - Neutral sentiment as default
  - Graceful error handling

## Performance Characteristics

### CPU Usage
- **Model Size**: 2-3B parameters
- **Memory**: ~4-6GB for model
- **Inference**: ~1-3 seconds per call on CPU

### Cost Optimization
- **Tokens per Request**: ~150-250 tokens average
- **Sentiment Checks**: Every 2 messages (configurable)
- **History Cap**: 25 messages maximum

### Scalability
- **Concurrent Users**: Limited by Ollama capacity
- **Consider**: Multiple Ollama instances for scale
- **Alternative**: Switch to API-based LLM for production

## Integration Points

### Existing System Integration
```python
# Your existing rule-based bot
def handle_message(user_id, message, state):
    # Add intelligence layer
    result = orchestrator.process_message(user_id, message, state)
    
    # Use results
    if result.extracted_data:
        store_data(result.extracted_data)
    
    if not result.should_proceed:
        send_simplified_flow()
    else:
        continue_normal_flow()
```

### ERPNext Integration
```python
# After confirmation
if user_confirms:
    # Use collected data
    user_data = conversation_manager.get_user_data(user_id)
    
    # Send to ERPNext
    requests.post(ERPNEXT_WEBHOOK, json=user_data)
```

### Google Calendar Integration
```python
# Check availability
date = result.extracted_data.get("appointment_date")
available_slots = check_calendar_availability(date)

if not available_slots:
    suggest_alternative_dates()
```

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock LLM responses
- Validate data extraction

### Integration Tests
- Test full message flow
- Verify state transitions
- Check sentiment analysis

### Load Tests
- Test concurrent conversations
- Monitor memory usage
- Measure response times

## Future Enhancements

1. **Fine-tuning**: Train custom models on your conversation data
2. **Multi-language**: Support Hindi, regional languages
3. **Voice Notes**: Integrate speech-to-text
4. **Analytics**: Dashboard for sentiment trends
5. **A/B Testing**: Compare intelligence layer vs. rule-based

## Troubleshooting

### Common Issues

1. **Slow Response Times**
   - Solution: Use smaller model (phi3:mini)
   - Solution: Increase Ollama workers

2. **Poor Data Extraction**
   - Solution: Add examples to signatures
   - Solution: Fine-tune on your data

3. **Memory Issues**
   - Solution: Reduce MAX_CHAT_HISTORY
   - Solution: Lower MAX_TOKENS

4. **Incorrect Sentiment**
   - Solution: Adjust thresholds in config
   - Solution: Collect labeled data for fine-tuning
