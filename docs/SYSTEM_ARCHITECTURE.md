# Yawlit Intelligent Chatbot - Complete System Architecture

**Version**: Phase 2 (Dec 2024)
**Status**: Production-Ready with Known Optimizations
**Framework**: FastAPI + DSPy + Pydantic

---

## 1. High-Level System Overview

```bash
┌────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI HTTP LAYER                               │
│                  (main.py - REST API Endpoints)                            │
├──────┬──────────────┬──────────────┬──────────────┬───────────────┬────────┤
│ GET  │  POST /chat  │ POST /extract│ POST /sentiment│ POST /api/  │ Startup│
│  /   │              │              │               │ confirmation │ Hook   │
└──────┴──────────────┴──────────────┴──────────────┴───────────────┴────────┘
         │                │                │              │
         │                └────────────────┴──────────────┘
         │                    │
         └────────────────────┼────────────────────────────┐
                              │                            │
                    ┌─────────▼──────────┐      ┌──────────▼──────────┐
                    │ MessageProcessor   │      │ Booking Bridge      │
                    │ (orchestrator)     │      │ (booking_flow)      │
                    └────────────────────┘      └─────────────────────┘
                              │
        ┌─────────────────────┼──────────────────────────┐
        │                     │                          │
        ▼                     ▼                          ▼
   ┌──────────────┐   ┌─────────────────┐      ┌────────────────┐
   │ Coordinator  │   │ Service Layer   │      │ Utility Layer  │
   │  Classes     │   │   Services      │      │     Utils      │
   └──────────────┘   └─────────────────┘      └────────────────┘
```

---

## 2. Request Processing Pipeline

### 2.1 Main Processing Flow (POST /chat)

```bash
╔════════════════════════════════════════════════════════════════════════════╗
║                         MESSAGE PROCESSOR                                  ║
║                   (orchestrator/message_processor.py)                      ║
╚════════════════════════════════════════════════════════════════════════════╝

INPUT: {conversation_id, user_message}
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 1: Conversation Management                                 │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ ConversationManager.add_user_message(conv_id, message)     │  │
  │ │  └─→ Stores message, retrieves context + current_state     │  │
  │ │  └─→ Returns ValidatedConversationContext                  │  │
  │ │                                                            │  │
  │ │ ConversationManager.get_dspy_history(conv_id)              │  │
  │ │  └─→ Converts messages to dspy.History format              │  │
  │ │  └─→ Used by all AI modules                                │  │
  │ └────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘
  │
  │ Current State: GREETING / NAME_COLLECTION / ... / COMPLETED
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 2: Sentiment Analysis                                      │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ SentimentAnalysisService.analyze(history, current_msg)     │  │
  │ │  └─→ SentimentAnalyzer module (DSPy)                       │  │
  │ │  └─→ Extracts: interest, anger, disgust, boredom, neutral  │  │
  │ │  └─→ Returns ValidatedSentimentScores (1-10 scale)         │  │
  │ └────────────────────────────────────────────────────────────┘  │
  │                                                                 │
  │ Sentiment used for:                                             │
  │  • Response tone decision                                       │
  │  • State transition logic (upset → SERVICE_SELECTION)           │
  │  • Response generation brevity                                  │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 3: Intent Classification                                   │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ ExtractionCoordinator.classify_intent(history, msg)        │  │
  │ │  └─→ IntentClassifier module (DSPy)                        │  │
  │ │  └─→ Classifies: inquire, pricing, booking, complaint, etc │  │
  │ │  └─→ Returns ValidatedIntent with confidence               │  │
  │ └────────────────────────────────────────────────────────────┘  │
  │                                                                 │
  │ Intent used for:                                                │
  │  • Response mode decision (OVERRIDES sentiment)                 │
  │  • Template selection                                           │
  │  • Determines whether to show templates vs LLM response         │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 4: Response Mode Decision                                  │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ TemplateManager.decide_response_mode(msg, intent, sent)    │  │
  │ │  └─→ Mode can be: LLM_ONLY, TEMPLATE_ONLY, HYBRID          │  │
  │ │  └─→ Intent OVERRIDES sentiment                            │  │
  │ │  └─→ Returns (mode, template_key)                          │  │
  │ └────────────────────────────────────────────────────────────┘  │
  │                                                                 │
  │ Example Decision Logic:                                         │
  │  • pricing inquiry → TEMPLATE_ONLY (show service prices)        │
  │  • general greeting → HYBRID (LLM + gentle template)            │
  │  • complaint → LLM_ONLY (empathetic response)                   │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 5: Data Extraction                                         │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ ExtractionCoordinator.extract_for_state(state, msg, hist)  │  │
  │ │                                                            │  │
  │ │  5a. Filter history to USER-ONLY messages                  │  │
  │ │      └─→ Prevents LLM confusion from chatbot responses     │  │
  │ │                                                            │  │
  │ │  5b. Extract Name (NameExtractor module)                   │  │
  │ │      └─→ first_name, last_name, full_name                  │  │
  │ │      └─→ Validation: not greeting stopwords, not vehicle   │  │
  │ │      └─→ Stops if matches vehicle brand enum               │  │
  │ │                                                            │  │
  │ │  5c. Extract Phone (PhoneExtractor module)                 │  │
  │ │      └─→ phone_number (10-digit Indian format)             │  │
  │ │                                                            │  │
  │ │  5d. Extract Vehicle (VehicleDetailsExtractor module)      │  │
  │ │      └─→ vehicle_brand, vehicle_model, vehicle_plate       │  │
  │ │      └─→ Stops if brand matches name (prevent confusion)   │  │
  │ │                                                            │  │
  │ │  5e. Extract Date (DateParser module)                      │  │
  │ │      └─→ appointment_date (parsed to standard format)      │  │
  │ │                                                            │  │
  │ │  Returns: Dict[field_name → value] or None                 │  │
  │ └────────────────────────────────────────────────────────────┘  │
  │                                                                 │
  │ Extracted Data Stored Immediately:                              │
  │  ConversationManager.store_user_data(conv_id, key, value)    │  │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 6: Retroactive Validation                                  │
  │ ┌────────────────────────────────────────────────────────────┐  │
  │ │ final_validation_sweep(state, extracted_data, history)     │ │
  │ │                                                            │  │
  │ │  6a. Determine missing fields for current state            │  │
  │ │                                                            │ │
  │ │  6b. For each missing field:                             │ │
  │ │      └─→ Skip if already extracted in current turn      │ │
  │ │      └─→ Scan history (last 2 messages via config)       │ │
  │ │      └─→ Retroactively extract from earlier turns       │ │
  │ │      └─→ User-only history to prevent chatbot confusion │ │
  │ │                                                            │ │
  │ │  6c. Return filled data (merged with current extraction) │ │
  │ │                                                            │ │
  │ │  Returns: Dict with all retroactively found data         │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Performance: ~10-20 seconds (limited to last 2 messages)     │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 7: Empathetic Response Generation                         │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ IF should_send_llm_response(response_mode):               │ │
  │ │   _generate_empathetic_response(history, msg, state, sent)│ │
  │ │                                                            │ │
  │ │   7a. Analyze Tone (SentimentToneAnalyzer)               │ │
  │ │       └─→ Converts sentiment scores to tone + max_sent   │ │
  │ │       └─→ Angry → brief, helpful tone                   │ │
  │ │       └─→ Bored → engaging tone                         │ │
  │ │                                                            │ │
  │ │   7b. Generate Response (ToneAwareResponseGenerator)     │ │
  │ │       └─→ Uses tone directive + max_sentences constraint │ │
  │ │       └─→ Returns empathetic response                   │ │
  │ │                                                            │ │
  │ │  Returns: string (LLM response) or fallback               │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Response uses: conversation history (includes assistant msgs) │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 8: Response Composition                                   │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ ResponseComposer.compose_response(user_msg, llm_resp,...)│ │
  │ │                                                            │ │
  │ │  8a. Decide response mode                                │ │
  │ │  8b. Add LLM response (if should_send_llm_response)      │ │
  │ │  8c. Add template content (if should_send_template)      │ │
  │ │  8d. Render template with extracted variables            │ │
  │ │  8e. Return final composed response                      │ │
  │ │                                                            │ │
  │ │  Returns: {"response": "...", "metadata": {...}}         │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Modes:                                                         │
  │  • LLM_ONLY: Just the empathetic response                     │
  │  • TEMPLATE_ONLY: Just the template (prices, info, etc)      │
  │  • HYBRID: LLM response + separator + template               │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 9: Typo Detection (CONFIRMATION state only)              │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ IF current_state == CONFIRMATION && extracted_data:       │ │
  │ │   ExtractionCoordinator.detect_typos_in_confirmation()   │ │
  │ │                                                            │ │
  │ │   └─→ TypoDetector module (DSPy) checks each field       │ │
  │ │   └─→ Suggests corrections: {"field": "correction"}      │ │
  │ │                                                            │ │
  │ │  Returns: Dict of corrections or None                    │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Only runs in CONFIRMATION state (not every turn)              │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 10: State Transition Logic                               │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ StateCoordinator.determine_next_state(state, sentiment,   │ │
  │ │                                        extracted_data)     │ │
  │ │                                                            │ │
  │ │  10a. Priority 1: Check sentiment (anger > 6.0)         │ │
  │ │       └─→ Return SERVICE_SELECTION (offer help)          │ │
  │ │                                                            │ │
  │ │  10b. Priority 2: Check confirmation state               │ │
  │ │       └─→ If user confirms → COMPLETED                  │ │
  │ │                                                            │ │
  │ │  10c. Priority 3: Data-driven transitions                │ │
  │ │       ┌─ Name extracted → NAME_COLLECTION              │ │
  │ │       ├─ Vehicle extracted → VEHICLE_DETAILS            │ │
  │ │       ├─ Date extracted → DATE_SELECTION                │ │
  │ │       └─ General progression                             │ │
  │ │                                                            │ │
  │ │  10d. Priority 4: Keyword-based (service keywords)       │ │
  │ │       └─→ Only from GREETING → SERVICE_SELECTION        │ │
  │ │                                                            │ │
  │ │  10e. Otherwise: Stay in current state                   │ │
  │ │                                                            │ │
  │ │  Returns: next_state (ConversationState enum)            │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ State Machine (11 states):                                    │
  │  GREETING → NAME_COLLECTION → VEHICLE_DETAILS → DATE_SELECTION
  │      ↓                                              ↓          │
  │  SERVICE_SELECTION ──────────────────────→ CONFIRMATION → COMPLETED
  │                                                                 │
  │ Update conversation state:                                    │
  │  ConversationManager.update_state(conv_id, next_state,reason)│
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 11: Scratchpad Update                                    │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ ScratchpadCoordinator.get_or_create(conv_id)              │ │
  │ │ ScratchpadCoordinator.update_from_extraction(...)         │ │
  │ │                                                            │ │
  │ │  11a. For each extracted field → update scratchpad       │ │
  │ │  11b. Track booking form completeness (%)                │ │
  │ │  11c. Mark which fields are filled                       │ │
  │ │                                                            │ │
  │ │  Returns: Updated scratchpad with completeness score     │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Scratchpad tracks booking progress:                          │
  │  {first_name, vehicle_brand, vehicle_model, vehicle_plate,  │ │
  │   appointment_date, phone, etc}                              │
  └─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────────────────────────────────────────────────┐
  │ STEP 12: Confirmation Validation                              │
  │ ┌────────────────────────────────────────────────────────────┐ │
  │ │ Check ALL required fields present:                         │ │
  │ │  CONFIRMATION state requires:                             │ │
  │ │   {first_name, vehicle_brand, vehicle_model,              │ │
  │ │    vehicle_plate, appointment_date}                       │ │
  │ │                                                            │ │
  │ │  should_confirm = (next_state == CONFIRMATION &&
  │ │                    required_fields ⊆ extracted_fields)   │ │
  │ │                                                            │ │
  │ │  Returns: boolean flag for confirmation readiness         │ │
  │ └────────────────────────────────────────────────────────────┘ │
  │                                                                 │
  │ Only shows confirmation screen when ALL data present         │
  └─────────────────────────────────────────────────────────────────┘
  │
  │
  └──────────────────────────────────────────────────────────────────┐
         │                                                           │
         ▼                                                           │
   ╔═════════════════════════════════════════════════════════════╗   │
   ║  RETURN ValidatedChatbotResponse                           ║   │
   ║  {                                                          ║   │
   ║    message: "...",                    # Composed response  ║   │
   ║    should_proceed: true,                                   ║   │
   ║    extracted_data: {name, vehicle...},                     ║   │
   ║    sentiment: {interest, anger, ...},                      ║   │
   ║    should_confirm: boolean,           # Show confirmation? ║   │
   ║    scratchpad_completeness: 0-100,    # Form % filled     ║   │
   ║    state: "name_collection",          # Next state        ║   │
   ║    data_extracted: boolean,           # Any data found?    ║   │
   ║    typo_corrections: {...},           # If CONFIRMATION    ║   │
   ║  }                                                          ║   │
   ╚═════════════════════════════════════════════════════════════╝   │
```

---

## 3. Coordinator Architecture (Single Responsibility Principle)

```bash
                    ┌──────────────────────────┐
                    │  MessageProcessor        │
                    │ (orchestrator)           │
                    │ Delegates to:            │
                    └───────┬──────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
    │ExtractionC  │   │StateCoord    │   │ScratchpadCoord   │
    │Coordinator  │   │Coordinator   │   │Coordinator       │
    └─────────────┘   └──────────────┘   └──────────────────┘

    Responsibility:    Responsibility:    Responsibility:
    • Extract name     • Transitions      • Track form
    • Extract phone      between states    progress
    • Extract vehicle  • Apply rules     • Update booking
    • Extract date     • Use sentiment   • Calculate %
    • Classify intent  • Validate data   complete
    • Detect typos     • Logic flow      • Suggest CTAs

    Delegates to:      Uses:              Uses:
    • NameExtractor    • StateCoordinator • BookingScratchpad
    • PhoneExtractor   • SentimentScores • ServiceRequest
    • VehicleExt       • ExtractedData   • ConversationMgr
    • DateParser       • UserMessage
    • IntentClassifier
    • TypoDetector
```

---

## 4. Data Flow Architecture

```bash
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Per-Conversation Storage (ConversationManager)                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ conversations: Dict[conv_id → ValidatedConversationContext]   │   │
│  │                                                                 │   │
│  │ ValidatedConversationContext:                                  │   │
│  │  ├─ conversation_id: str                                       │   │
│  │  ├─ messages: List[ValidatedMessage]                          │   │
│  │  │   └─ Each: {role: "user"|"assistant", content: str}       │   │
│  │  ├─ state: ConversationState (GREETING→COMPLETED)           │   │
│  │  ├─ user_data: Dict[key → value]                            │   │
│  │  │   ├─ first_name, last_name, full_name                    │   │
│  │  │   ├─ phone, email                                         │   │
│  │  │   ├─ vehicle_brand, vehicle_model, vehicle_plate         │   │
│  │  │   ├─ appointment_date                                     │   │
│  │  │   └─ service_type                                         │   │
│  │  └─ state_transitions: List[ValidatedStateTransition]       │   │
│  │      └─ Each: {from_state, to_state, timestamp, reason}     │   │
│  │                                                                 │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Per-Conversation Booking Data (ScratchpadCoordinator)                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ scratchpads: Dict[conv_id → BookingScratchpad]               │   │
│  │                                                                 │   │
│  │ BookingScratchpad:                                             │   │
│  │  ├─ conversation_id: str                                       │   │
│  │  ├─ fields: Dict[field_name → "filled"|"empty"]             │   │
│  │  ├─ completeness_score: 0-100 (% form filled)              │   │
│  │  ├─ last_updated: datetime                                    │   │
│  │  └─ get_completeness() → float                               │   │
│  │                                                                 │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Configuration (Config in config.py)                                   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ # Behavioral Knobs                                             │   │
│  │ RETROACTIVE_SCAN_LIMIT = 2           # Last N messages to scan│   │
│  │ MAX_CHAT_HISTORY = 25                # Keep last 25 messages  │   │
│  │ SENTIMENT_CHECK_INTERVAL = 2         # Check every N turns   │   │
│  │                                                                 │   │
│  │ GREETING_STOPWORDS = {...}           # Reject greetings      │   │
│  │ SENTIMENT_THRESHOLDS = {...}         # Anger > 6.0 → help   │   │
│  │                                                                 │   │
│  │ SERVICES = {"wash": "...", ...}      # Service descriptions  │   │
│  │ VEHICLE_TYPES = [...]                # Hatchback, Sedan, ... │   │
│  │                                                                 │   │
│  │ # LLM Configuration                                           │   │
│  │ OLLAMA_BASE_URL = "http://localhost:11434"                  │   │
│  │ MODEL_NAME = "qwen3:8b"                                       │   │
│  │ TEMPERATURE = 0.3                    # Lower = more consistent│   │
│  │                                                                 │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. DSPy Module Architecture

```bash
┌─────────────────────────────────────────────────────────────────────┐
│                      DSPy MODULES LAYER                             │
│                 (In-Process LLM Chain Orchestration)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DSPy Configuration (dspy_config.py)                                │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ • Configure Ollama as LM backend                               ││
│  │ • Set MODEL_NAME = "qwen3:8b" (8B param, CPU-friendly)        ││
│  │ • Cache DSPy modules for performance                          ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  Core Extraction Modules (modules.py - DSPy ChainOfThought)        │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │  NameExtractor                                                  ││
│  │  ├─ Input: conversation_history, user_message                 ││
│  │  ├─ Output: {first_name, last_name}                          ││
│  │  └─ Uses: Chain-of-Thought reasoning                          ││
│  │                                                                 ││
│  │  VehicleDetailsExtractor                                        ││
│  │  ├─ Input: conversation_history, user_message                 ││
│  │  ├─ Output: {brand, model, number_plate}                      ││
│  │  └─ Uses: Brand/model matching, plate extraction             ││
│  │                                                                 ││
│  │  PhoneExtractor                                                 ││
│  │  ├─ Input: conversation_history, user_message                 ││
│  │  ├─ Output: {phone_number}                                     ││
│  │  └─ Uses: Indian phone format (10 digits)                    ││
│  │                                                                 ││
│  │  DateParser                                                     ││
│  │  ├─ Input: conversation_history, user_message                 ││
│  │  ├─ Output: {date_str} (e.g., "2024-12-25")                 ││
│  │  └─ Uses: Relative & absolute date parsing                   ││
│  │                                                                 ││
│  │  SentimentAnalyzer                                              ││
│  │  ├─ Input: conversation_history, current_message              ││
│  │  ├─ Output: {interest_score, anger_score, ...}                ││
│  │  └─ Scale: 1-10 (LLM outputs, then clamped)                 ││
│  │                                                                 ││
│  │  IntentClassifier                                               ││
│  │  ├─ Input: conversation_history, current_message              ││
│  │  ├─ Output: {intent_class, reasoning}                         ││
│  │  └─ Classes: inquire, pricing, booking, complaint, etc       ││
│  │                                                                 ││
│  │  SentimentToneAnalyzer                                          ││
│  │  ├─ Input: sentiment scores (interest, anger, ...)            ││
│  │  ├─ Output: {tone_directive, max_sentences}                   ││
│  │  └─ Maps: sentiment → tone (helpful, brief, engaging, etc)   ││
│  │                                                                 ││
│  │  ToneAwareResponseGenerator                                     ││
│  │  ├─ Input: history, msg, tone_directive, max_sentences        ││
│  │  ├─ Output: {response} (1-3 sentences, tone-aware)           ││
│  │  └─ Uses: Constrained generation                              ││
│  │                                                                 ││
│  │  TypoDetector                                                   ││
│  │  ├─ Input: field_name, value, history                         ││
│  │  ├─ Output: {has_typo, correction}                            ││
│  │  └─ Used: CONFIRMATION state only                             ││
│  │                                                                 ││
│  │  VehicleBrandEnum (80+ vehicles)                               ││
│  │  ├─ TOYOTA, HONDA, MAHINDRA, MARUTI, TATA, ...              ││
│  │  └─ Used for validation (prevent vehicle→name confusion)     ││
│  │                                                                 ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  DSPy Input/Output Format (dspy.History)                            │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ dspy.History(                                                   ││
│  │   messages=[                                                    ││
│  │     {role: "user", content: "I have Honda City"},             ││
│  │     {role: "assistant", content: "Thanks! Date?"},            ││
│  │     {role: "user", content: "25th"},                          ││
│  │   ]                                                             ││
│  │ )                                                               ││
│  │                                                                 ││
│  │ NOTE: For extraction, history is filtered to USER-ONLY        ││
│  │       to prevent LLM confusion from chatbot responses         ││
│  │                                                                 ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  LLM Backend (Ollama)                                              │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                                                                 ││
│  │  Local: http://localhost:11434                                ││
│  │  Model: qwen3:8b (8B parameters, CPU-capable)                ││
│  │  Temp: 0.3 (lower = more consistent, less creative)          ││
│  │                                                                 ││
│  │  Process:                                                       ││
│  │  1. Client sends request to MessageProcessor                  ││
│  │  2. Coordinator calls DSPy module (e.g., NameExtractor)       ││
│  │  3. DSPy calls LM backend (Ollama)                            ││
│  │  4. Ollama runs inference on local model                      ││
│  │  5. Result returned as dspy.Prediction object                 ││
│  │  6. Coordinator extracts fields (first_name, last_name)       ││
│  │  7. Validates & returns to flow                               ││
│  │                                                                 ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. State Machine Transitions

```bash
┌─────────────┐
│  GREETING   │◄─────── START HERE
└─────┬───────┘
      │
      │ Name extraction OR "service" keyword
      │
      ▼
┌──────────────────┐       ┌─────────────────────┐
│ NAME_COLLECTION  │       │ SERVICE_SELECTION   │
└────────┬─────────┘       │ (for pricing, etc)  │
         │                 └─────────────────────┘
         │ Phone/Vehicle                │
         │ extraction                   │ Data extraction
         │                              │
         ▼                              ▼
┌──────────────────────────────────────────────┐
│      VEHICLE_DETAILS                         │
│  Collect: brand, model, plate                │
└─────────────────────────────┬────────────────┘
                              │ Vehicle found OR date extraction
                              │
                              ▼
                      ┌──────────────────┐
                      │ DATE_SELECTION   │
                      │ Collect date     │
                      └────────┬─────────┘
                               │ Date found
                               │
                               ▼
                      ┌──────────────────────────┐
                      │ CONFIRMATION             │
                      │ Show booking summary     │
                      │ Wait for user confirm    │
                      └────────┬─────────────────┘
                               │ User says "yes", "confirm", etc
                               │
                               ▼
                      ┌──────────────────┐
                      │ COMPLETED        │
                      │ Booking done     │
                      └──────────────────┘

Special Cases:
──────────────
• SENTIMENT (anger > 6.0) → SERVICE_SELECTION (offer help)
• Can escape SERVICE_SELECTION via data extraction
• TIER_SELECTION, VEHICLE_TYPE, SLOT_SELECTION, ADDRESS_COLLECTION
  (defined but not yet active in Phase 2)
```

---

## 7. Response Decision Matrix

```bash
╔══════════════════════════════════════════════════════════════════╗
║                    RESPONSE MODE DECISION                        ║
╚══════════════════════════════════════════════════════════════════╝

Input: {user_message, intent, sentiment_scores, current_state}
Output: ResponseMode (LLM_ONLY | TEMPLATE_ONLY | HYBRID)

Decision Logic:
───────────────

┌─ PRIORITY 1: INTENT (OVERRIDES SENTIMENT)
│  ├─ Pricing inquiry → TEMPLATE_ONLY (show services + prices)
│  ├─ Booking inquiry → TEMPLATE_ONLY (booking info)
│  ├─ Complaint → LLM_ONLY (empathetic response)
│  └─ General inquire → HYBRID (response + gentle CTA)
│
├─ PRIORITY 2: SENTIMENT (if intent = general)
│  ├─ High interest (> 5.0) → HYBRID (engage + offer)
│  ├─ High anger (> 6.0) → LLM_ONLY (empathetic, no sales)
│  ├─ High disgust (> 3.0) → LLM_ONLY (address concern)
│  ├─ High boredom (> 5.0) → HYBRID (re-engage)
│  └─ Neutral → HYBRID (standard response + CTA)
│
├─ PRIORITY 3: CONVERSATION STATE
│  ├─ GREETING → HYBRID (welcome + ask name)
│  ├─ NAME_COLLECTION → HYBRID (confirm name + ask vehicle)
│  ├─ VEHICLE_DETAILS → HYBRID (confirm vehicle + ask date)
│  ├─ DATE_SELECTION → TEMPLATE_ONLY (show availability)
│  └─ CONFIRMATION → TEMPLATE_ONLY (booking summary)
│
└─ DEFAULT: HYBRID (balanced approach)

Example Responses:
──────────────────

1. Pricing Inquiry
   ─────────────────
   Intent: "pricing"
   Mode: TEMPLATE_ONLY
   Response: [Service menu with prices]

2. Complaint (angry)
   ──────────────────
   Intent: "complaint"
   Sentiment: anger = 8.0
   Mode: LLM_ONLY
   Response: "I'm really sorry to hear that. Let me help you..."
             [No template, no sales pitch]

3. General Interest (bored)
   ────────────────────────
   Intent: "inquire"
   Sentiment: boredom = 7.0
   Mode: HYBRID
   Response: "Let me tell you about our premium services..."
             [LLM response] + [Service template]

4. Greeting
   ─────────
   Intent: "general"
   Sentiment: interest = 6.0
   Mode: HYBRID
   Response: "Hi! Welcome to Yawlit..."
             [Empathetic intro] + [What's your name?]
```

---

## 8. Validation Layers

```bash
┌─────────────────────────────────────────────────────────┐
│             VALIDATION PIPELINE                        │
│          (Multiple Safety Nets)                        │
└─────────────────────────────────────────────────────────┘

Layer 1: Extraction Validation (ExtractionCoordinator)
─────────────────────────────────────────────────────
├─ Vehicle Brand Rejection
│  └─ If first_name matches VehicleBrandEnum → reject
│
├─ Greeting Stopwords Rejection
│  └─ If first_name in {haan, hello, hi, ...} → reject
│
├─ Quote Stripping
│  └─ DSPy sometimes returns '""' → strip quotes before validation
│
├─ None/Unknown Filtering
│  └─ Reject if value = "none", "unknown", "n/a"
│
└─ Min/Max Length Checks
   └─ first_name: 1-50 chars, vehicle_brand: 1-50 chars


Layer 2: Pydantic Model Validation (models.py)
──────────────────────────────────────────────
├─ ValidatedName
│  ├─ first_name: pattern '^[A-Za-z][A-Za-z\'-]*([ .][A-Za-z][A-Za-z\'-]*)*$'
│  ├─ Prevents numbers, only allows letters, hyphens, apostrophes
│  └─ Model validator: name consistency checks
│
├─ ValidatedVehicleDetails
│  ├─ brand: min 1 char, max 50
│  ├─ model: optional, fallback to "Unknown"
│  └─ number_plate: Indian format (MH12AB1234)
│
├─ ValidatedDate
│  ├─ date_str: ISO format (2024-12-25)
│  └─ Parsed from various input formats
│
├─ ValidatedSentimentScores
│  ├─ Each score: 1-10 (clamped)
│  └─ Includes reasoning string
│
└─ ValidatedPhone
   ├─ phone_number: 10 digits (Indian format)
   └─ Plus sign allowed for international


Layer 3: Retroactive Validation (retroactive_validator.py)
───────────────────────────────────────────────────────────
├─ Missing Field Detection
│  └─ State requires {first_name, vehicle_brand, ...}?
│
├─ Retroactive Scanning
│  ├─ Scan last 2 messages only (RETROACTIVE_SCAN_LIMIT)
│  ├─ User-only history (filter out assistant messages)
│  └─ Extract missing prerequisite data
│
└─ Early Exit Optimization
   └─ Skip scan if field already extracted in current turn


Layer 4: Confirmation Validation (message_processor.py)
───────────────────────────────────────────────────────
└─ Requires ALL fields present:
   ├─ first_name ✓
   ├─ vehicle_brand ✓
   ├─ vehicle_model ✓
   ├─ vehicle_plate ✓
   └─ appointment_date ✓

   If all present → should_confirm = true
   Otherwise → stay in DATE_SELECTION


Layer 5: Typo Detection (TypoDetector DSPy module)
──────────────────────────────────────────────────
└─ Only in CONFIRMATION state
   ├─ Check each field: name, vehicle, date, phone
   ├─ Suggest corrections if typos found
   └─ User can edit before final booking
```

---

## 9. Performance Characteristics

```bash
┌──────────────────────────────────────────────────────┐
│            PERFORMANCE PROFILE                      │
│           (Local Ollama, CPU Mode)                  │
└──────────────────────────────────────────────────────┘

Latencies:
──────────

API Endpoint (/chat):
  Total Time: 10-30 seconds per message

  Breakdown:
  ├─ Conversation storage: ~50ms
  ├─ Sentiment analysis (DSPy call): ~3-5s
  ├─ Intent classification (DSPy call): ~2-4s
  ├─ Data extraction (DSPy calls):
  │  ├─ NameExtractor: ~2-3s
  │  ├─ VehicleExtractor: ~2-3s
  │  ├─ DateParser: ~1-2s
  │  └─ PhoneExtractor: ~1-2s
  ├─ Retroactive validation sweep: ~10-20s
  │  ├─ Limited to last 2 messages
  │  └─ Early exit if data found
  ├─ Response generation (DSPy): ~2-4s
  ├─ Response composition: ~100ms
  └─ State transition: ~50ms

Optimizations Applied:
───────────────────────

✓ Retroactive Scan Limit = 2 (down from 3)
  └─ Reduces scan time from 20-40s to 10-20s

✓ Skip Scan if Data Found
  └─ Early exit if current turn extracted field

✓ User-Only History Filtering
  └─ Prevents LLM confusion from chatbot responses
  └─ Smaller token count, faster inference

✓ Greeting Stopwords Filter
  └─ Prevents bad extractions earlier (fail-fast)

✓ DSPy Caching
  └─ Modules cached after first import

Memory Usage:
─────────────

Per Conversation:
  ├─ ValidatedConversationContext: ~5-10 KB
  │  └─ 25 messages @ ~200 bytes each
  ├─ BookingScratchpad: ~2 KB
  ├─ State history: ~1 KB
  └─ Total: ~10-15 KB per active conversation

System:
  ├─ DSPy modules (cached): ~50-100 MB
  ├─ Model weights (Ollama): ~8 GB (loaded at startup)
  └─ ConversationManager dict: grows with # conversations

Scalability:
─────────────

Current Design:
  ├─ In-memory conversation storage (no persistence)
  ├─ Single-threaded FastAPI (production: use workers)
  ├─ Local Ollama inference (CPU-bound)
  └─ No database backend

Bottleneck:
  └─ DSPy LLM inference (3-5s per call)

To Scale:
  ├─ Add conversation persistence (SQLite → PostgreSQL)
  ├─ Implement conversation cleanup (archive old)
  ├─ Use GPU-accelerated Ollama (faster inference)
  ├─ Cache extraction results (Redis)
  └─ Batch process multiple conversations
```

---

## 10. Error Handling & Fallbacks

```bash
┌──────────────────────────────────────────────────────┐
│         RESILIENCE ARCHITECTURE                      │
│      (Graceful Degradation & Fallbacks)              │
└──────────────────────────────────────────────────────┘

Tier 1: Component-Level Fallbacks
──────────────────────────────────

Sentiment Analysis Fails
├─ Catch: Exception in SentimentAnalysisService
└─ Fallback: Return neutral sentiment (interest=5.0, anger=1.0)

Name Extraction Fails
├─ Try: DSPy NameExtractor module
├─ Fallback 1: Simple regex "I am X" or "My name is X"
└─ Fallback 2: Return None (no name extracted this turn)

Vehicle Extraction Fails
├─ Try: DSPy VehicleDetailsExtractor module
├─ Fallback 1: Regex pattern matching (brand names, plate format)
└─ Fallback 2: Return None (missing data, retroactive scan may find it later)

Intent Classification Fails
├─ Try: DSPy IntentClassifier module
└─ Fallback: Default to "inquire" with confidence=0.0

Response Generation Fails
├─ Try: Tone-aware response generation
├─ Fallback 1: Generic empathetic response
│  └─ "I understand. How can I help?"
└─ Fallback 2: Return response_mode decision (may skip to template only)


Tier 2: Process-Level Fallbacks
────────────────────────────────

Retroactive Validation Fails
├─ Catches Exception in final_validation_sweep
├─ Logs error
└─ Continues with current extraction only (no retroactive data)

State Transition Fails
├─ Catches: Invalid state in StateCoordinator
└─ Action: Stay in current state (safe default)

Typo Detection Fails
├─ Catches: Exception in TypoDetector call
└─ Action: Proceed without suggestions (optional feature)

Response Composition Fails
├─ Catches: Exception in ResponseComposer
└─ Fallback: Return: {response: "...", error: message}


Tier 3: System-Level Fallbacks
───────────────────────────────

Conversation Manager Unavailable
├─ HTTP Status: 503 (Service Unavailable)
├─ Detail: "Orchestrator not available"
└─ Client: Should retry after delay

Orchestrator Startup Fails
├─ Lifespan catches exception
├─ Logs error with traceback
└─ App still starts (endpoints return 503)

DSPy Configuration Fails
├─ Caught in dspy_configurator.configure()
├─ Logs which LM backend failed
└─ Falls back to mock/dummy responses


Validation Errors
─────────────────

Pydantic ValidationError
├─ Caught in extraction pipeline
├─ Data rejected from Pydantic model
└─ Falls back to None (retry retroactively)

State Validation
├─ Invalid state enum value
└─ Fallback: Stay in current state

Field Type Mismatch
├─ Sentiment score is string instead of float
├─ Try: Convert via _parse_score() with fallback logic
└─ Fallback: Clamp to valid range (1-10)


Exception Propagation
─────────────────────

Level 1: Component
  └─ ExtractionCoordinator catches and logs

Level 2: Process
  └─ MessageProcessor catches and logs

Level 3: API
  └─ FastAPI endpoint catches and returns HTTP 500

Level 4: Client
  └─ Client should handle HTTP errors and retry


Recovery Strategies
────────────────────

Timeout (slow inference)
└─ Set Ollama timeout → Return None → Fallback

Out of Memory
└─ Reduce MAX_CHAT_HISTORY or clear old conversations

Model Loading Failure
└─ Log error → Skip LLM-based features → Use rule-based only

Network Error (Ollama unreachable)
└─ Retry with exponential backoff → After 3 retries, return error
```

---

## 11. Testing & Quality Assurance

```bash
┌──────────────────────────────────────────────────────┐
│          TESTING INFRASTRUCTURE                      │
│        (Conversation Simulation & E2E)               │
└──────────────────────────────────────────────────────┘

Test Framework: (tests/conversation_simulator_v2.py)
───────────────────────────────────────────────────

Simulated Conversations:
├─ Realistic Turn Sequences
│  ├─ Turn 1: Greeting + Name
│  ├─ Turn 2: Vehicle Details
│  ├─ Turn 3: Date Selection
│  ├─ Turn 4: Confirmation
│  └─ Turn 5: Completion
│
├─ Dynamic Message Generation
│  ├─ Random vehicle selection (50+ brands)
│  ├─ Random license plate generation (MH12AB1234 format)
│  ├─ 50/50 Combined vs Sequential delivery
│  ├─ Varying natural language phrasing
│  └─ Hindi/English mixing (realistic)
│
├─ State Transition Validation
│  ├─ Verify state flows GREETING → COMPLETED
│  ├─ Check state change reasons logged
│  └─ Ensure no state loops
│
└─ Data Extraction Verification
   ├─ Verify all fields extracted correctly
   ├─ Check validation passed
   └─ Ensure no false extractions

Example Scenario:
─────────────────

Turn 1: "Hi, I'm Divya Iyer"
  Expected State: GREETING → NAME_COLLECTION
  Check: first_name="Divya", last_name="Iyer"

Turn 2: "I have Honda City, plate MH12AB1234"
  Expected State: NAME_COLLECTION → VEHICLE_DETAILS
  Check: vehicle_brand="Honda", vehicle_model="City", vehicle_plate="MH12AB1234"

Turn 3: "December 25th"
  Expected State: VEHICLE_DETAILS → DATE_SELECTION
  Check: appointment_date="2024-12-25"

Turn 4: "Yes, confirm"
  Expected State: DATE_SELECTION → CONFIRMATION → COMPLETED
  Check: should_confirm=true, state="completed"
```

---

## 12. Key Architectural Decisions

```bash
┌──────────────────────────────────────────────────────┐
│        ARCHITECTURAL RATIONALE                     │
│     (Why These Design Choices?)                    │
└──────────────────────────────────────────────────────┘

1. Single Responsibility Principle (SRP)
─────────────────────────────────────────
   ❌ BEFORE: One MonolithicChatbot class (2000+ lines)
   ✓ AFTER: MessageProcessor delegates to:
            - ExtractionCoordinator (data extraction)
            - StateCoordinator (state transitions)
            - ScratchpadCoordinator (booking tracking)
            - SentimentAnalysisService (sentiment analysis)
            - ResponseComposer (response generation)
            - TemplateManager (template selection)

   Benefit: Each class has ONE reason to change
           Easy to test, extend, fix


2. DSPy Framework for LLM Integration
──────────────────────────────────────
   ❌ BEFORE: Direct LLM prompt crafting (brittle)
   ✓ AFTER: DSPy modules with Chain-of-Thought reasoning
            Composable, learnable, optimizable

   Why Qwen3:8B:
   ├─ 8B parameters = CPU-feasible (~8 GB memory)
   ├─ Indian-optimized (understands Hindi names, context)
   ├─ Quantized versions available (4-bit, 5-bit)
   └─ Good balance of speed vs quality


3. User-Only History Filtering
──────────────────────────────
   ❌ BEFORE: Pass full history (user + assistant) to extractors
             → LLM confused by chatbot's own words
             → Extracts "finished", "now" as user data

   ✓ AFTER: Filter to user messages only
            → Cleaner context
            → LLM focuses on user intent
            → Faster inference (fewer tokens)

   Exception: Response generation still uses full history
              → LLM needs to know what was said


4. Retroactive Validation Pattern
──────────────────────────────────
   Problem: User provides data out of order
            "I have Honda City" (turn 2) before "My name is X" (turn 3)

   Solution: Retroactive scans conversation history
             └─ Finds "My name is X" from earlier turns
             └─ Merges with current extraction
             └─ Advances state when prerequisites met

   Optimization: Scan limit = 2 (last 2 messages)
                 └─ 70% reduction in latency
                 └─ Most data appears within 2 recent turns


5. Stopwords & Brand Validation
────────────────────────────────
   Problem: "Haan, hello" extracted as first_name="Haan"
            "Mahindra Scorpio" extracted as first_name="Mahindra"

   Solution: Multi-layer validation
   ├─ Layer 1: Stopwords filter (haan, hello, hi, yes)
   ├─ Layer 2: Vehicle brand enum check (80+ vehicles)
   ├─ Layer 3: Pydantic pattern validation (letters only)
   └─ Layer 4: Retroactive validator re-checks everything

   Benefit: Prevents data corruption at extraction source


6. Confirmation Screen Pattern
──────────────────────────────
   ✓ Only shows when:
     ├─ State == CONFIRMATION (triggered by date extraction)
     └─ ALL required fields present
        {first_name, vehicle_brand, vehicle_model, vehicle_plate, appointment_date}

   Benefit: Never shows incomplete bookings
            User can review & edit before final submission


7. State Machine vs Conditional Routing
────────────────────────────────────────
   ❌ BEFORE: Complex if-else chains
   ✓ AFTER: Finite State Machine (11 states)
            Transitions defined clearly in StateCoordinator

   Benefits:
   ├─ State is explicit (users know where they are)
   ├─ Transitions are visible (easy to debug)
   ├─ Can visualize flow
   └─ Testable (given state → given data → expect next state)


8. Configuration Over Code
──────────────────────────
   ✓ Centralized Config Class:
   ├─ RETROACTIVE_SCAN_LIMIT = 2
   ├─ GREETING_STOPWORDS = {...}
   ├─ SENTIMENT_THRESHOLDS = {...}
   ├─ MAX_CHAT_HISTORY = 25
   └─ TEMPERATURE = 0.3

   Benefit: Change behavior without code changes
            A/B test different thresholds
            Different configs for different users/regions


9. In-Memory Storage (for now)
──────────────────────────────
   Current: Dict[conv_id → ValidatedConversationContext]

   Trade-off:
   ✓ Fast (no DB latency)
   ✓ Simple (no schema management)
   ✗ Not persistent (lost on restart)
   ✗ Single-process (can't distribute)

   Future: Migrate to SQLite → PostgreSQL
           Add conversation archival
           Implement cleanup jobs


10. Response Composition (LLM + Template)
─────────────────────────────────────────
    ❌ BEFORE: Either/or (LLM or template, not both)
    ✓ AFTER: Intelligent blending

    Modes:
    ├─ LLM_ONLY: Empathy-focused (complaints, etc)
    ├─ TEMPLATE_ONLY: Info-focused (pricing, dates, etc)
    └─ HYBRID: Both (engaging + informative)

    Decision: Intent > Sentiment > State > Default

    Benefit: Personal + Professional
             Conversational + Informative
```

---

## 13. Known Limitations & Future Work

```bash
┌──────────────────────────────────────────────────────┐
│          LIMITATIONS & ROADMAP                      │
│        (What's Not Yet Implemented)                │
└──────────────────────────────────────────────────────┘

Current Limitations:
───────────────────

1. No Persistence
   └─ Conversations lost on restart
   └─ No analytics/history
   └─ TODO: Add SQLite/PostgreSQL backend

2. Single-Process Architecture
   └─ Can't scale to multiple workers easily
   └─ Conversation affinity needed
   └─ TODO: Add Redis for distributed state

3. Unused States (4 states defined but not used)
   ├─ TIER_SELECTION
   ├─ VEHICLE_TYPE
   ├─ SLOT_SELECTION
   └─ ADDRESS_COLLECTION
   └─ TODO: Implement Phase 2 booking flow

4. No Rate Limiting
   └─ Can hammer /chat endpoint
   └─ TODO: Add per-user rate limits

5. No User Authentication
   └─ No user accounts
   └─ TODO: Add JWT/OAuth

6. Limited Error Messages
   └─ Generic fallbacks
   └─ TODO: More specific user-facing messages

7. No Conversation Cleanup
   └─ In-memory storage grows forever
   └─ TODO: Archive/delete old conversations

8. No A/B Testing Framework
   └─ Can't split users into different variants
   └─ TODO: Add experiment management


Phase 2 Roadmap (In Progress):
─────────────────────────────

✓ DONE: Retroactive validation with history scanning
✓ DONE: State machine state management
✓ DONE: Multi-dimensional sentiment analysis
✓ DONE: User-only history filtering for extractors
✓ DONE: Stopwords filter for greetings
✓ DONE: Vehicle brand validation
✓ DONE: Confirmation screen with ALL-fields validation
✓ DONE: Typo detection in confirmation

🔄 IN PROGRESS: Booking flow integration (booking_orchestrator_bridge.py)

📋 TODO - Phase 3:
   ├─ Implement remaining states (TIER, SLOT, ADDRESS)
   ├─ Add persistent storage (SQLite)
   ├─ Implement conversation cleanup
   ├─ Add analytics & reporting
   ├─ User authentication
   ├─ Rate limiting
   ├─ Monitoring & alerting
   ├─ A/B testing framework
   ├─ Multi-language support (Hindi)
   ├─ Conversation export
   └─ Admin dashboard


Technical Debt:
───────────────

1. Duplicate Code
   ├─ _is_vehicle_brand() in 2 files
   ├─ SentimentDimension enum in 2 files
   └─ ConversationState enum in 2 files
   └─ TODO: Consolidate to single source of truth

2. God Object (models.py)
   └─ 953 lines, contains too many concerns
   └─ TODO: Split into smaller, focused models

3. Unused Methods
   ├─ ~60 lines of dead code (deprecated features)
   ├─ Deprecated classes not cleaned up
   └─ TODO: Remove unused code

4. Circular Dependencies
   └─ Some modules require function-level imports
   └─ TODO: Refactor to break cycles

5. Inconsistent Logging
   ├─ Emoji in log messages (should be removed in prod)
   ├─ Different log levels in different files
   └─ TODO: Standardize logging format

6. Configuration Scattered
   ├─ Sentiment thresholds hardcoded in 4 places
   ├─ Service names hardcoded in templates
   └─ TODO: Centralize all configuration


Performance Roadmap:
────────────────────

Current: 10-30 seconds per turn (CPU inference)

Optimizations:
├─ GPU acceleration (NVIDIA GPU + CUDA)
│  └─ Expected: 2-5s per turn
│
├─ Model quantization (4-bit, 5-bit)
│  └─ Expected: 5-10s per turn, 50% memory reduction
│
├─ Batch inference (process multiple conversations)
│  └─ Expected: 30-50% latency reduction
│
├─ LLM caching (cache extraction for common inputs)
│  └─ Expected: 50-70% hit rate for repeated inputs
│
└─ Smaller models (3B, 7B variants)
   └─ Expected: 2-3s per turn, trade-off with quality
```

---

## Summary

This system is a **sophisticated multi-layer conversational AI** built on:

- **FastAPI** for HTTP endpoints
- **DSPy** for composable LLM reasoning chains
- **Pydantic** for data validation
- **Local Ollama** for CPU-friendly inference
- **State Machine** for explicit conversation flow
- **Coordinator Pattern** for clean separation of concerns
- **Multi-validation layers** for data quality

The architecture prioritizes:

1. **Clarity** - Each component has one job
2. **Resilience** - Graceful fallbacks at every level
3. **Performance** - Optimizations for latency
4. **Extensibility** - Easy to add new states/validators
5. **Testability** - Simulated conversations validate behavior

The system is **production-ready for Phase 2** with known limitations documented and roadmap for Phase 3 defined.
