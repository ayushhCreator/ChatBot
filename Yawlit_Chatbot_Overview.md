# Yawlit Intelligent Chatbot - Project Overview

This is a sophisticated car wash booking chatbot built with FastAPI, DSPy (AI framework), and Ollama (local LLM). The system uses AI to handle natural language conversations for car wash bookings.

## How to Run the Application:

### Prerequisites:
- Python 3.12 or higher
- Ollama (for running local LLM)
- Install required model: `ollama pull gemma3:4b` (as configured in config.py)

### Installation:
```bash
pip install -r requirements.txt
```

### Running the Application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```
Or directly:
```bash
python main.py
```

## Key Files and Their Functions:

1. **`main.py`** - Main entry point with FastAPI server
   - Sets up API endpoints for `/chat`, `/sentiment`, `/extract`, `/api/confirmation`
   - Handles startup/shutdown logic with DSPy configuration

2. **`orchestrator/message_processor.py`** - Core business logic
   - Main orchestrator that coordinates all components
   - Handles conversation state management
   - Processes user messages and generates responses

3. **`config.py`** - Configuration settings
   - LLM settings (Ollama URL, model: gemma3:4b)
   - Conversation states and flow rules
   - Sentiment thresholds and service information

4. **`models.py`** - Data validation models
   - Pydantic models for validated data extraction
   - Conversation context, responses, and sentiment analysis
   - Error handling for data validation

5. **`modules.py`** - AI/DSPy modules
   - Contains various DSPy modules (sentiment analyzer, name extractor, etc.)
   - Chain-of-thought reasoning for different tasks

6. **`conversation_manager.py`** - Conversation state management
   - Manages conversation history and state transitions
   - Stores user data during conversation

7. **`booking_orchestrator_bridge.py`** - Booking flow integration
   - Manages the booking confirmation process
   - Handles service request creation

8. **`conversation_script_manager.py`** - Personality and behavior scripts
   - Defines personality traits for different conversation states
   - Controls the chatbot's behavior in each state

## How the Chatbot Works (Simple Explanation):

1. **User starts a conversation** → Bot greets them and asks for their name

2. **Conversation Flow**:
   - Greeting → Name collection → Vehicle details → Date selection → Confirmation → Completed
   - Bot intelligently extracts information from user's natural language

3. **AI Features**:
   - **Sentiment Analysis**: Detects user's mood and responds appropriately
   - **Intent Classification**: Understands what user wants (book, inquire, etc.)
   - **Data Extraction**: Pulls out names, vehicle details, dates from messages
   - **Name Validation**: Filters out greetings like "hello" from being extracted as names

4. **Smart Confirmation**:
   - Uses DSPy to detect when user confirms booking
   - Offers "confirm/edit/cancel" options when all data is collected
   - Can auto-confirm after multiple attempts if user doesn't respond clearly

5. **State Management**:
   - Tracks where user is in booking process (greeting, name collection, etc.)
   - Ensures required information is collected before proceeding
   - Maintains conversation context across messages

6. **Data Validation**:
   - Validates all extracted information (phone numbers, dates, names)
   - Retroactively fills missing information
   - Ensures data quality before creating booking

7. **Service Request Creation**:
   - Once all required fields are collected and user confirms
   - Creates a service request with booking details
   - Stores booking information for the business

The system is designed to handle natural language input and guide users through a car wash booking process using AI to understand their needs, validate information, and create bookings efficiently.

## Project Summary

**Yawlit Car Wash Chatbot** is a sophisticated AI-powered booking system that handles customer conversations for car wash services using natural language processing. It's built with FastAPI and DSPy, using Ollama as the local LLM backend with the gemma3:4b model.

### Key Features:
- Natural language processing for booking conversations
- Sentiment analysis to adjust tone based on customer mood
- Smart data extraction from unstructured text
- State-based conversation flow (greeting → name → vehicle → date → confirmation → completed)
- Advanced validation and retroactive data completion
- Dual confirmation modes (CHAT vs BUTTON) for different business workflows

### To run:
Install dependencies and run with uvicorn on port 8002.

The system is designed to be robust with data validation, sentiment awareness, and conversation state management to provide a professional booking experience.