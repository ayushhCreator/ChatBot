# DETAILED DATA FLOW ARCHITECTURE ANALYSIS

## 1. STATE MACHINE: THE 11 CONVERSATION STATES

From `/home/riju279/Downloads/demo/example/config.py`:

```python
class ConversationState(str, Enum):
    GREETING = "greeting"                    # State 1: Initial greeting
    NAME_COLLECTION = "name_collection"      # State 2: Collect customer name
    SERVICE_SELECTION = "service_selection"  # State 3: Show services/pricing
    TIER_SELECTION = "tier_selection"        # State 4: Service tier options
    VEHICLE_TYPE = "vehicle_type"            # State 5: Vehicle type selection
    VEHICLE_DETAILS = "vehicle_details"      # State 6: Vehicle brand/model/plate
    DATE_SELECTION = "date_selection"        # State 7: Appointment date
    SLOT_SELECTION = "slot_selection"        # State 8: Time slot selection
    ADDRESS_COLLECTION = "address_collection" # State 9: Service address
    CONFIRMATION = "confirmation"             # State 10: Confirm all details
    COMPLETED = "completed"                   # State 11: Booking complete
```

## 2. COMPLETE DATA FLOW: USER INPUT → OUTPUT

### PHASE: Message Entry & Storage
```
User Input (FastAPI: /chat endpoint)
    ↓
main.py: ChatRequest.user_message
    ↓
MessageProcessor.process_message(conversation_id, user_message)
    ↓
ConversationManager.add_user_message(conversation_id, content)
    └─→ ValidatedConversationContext.messages.append({role: "user", content})
    └─→ Returns: ValidatedConversationContext with updated messages
```

**Key File**: `/home/riju279/Downloads/demo/example/conversation_manager.py`
- Lines 29-33: `add_user_message()` stores raw user input
- Line 82: `get_dspy_history()` converts messages to DSPy.History format

---

### PHASE: Intent & Sentiment Analysis
```
MessageProcessor.process_message() [Line 88]
    ├─ ExtractionCoordinator.classify_intent(history, user_message)
    │   ├─ Call: modules.IntentClassifier()
    │   ├─ Returns: ValidatedIntent
    │   │   ├── intent_class: str (e.g., "book", "inquire", "complaint")
    │   │   ├── confidence: float (0.0-1.0)
    │   │   └── metadata: ExtractionMetadata
    │   └─ Stored in: `intent` variable (Line 88)
    │
    └─ SentimentAnalysisService.analyze(history, user_message)
        ├─ Call: sentiment_analyzer modules
        ├─ Returns: ValidatedSentimentScores
        │   ├── interest: float (1-10)
        │   ├── anger: float (1-10)
        │   ├── disgust: float (1-10)
        │   ├── boredom: float (1-10)
        │   └── neutral: float
        └─ Stored in: `sentiment` variable (Line 91)
```

**Key Files**: 
- `/home/riju279/Downloads/demo/example/orchestrator/extraction_coordinator.py` (Lines 152-194)
- `/home/riju279/Downloads/demo/example/sentiment_analyzer.py`

---

### PHASE: Response Mode Decision
```
MessageProcessor [Line 109-117]
    ↓
TemplateManager.decide_response_mode(
    user_message,
    intent=intent.intent_class,          # "book" | "inquire" | "complaint" | etc.
    sentiment_interest,                   # Combined sentiment scores
    sentiment_anger,
    sentiment_disgust,
    sentiment_boredom,
    current_state=context.state.value
)
    ↓
Returns: (ResponseMode, template_key)
    ├─ ResponseMode.LLM_ONLY
    ├─ ResponseMode.TEMPLATE_ONLY
    ├─ ResponseMode.LLM_THEN_TEMPLATE
    └─ ResponseMode.TEMPLATE_THEN_LLM
    
Stored in: response_mode, template_key
```

**Key Logic**:
- Intent OVERRIDES sentiment (pricing inquiry always shows pricing template)
- Anger > 6.0 → LLM_ONLY (don't push templates)
- Disinterested → LLM_ONLY (engage, don't push)
- Complaint → LLM_ONLY (empathize first)

**Key File**: `/home/riju279/Downloads/demo/example/template_manager.py`

---

### PHASE: Data Extraction
```
MessageProcessor [Line 120-122]
    ↓
ExtractionCoordinator.extract_for_state(
    current_state,                        # ConversationState enum
    user_message,                         # Raw user input
    history                               # dspy.History
)
    ├─ Filters history to USER-ONLY messages (prevents LLM reading bot responses)
    │   └─ filter_dspy_history_to_user_only(history)
    │
    ├─ DataExtractionService.extract_name(user_message, user_only_history)
    │   ├─ Try: DSPy NameExtractor
    │   ├─ Strip quotes, validate
    │   ├─ Reject if: vehicle_brand OR greeting_stopword
    │   └─ Fallback: Regex pattern matching
    │
    ├─ DataExtractionService.extract_phone(...)
    │   ├─ Try: DSPy PhoneExtractor
    │   └─ Fallback: 10-digit Indian phone regex
    │
    ├─ DataExtractionService.extract_vehicle_details(...)
    │   ├─ Try: DSPy VehicleDetailsExtractor
    │   └─ Fallback: Regex for plate number + brand matching
    │
    └─ DataExtractionService.parse_date(...)
        ├─ Try: DSPy DateParser with current_date context
        └─ Fallback: Regex date pattern matching (YYYY-MM-DD, DD-MM-YYYY)

Returns: Dict[str, Any] or None
    {
        "first_name": str,
        "last_name": str,
        "full_name": str,
        "phone": str,
        "vehicle_brand": str,
        "vehicle_model": str,
        "vehicle_plate": str,
        "appointment_date": str
    }

Stored in: extracted_data variable
```

**Key Files**:
- `/home/riju279/Downloads/demo/example/orchestrator/extraction_coordinator.py` (Lines 59-150)
- `/home/riju279/Downloads/demo/example/data_extractor.py` (Lines 33-262)

**Critical Validations**:
- Sanitization: Strip quotes from DSPy output (fixes `""` empty string issue)
- Vehicle Brand Check: Reject if extracted name matches VehicleBrandEnum
- Greeting Stopwords: Reject "Haan", "Hello", "Hi", etc. as names (Config.GREETING_STOPWORDS)

---

### PHASE: LLM Response Generation (If Needed)
```
MessageProcessor [Line 126-129]
    ├─ Check: should_send_llm_response(response_mode)?
    │
    └─ IF YES → _generate_empathetic_response(...)
        ├─ Call: SentimentToneAnalyzer()
        │   └─ Analyzes sentiment scores → tone_directive + max_sentences
        │
        └─ Call: ToneAwareResponseGenerator()
            ├─ Input: tone_directive ("be sympathetic", "be helpful", etc.)
            ├─ Input: max_sentences (constraint based on sentiment)
            └─ Returns: Empathetic LLM response (str)

Stored in: llm_response variable
```

**Key Files**: 
- `/home/riju279/Downloads/demo/example/orchestrator/message_processor.py` (Lines 241-287)
- `/home/riju279/Downloads/demo/example/modules.py` (SentimentToneAnalyzer, ToneAwareResponseGenerator)

---

### PHASE: Retroactive Validation & Data Completion
```
MessageProcessor [Line 158-187]
    ↓
final_validation_sweep(
    current_state=context.state.value,
    extracted_data={...},               # May be empty or partial
    history=dspy.History
)
    ↓
ConversationValidator.validate_and_complete()
    ├─ Get missing fields for current state
    │   └─ DataRequirements.get_missing_fields(state, extracted_data)
    │       └─ Check REQUIREMENTS dict for state's mandatory fields
    │
    ├─ IF name missing → RetroactiveScanner.scan_for_name(history)
    │   └─ Search recent user messages for first_name mention
    │   └─ Use DSPy to extract retroactively
    │
    ├─ IF vehicle missing → RetroactiveScanner.scan_for_vehicle_details(history)
    │   └─ Search combined recent messages for brand/model/plate
    │
    └─ IF date missing → RetroactiveScanner.scan_for_date(history)
        └─ Search recent messages for date patterns

Returns: Updated extracted_data with filled gaps
Merged back into: extracted_data (Lines 167-185)
```

**Key Data Requirements**:
```python
REQUIREMENTS = {
    "greeting": [],
    "name_collection": ["first_name", "last_name", "full_name"],
    "service_selection": ["first_name"],
    "vehicle_details": ["first_name", "vehicle_brand", "vehicle_model", "vehicle_plate"],
    "date_selection": ["first_name", "vehicle_brand", "vehicle_model", "vehicle_plate", "appointment_date"],
    "confirmation": ["first_name", "vehicle_brand", "vehicle_model", "vehicle_plate", "appointment_date"],
    "completed": ["first_name", "vehicle_brand", "vehicle_model", "vehicle_plate", "appointment_date"]
}
```

**Key Files**: 
- `/home/riju279/Downloads/demo/example/retroactive_validator.py` (Lines 363-437)

---

### PHASE: Response Composition
```
MessageProcessor [Line 132-142]
    ↓
ResponseComposer.compose_response(
    user_message,
    llm_response,                       # May be empty
    intent=intent.intent_class,
    sentiment_interest/anger/disgust/boredom,
    current_state=context.state.value,
    template_variables={extracted_data}
)
    ├─ Call: TemplateManager.decide_response_mode() AGAIN
    │   └─ Confirms response mode (LLM, template, or both)
    │
    ├─ PART 1: Add LLM response if mode requires
    │   └─ IF should_send_llm_response(mode) → response_parts.append(llm_response)
    │
    ├─ PART 2: Add template if mode requires
    │   ├─ IF should_send_template(mode) → get_template(template_key)
    │   ├─ Render with variables
    │   └─ Add separator (──────) between LLM + template
    │
    └─ Combine all parts → final_response

Returns: Dict[str, Any]
    {
        "response": str (final composed message),
        "mode": str (ResponseMode.value),
        "has_llm_response": bool,
        "has_template": bool,
        "template_type": str,
        "requires_cta": bool
    }
```

**Key Files**: 
- `/home/riju279/Downloads/demo/example/response_composer.py` (Lines 45-116)

---

### PHASE: State Transition Decision
```
MessageProcessor [Line 190-197]
    ↓
StateCoordinator.determine_next_state(
    current_state=context.state,        # Current ConversationState
    sentiment,                          # ValidatedSentimentScores
    extracted_data,                     # Dict of extracted fields
    user_message                        # Raw input for keyword detection
)
    ├─ IF anger > 6.0 → ConversationState.SERVICE_SELECTION (offer help)
    │
    ├─ IF current_state == CONFIRMATION:
    │   └─ Check confirm_keywords ("yes", "confirm", "ok", "go", "book")
    │   └─ IF match → ConversationState.COMPLETED
    │
    ├─ IF extracted_data:
    │   ├─ Name extracted → GREETING/SERVICE → NAME_COLLECTION
    │   ├─ Phone extracted → NAME_COLLECTION → VEHICLE_DETAILS
    │   ├─ Vehicle extracted → NAME/SERVICE → VEHICLE_DETAILS
    │   │                      VEHICLE → DATE_SELECTION
    │   └─ Date extracted → VEHICLE/SERVICE → DATE_SELECTION
    │                       DATE → CONFIRMATION
    │
    └─ Service keywords ("service", "price", "offer") from GREETING → SERVICE_SELECTION

Returns: ConversationState (next_state)
```

**Key Logic in StateCoordinator** (`/home/riju279/Downloads/demo/example/orchestrator/state_coordinator.py`):
- Lines 44-45: Anger detection overrides normal flow
- Lines 48-51: Confirmation requires specific keywords
- Lines 54-87: Data extraction drives state progression
- Lines 89-94: Service inquiry keywords trigger SERVICE_SELECTION

---

### PHASE: Data Storage
```
MessageProcessor [Line 152-155]
    ↓
ConversationManager.store_user_data(conversation_id, key, value)
    └─ context.user_data[key] = value
    └─ Stored in: ValidatedConversationContext.user_data

MessageProcessor [Line 184-185]
    ↓
AFTER retroactive sweep, store updated data too:
    └─ store_user_data() for each retroactively filled field
```

---

### PHASE: Typo Detection (Confirmation State Only)
```
MessageProcessor [Line 147-150]
    ├─ Check: IF current_state == ConversationState.CONFIRMATION AND extracted_data
    │
    └─ ExtractionCoordinator.detect_typos_in_confirmation(
        extracted_data,
        user_message,
        history
    )
        ├─ Call: modules.TypoDetector() for each field
        ├─ Returns: Dict[field_name → correction]
        └─ Stored in: typo_corrections variable
```

---

### PHASE: Scratchpad Update
```
MessageProcessor [Line 200-206]
    ↓
ScratchpadCoordinator.get_or_create(conversation_id)
    ├─ Create or retrieve scratchpad for conversation
    │
    └─ For each extracted_data key/value:
        └─ ScratchpadCoordinator.update_from_extraction(
            scratchpad,
            next_state,                 # Use NEXT state, not current
            key,
            value
        )
```

---

### PHASE: Confirmation Decision
```
MessageProcessor [Line 218-221]
    ├─ Get CONFIRMATION state requirements
    │   └─ required_fields = {first_name, vehicle_brand, vehicle_model, vehicle_plate, appointment_date}
    │
    ├─ Extract current extracted_fields = set(extracted_data.keys())
    │
    └─ should_confirm = (
        next_state == ConversationState.CONFIRMATION AND
        required_fields.issubset(extracted_fields)  # ALL required present
    )
```

**CRITICAL**: Confirmation only triggers when:
1. State transitioned to CONFIRMATION
2. ALL required fields are present (from current turn + retroactive scans)

---

### PHASE: Response Construction
```
MessageProcessor [Line 226-239]
    ↓
ValidatedChatbotResponse(
    message=response["response"],
    should_proceed=True,
    extracted_data=extracted_data,
    sentiment=sentiment.to_dict(),
    should_confirm=should_confirm,    # Triggers confirmation screen
    scratchpad_completeness=float,
    state=next_state.value,           # NEW state after transition
    data_extracted=bool,              # True if extracted_data is not empty
    typo_corrections=dict
)
    ↓
Return to FastAPI /chat endpoint → ChatResponse model
```

---

## 3. STATE TRANSITIONS: THE COMPLETE STATE MACHINE

### State Transition Matrix

```
Current State          Input Condition                    Next State
────────────────────────────────────────────────────────────────────
GREETING               - User says "hello"                GREETING (stay)
                       - Asks about services              SERVICE_SELECTION
                       - Provides name                    NAME_COLLECTION
                       - Angry (anger > 6.0)              SERVICE_SELECTION

NAME_COLLECTION        - Phone extracted                  VEHICLE_DETAILS
                       - Vehicle extracted                VEHICLE_DETAILS
                       - Any data extracted               VEHICLE_DETAILS (default)
                       - Angry                            SERVICE_SELECTION

SERVICE_SELECTION      - Provides vehicle info            VEHICLE_DETAILS
                       - Provides name                    NAME_COLLECTION
                       - Any data extracted               Varies by data type

VEHICLE_DETAILS        - Vehicle brand/model extracted    DATE_SELECTION
                       - Additional vehicle data          DATE_SELECTION (stays)
                       - Any other extraction             VEHICLE_DETAILS (stay)

DATE_SELECTION         - Date extracted                   CONFIRMATION
                       - More data extracted              CONFIRMATION (default)

CONFIRMATION           - "yes"/"confirm"/"ok"/"go"/"book" COMPLETED
                       - "edit"/"change"/"fix"            CONFIRMATION (stays - re-show form)
                       - "cancel"/"no"/"stop"             CANCELLED (reset)

COMPLETED              ─ (Final state, booking done)      COMPLETED

CANCELLED              ─ (Final state, user cancelled)    CANCELLED
```

**Key Rule**: Data extraction drives state forward. Sentiment (anger) can override to SERVICE_SELECTION.

---

## 4. CRITICAL DATA FLOW ARCHITECTURE

### Data Mutation Points (Where Data Changes)

1. **Extraction Point** (Lines 120-122 of message_processor.py)
   - DSPy modules create ValidatedName, ValidatedVehicleDetails, etc.
   - Sanitization: Strip quotes, validate brands, reject stopwords
   - Returns: Dict[str, Any] with extracted fields

2. **Retroactive Completion** (Lines 158-187)
   - Fills gaps from conversation history
   - Can overwrite "Unknown" with real values
   - OVERWRITES initial extracted_data if retroactive found better values

3. **Confirmation Storage** (Lines 152-155)
   - Stores in ConversationContext.user_data
   - Acts as persistent storage for conversation

4. **Scratchpad Update** (Lines 200-206)
   - Updates booking scratchpad with extracted data
   - Used for confirmation summary display
   - Separate from conversation context

### Data Flow Critical Points

```
User Input
    ↓
ConversationManager.add_user_message()  ← Message stored
    ↓
ExtractionCoordinator.extract_for_state()  ← Data extracted
    ↓
final_validation_sweep()  ← Data completed/improved
    ↓
ConversationManager.store_user_data()  ← Data persisted
    ↓
ScratchpadCoordinator.update_from_extraction()  ← Booking form updated
    ↓
ResponseComposer.compose_response()  ← Response rendered
    ↓
StateCoordinator.determine_next_state()  ← State transitioned
    ↓
ConversationManager.update_state()  ← State persisted
    ↓
ValidatedChatbotResponse returned to FastAPI
```

---

## 5. BOOKING COMPLETION ARCHITECTURE

### Current Integration (Lines 239-276 of main.py)

```
/api/confirmation endpoint
    ├─ Parse JSON: conversation_id, user_input, action
    │
    └─ BookingOrchestrationBridge.initialize_booking(conversation_id)
        └─ BookingFlowManager(conversation_id)
            ├─ ScratchpadManager
            ├─ BookingStateMachine
            └─ ConfirmationHandler
    
    └─ BookingOrchestrationBridge.process_booking_turn(user_input, extracted_data, intent)
        └─ BookingFlowManager.process_for_booking()
            ├─ Add extracted_data to scratchpad
            ├─ Check: should_trigger_confirmation(user_message, intent, state)
            ├─ IF yes → Show summary → CONFIRMATION state
            ├─ IF in CONFIRMATION state:
            │   ├─ Detect action (CONFIRM/EDIT/CANCEL)
            │   ├─ IF CONFIRM → ServiceRequestBuilder.build() → COMPLETION
            │   ├─ IF EDIT → Update scratchpad → re-show form
            │   └─ IF CANCEL → Clear scratchpad → CANCELLED
            └─ Return: (response_message, ServiceRequest if confirmed)
```

**Critical Issue**: 
- Booking flow is SEPARATE from main orchestrator
- No direct integration of confirmation state back to MessageProcessor
- Confirmation triggers from `should_confirm` flag in ValidatedChatbotResponse
- BUT booking completion is handled separately in `/api/confirmation` endpoint

---

## 6. RESPONSE DECISION LOGIC MATRIX

### Template Manager: Response Mode Selection

```
Intent         Sentiment          Response Mode              Template Type
────────────────────────────────────────────────────────────────────
"book"         -                  TEMPLATE_ONLY             "booking"
"pricing"      -                  TEMPLATE_ONLY             "plans"
"inquire"      interest > 5.0     TEMPLATE_THEN_LLM         "catalog"
               interest ≤ 5.0     LLM_ONLY                  None
"complaint"    anger > 8.0        LLM_ONLY                  None
               anger ≤ 8.0        LLM_THEN_TEMPLATE         "help"
"cancel"       -                  LLM_THEN_TEMPLATE         "cancel_process"
"small_talk"   -                  LLM_ONLY                  None
-              anger > 6.0        LLM_ONLY                  None (offer service_selection)
-              disgust > 8.0      LLM_ONLY                  None
-              boredom > 9.0      LLM_ONLY                  None
```

**Intent Priority**: Intent OVERRIDES all sentiment considerations

---

## SUMMARY: 11-STATE STATE MACHINE WITH DATA FLOW

```
[GREETING] --name extracted--> [NAME_COLLECTION] --phone extracted--> [VEHICLE_DETAILS]
    |                                  |
    +---service inquiry-------> [SERVICE_SELECTION]
    |
    +---angry (anger>6)---------> [SERVICE_SELECTION]

[VEHICLE_DETAILS] --vehicle extracted--> [DATE_SELECTION] --date extracted--> [CONFIRMATION]
    |                                         |
    +-------vehicle complete-------> [DATE_SELECTION]

[CONFIRMATION] --confirm keywords--> [COMPLETED]
         |
         +--edit keywords----> [CONFIRMATION] (stay, show form again)
         |
         +--cancel keywords---> [CANCELLED]

[COMPLETED] = Final state (booking created via ServiceRequestBuilder)
[CANCELLED] = Final state (booking discarded)
```

### Data Requirements by State
```
GREETING:       No requirements
NAME_COLLECTION: Must have first_name, last_name, full_name
SERVICE_SELECTION: Must have first_name
VEHICLE_DETAILS: Must have first_name, vehicle_brand, vehicle_model, vehicle_plate
DATE_SELECTION: Must have ^^ + appointment_date
CONFIRMATION: Must have ^^ (same as DATE_SELECTION)
COMPLETED: Must have ^^ (same requirements)
```

