# Phase 2 & Phase 3 Detailed TODO

**Status:** Ready to implement ✅
**Phase 2 Duration:** ~36-40 hours (4 subphases)
**Phase 3 Duration:** ~20-24 hours (code cleanup + modularization)

---

## EXECUTIVE SUMMARY

### Phase 2: Scratchpad/Confirmation Architecture (36-40 hours)
Transform raw data extraction into structured booking flow with user confirmation:

```
Turn 1: "Hi" → DetectIntent → Extract name/vehicle → Store in scratchpad
Turn 2: "I need service" → Extract service_type → Update scratchpad
Turn 3: "Can you do Monday?" → Extract date → Detect booking intent
Turn 4: TRIGGER → Show confirmation form (read-only summary of scratchpad)
Turn 5: User says "confirm" → Build ServiceRequest → Send to backend
```

### Phase 3: Code Cleanup (20-24 hours)
Enforce <150 line rule that was broken during rapid development:
- models.py: 916 lines → 400-500 lines (split model families)
- retroactive_validator.py: 357 lines → 200 lines
- chatbot_orchestrator.py: 332 lines → 250 lines
- Create `helpers/` package for shared utilities

**Why Phase 3 is important:** Refactoring during Phase 2 implementation would slow development. Better to build, test, then refactor.

---

## PHASE 2: SCRATCHPAD/CONFIRMATION ARCHITECTURE

### 2a. ScratchpadManager (NEW FILE)

**File:** `example/scratchpad.py`
**Target Size:** <150 lines
**Status:** Define → Code → Test

#### Purpose
Single source of truth for collecting extracted data across conversation. Each field tracked with:
- Value
- Source (direct_extraction, retroactive_extraction, user_input, inferred)
- Turn number
- Confidence score
- Extraction method (dspy, regex, keyword)
- Timestamp

#### Key Classes

```python
class FieldEntry(BaseModel):
    """Single scraped field with metadata."""
    value: Optional[Any] = None
    source: Optional[str] = None  # "direct_extraction", "retroactive_extraction", etc.
    turn: Optional[int] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    timestamp: Optional[datetime] = None

class ScratchpadForm(BaseModel):
    """Three-section scratchpad (customer, vehicle, appointment)."""
    customer: Dict[str, FieldEntry]  # first_name, last_name, phone, email
    vehicle: Dict[str, FieldEntry]   # brand, model, plate, color, year
    appointment: Dict[str, FieldEntry]  # date, service_type, time_slot
    metadata: Dict[str, Any]  # conversation_id, created_at, data_completeness

class ScratchpadManager:
    """CRUD + validation for scratchpad."""
    def add_field(section, field_name, value, source, turn, confidence, extraction_method) → bool
    def get_field(section, field_name) → Optional[FieldEntry]
    def get_all_fields() → Dict
    def update_field(section, field_name, new_value) → bool
    def _update_completeness() → None
    def export_json() → str
```

#### Test Cases (in test_scratchpad.py)
- ✅ Add field to customer section
- ✅ Update existing field
- ✅ Verify metadata tracking
- ✅ Check completeness calculation (3/13 = 23%, 8/13 = 62%, etc.)
- ✅ Export to JSON

---

### 2b. ConfirmationGenerator (NEW FILE)

**File:** `example/confirmation.py`
**Target Size:** <100 lines
**Status:** Define → Code → Test

#### Purpose
Convert scratchpad → human-readable confirmation message for user review.

Two formats:
1. **Simple** - User sees clean summary (what goes in chat)
2. **Detailed** - Dev/debug mode with sources & confidence

#### Key Methods

```python
class ConfirmationGenerator:
    @staticmethod
    def generate_summary(scratchpad: ScratchpadForm) → str
        """Clean, user-friendly summary for confirmation."""

        Output example:
        ```
        📋 BOOKING CONFIRMATION
        ════════════════════════════════════════

        👤 CUSTOMER DETAILS:
           Name: John Smith [Turn 1]
           Phone: 555-0123
           Email: john@example.com

        🚗 VEHICLE DETAILS:
           Vehicle: Honda Civic
           Plate: ABC-1234

        📅 APPOINTMENT:
           Date: Monday, Dec 11
           Service: Oil Change

        [Edit] [Confirm] [Cancel]
        ```

    @staticmethod
    def generate_with_sources(scratchpad: ScratchpadForm) → str
        """Debug version with source attribution."""

        Output example:
        ```
        CUSTOMER:
          • first_name: John (100%) [from DIRECT_EXTRACTION - Turn 1]
          • phone: 555-0123 (85%) [from RETROACTIVE_EXTRACTION - Turn 3]
        ```
```

#### Test Cases (in test_confirmation.py)
- ✅ Generate summary with all fields
- ✅ Generate summary with partial fields
- ✅ Generate with sources format
- ✅ Verify formatting (emoji, line breaks, etc.)

---

### 2c. BookingIntentDetector (NEW FILE)

**File:** `example/booking_detector.py`
**Target Size:** <80 lines
**Status:** Define → Code → Test

#### Purpose
Detect when user is ready to confirm/book. Three trigger levels:

1. **Primary:** User says exact trigger word (confirm, book, schedule, proceed, etc.)
2. **Secondary:** Intent classified as "booking" (from Phase 1)
3. **Tertiary:** State machine is in "confirmation" stage

#### Key Logic

```python
CONFIRMATION_TRIGGERS = [
    "confirm", "book", "booking", "schedule", "appointment",
    "reserve", "let's book", "proceed", "checkout", "finalize"
]

def should_trigger_confirmation(user_message: str, intent: ValidatedIntent, state: str) → bool:
    # Check for trigger words
    # Check intent classification
    # Check state machine
    return trigger_detected or intent_is_booking or state_is_confirmation
```

#### Test Cases (in test_booking_detector.py)
- ✅ Trigger on "confirm"
- ✅ Trigger on "book it"
- ✅ Trigger on booking intent (even without trigger words)
- ✅ Trigger when state is "confirmation"
- ✅ No false positives on random messages

---

### 2d. ConfirmationHandler (NEW FILE)

**File:** `example/confirmation_handler.py`
**Target Size:** <120 lines
**Status:** Define → Code → Test

#### Purpose
Handle user actions at confirmation screen:
- **CONFIRM** → Proceed to booking
- **EDIT** → Modify specific field
- **CANCEL** → Abort booking

#### Key Classes

```python
class ConfirmationAction(str, Enum):
    CONFIRM = "confirm"
    EDIT = "edit"
    CANCEL = "cancel"

class ConfirmationHandler:
    def detect_action(user_input: str) → ConfirmationAction
        # "yes" / "correct" / "proceed" → CONFIRM
        # "edit name" / "change date" / "fix vehicle" → EDIT
        # "cancel" / "no" / "nevermind" → CANCEL

    def handle_confirm() → bool
        # Trigger ServiceRequestBuilder

    def handle_edit(field_spec: str, new_value: str) → bool
        # Find "customer.first_name" or similar
        # Update scratchpad
        # Return updated field

    def handle_cancel() → str
        # Clear scratchpad
        # Return friendly cancellation message
```

#### Test Cases (in test_confirmation_handler.py)
- ✅ Detect "confirm" action
- ✅ Detect "edit name to Jane" action
- ✅ Detect "cancel" action
- ✅ Handle ambiguous input (default to EDIT)
- ✅ Update field in scratchpad

---

### 2e. ServiceRequest & Builder (NEW FILE)

**File:** `example/service_request.py`
**Target Size:** <150 lines
**Status:** Define → Code → Test

#### Purpose
Transform confirmed scratchpad into ServiceRequest model ready for backend API/database.

#### Key Models

```python
class ServiceRequest(BaseModel):
    """Final booking record sent to backend."""
    service_request_id: str  # "SR-A1B2C3D4"
    conversation_id: str

    customer: Dict[str, Any]  # {first_name, last_name, phone, email}
    vehicle: Dict[str, Any]   # {brand, model, plate, year, color}
    appointment: Dict[str, Any]  # {date, service_type, time_slot}

    collection_sources: List[Dict]  # Audit trail

    created_at: datetime
    confirmed_at: datetime
    status: Literal["confirmed", "pending", "completed", "cancelled"]

class ServiceRequestBuilder:
    @staticmethod
    def build(scratchpad: ScratchpadForm, conversation_id: str) → ServiceRequest
        """Transform scratchpad (unstructured collection) → ServiceRequest (database record)."""
        # Extract customer/vehicle/appointment from scratchpad
        # Build collection_sources audit trail
        # Create ServiceRequest with metadata
        # Return ready for API POST
```

#### Test Cases (in test_service_request.py)
- ✅ Build ServiceRequest from full scratchpad
- ✅ Build with partial data
- ✅ Verify collection_sources tracking
- ✅ Verify ID generation
- ✅ Verify timestamps

---

### 2f. BookingStateMachine (NEW FILE)

**File:** `example/state_manager.py`
**Target Size:** <120 lines
**Status:** Define → Code → Test

#### Purpose
Track conversation state through booking flow:
```
greeting → data_collection → confirmation → booking → completion
```

Prevents invalid transitions (e.g., can't go straight to confirmation without data).

#### Key Classes

```python
class BookingState(str, Enum):
    GREETING = "greeting"
    DATA_COLLECTION = "data_collection"
    CONFIRMATION = "confirmation"
    BOOKING = "booking"
    COMPLETION = "completion"
    CANCELLED = "cancelled"

class BookingStateMachine:
    def __init__(self, initial_state=BookingState.GREETING)

    def can_transition(from_state, to_state) → bool
        """Validate state transitions."""
        # greeting → data_collection ✅
        # data_collection → confirmation ✅
        # confirmation → booking ✅
        # confirmation → data_collection ✅ (edit)
        # confirmation → cancelled ✅
        # Invalid: greeting → booking ❌

    def transition(new_state: BookingState) → bool
        """Move to new state if valid."""

    def get_current_state() → BookingState
```

#### Test Cases
- ✅ Valid transitions allowed
- ✅ Invalid transitions blocked
- ✅ State loop (confirm → edit → confirm) works

---

### 2g. Integrate into ChatbotOrchestrator

**File:** `chatbot_orchestrator.py` (UPDATE)
**Current Size:** 332 lines
**Target Size:** Keep <400 lines
**Status:** Add scratchpad orchestration

#### New Method: `_handle_booking_flow()`

```python
def _handle_booking_flow(self, user_message: str, intent: ValidatedIntent) → Tuple[str, bool]:
    """
    Orchestrate scratchpad → confirmation → booking flow.

    Returns: (response, should_show_confirmation)
    """

    # Step 1: Add extracted data to scratchpad
    if extracted_customer:
        scratchpad.add_field("customer", "first_name", extracted_customer["first_name"], ...)

    # Step 2: Check if booking intent detected
    if BookingIntentDetector.should_trigger_confirmation(user_message, intent, self.state):
        # Step 3: Show confirmation form
        confirmation_msg = ConfirmationGenerator.generate_summary(scratchpad)
        return confirmation_msg, should_show_confirmation=True

    # Step 4: Handle confirmation actions (confirm/edit/cancel)
    handler = ConfirmationHandler(scratchpad)
    action = handler.detect_action(user_message)

    if action == ConfirmationAction.CONFIRM:
        # Build service request + send to backend
        service_request = ServiceRequestBuilder.build(scratchpad, self.conversation_id)
        # TODO: POST to backend API
        return "Booking confirmed! Your reference: " + service_request.service_request_id, False

    elif action == ConfirmationAction.EDIT:
        # Update scratchpad + re-show form
        handler.handle_edit(field_spec, new_value)
        confirmation_msg = ConfirmationGenerator.generate_summary(scratchpad)
        return confirmation_msg, should_show_confirmation=True

    elif action == ConfirmationAction.CANCEL:
        # Clear scratchpad
        self.scratchpad = None
        self.state = BookingState.GREETING
        return handler.handle_cancel(), False
```

#### Integration Points

1. In `process_message()` - call `_handle_booking_flow()` if intent is booking-related
2. Add `self.scratchpad: Optional[ScratchpadManager]` instance variable
3. Add `self.booking_state: BookingStateMachine` instance variable
4. Update response routing to handle confirmation flow

---

### 2h. BookingFlowManager (NEW FILE)

**File:** `example/booking_flow_integration.py`
**Target Size:** <200 lines
**Status:** Define → Code → Test

#### Purpose
High-level coordinator for entire Phase 2 flow. Acts as facade hiding complexity from orchestrator.

```python
class BookingFlowManager:
    """Coordinates all Phase 2 components."""

    def __init__(self, conversation_id: str)

    def process_for_booking(user_message: str, intent: ValidatedIntent, extracted_data: Dict) → Dict:
        """
        Single method handles entire flow:
        - Add to scratchpad
        - Check confirmation trigger
        - Handle confirmation actions

        Returns: {
            "response": str,  # What to send to user
            "show_confirmation": bool,
            "action": ConfirmationAction | None,
            "booking_complete": bool,
            "service_request_id": str | None
        }
        """

    def get_scratchpad_summary() → str
        """Get current scratchpad state for debugging."""

    def get_collection_sources() → List[Dict]
        """Get audit trail."""
```

#### Benefits
- Orchestrator doesn't need to know about all 5 Phase 2 components
- Easy to test entire flow in one go
- Easy to mock in tests

---

### 2i. Add Confirmation Route to main.py

**File:** `main.py` (UPDATE)
**New Route:** `POST /api/confirmation`

```python
@app.post("/api/confirmation")
async def handle_confirmation(request: ConfirmationRequest):
    """
    User's action at confirmation screen.

    Request: {
        "conversation_id": "conv-123",
        "action": "confirm" | "edit" | "cancel",
        "field_spec": "customer.first_name",  # Only if action is "edit"
        "new_value": "Jane"  # Only if action is "edit"
    }

    Response: {
        "success": bool,
        "message": str,
        "service_request_id": str | None,  # Only if action is "confirm"
        "confirmation_form": str | None  # Only if action is "edit"
    }
    """

    conversation = get_conversation(request.conversation_id)
    booking_flow = BookingFlowManager(request.conversation_id)

    if request.action == "confirm":
        result = booking_flow.confirm_booking()
        return ServiceRequest(**result)

    elif request.action == "edit":
        result = booking_flow.edit_field(request.field_spec, request.new_value)
        return {"confirmation_form": result["confirmation_form"]}

    elif request.action == "cancel":
        result = booking_flow.cancel_booking()
        return {"message": result["message"]}
```

---

### 2j-l. Test Suite

#### test_scratchpad.py (<100 lines)
- Test CRUD operations
- Test metadata tracking
- Test completeness calculation
- Test JSON export

#### test_confirmation_flow.py (<150 lines)
- End-to-end: extract → scratchpad → confirmation → booking
- Test with full data, partial data
- Test edit flow
- Test cancel flow

#### test_service_request.py (<100 lines)
- Test ServiceRequest model validation
- Test builder from scratchpad
- Test audit trail generation
- Test ID generation

---

### 2m. Integration Testing

**Command:** `pytest tests/ -v`

Run against:
- Existing Phase 1 tests (should all still pass)
- New Phase 2 tests
- Integration test: Phase 1 detection → Phase 2 flow

---

### 2n. Update Documentation

Update `PHASE_1_ANALYSIS_AND_PHASE_2_INTEGRATION.md`:

```markdown
## PHASE 2: IMPLEMENTATION STATUS ✅

### 2a. ScratchpadManager ✅
- File: example/scratchpad.py (145 lines)
- Status: COMPLETE
- Tests: test_scratchpad.py PASSING

### 2b. ConfirmationGenerator ✅
- File: example/confirmation.py (98 lines)
- Status: COMPLETE
- Tests: test_confirmation.py PASSING

... (repeat for 2c-2h)

### Integration Test Results ✅
- E2E flow: greeting → data_collection → confirmation → booking
- All Phase 1 tests still passing
- No regressions
```

---

## PHASE 3: CODE CLEANUP (AFTER PHASE 2)

### Why Phase 3 Exists
During Phase 2 development, code size rules were relaxed to iterate faster:
- models.py: 916 lines (should be ~400-500)
- retroactive_validator.py: 357 lines (should be ~200)
- chatbot_orchestrator.py: 332 lines (after Phase 2, will be >400)

Phase 3 refactors without breaking functionality.

### 3a. Refactor models.py (916 → 400-500 lines)

**Current Problems:**
- Too many model definitions in one file
- Hard to navigate, find what you need
- Mixes domain models with validation models

**Solution: Split by responsibility**

```
example/models.py (split into):
├── models/domain.py          # Customer, Vehicle, Appointment
├── models/validation.py      # ValidatedIntent, ExtractionMetadata
├── models/responses.py       # ResponseMode, SentimentAnalysis
├── models/__init__.py        # Re-export all for convenience

example/models.py (100-150 lines):
    # Simple re-exports for backward compatibility
    from .domain import *
    from .validation import *
    from .responses import *
```

**Target Sizes:**
- models/domain.py: 200 lines
- models/validation.py: 150 lines
- models/responses.py: 80 lines
- models/__init__.py: 20 lines

**Test:** Existing tests still pass (imports unchanged)

---

### 3b. Refactor retroactive_validator.py (357 → 200 lines)

**Current Problems:**
- Extract logic mixed with validation
- Helper functions scattered throughout

**Solution: Extract helpers**

```
example/retroactive_validator.py (200 lines):
    from helpers.extractors import extract_vehicle_data, extract_customer_data
    from helpers.validators import validate_extraction_confidence

    class RetroactiveValidator:
        # Core logic only

helpers/extractors.py (120 lines):
    def extract_vehicle_data(history: List) → Dict: ...
    def extract_customer_data(history: List) → Dict: ...
    def extract_appointment_data(history: List) → Dict: ...

helpers/validators.py (80 lines):
    def validate_extraction_confidence(value, confidence) → bool: ...
    def validate_extraction_completeness(data) → float: ...
```

---

### 3c. Refactor chatbot_orchestrator.py (332 → 250-300 lines)

**After Phase 2, this will be >400 lines. Split:**

```
example/chatbot_orchestrator.py (250-300 lines):
    # Core orchestration logic only
    from booking_flow_integration import BookingFlowManager
    from helpers.response_helpers import format_response, handle_error

    class ChatbotOrchestrator:
        def process_message(user_message) → str:
            # Main flow

example/response_helpers.py (150 lines):
    def format_response(intent, sentiment, template) → str: ...
    def handle_error(error, context) → str: ...
    def sanitize_output(text) → str: ...
```

---

### 3d. Create helpers/ Package

```
example/helpers/
├── __init__.py           # Exports all helpers
├── validators.py         # Validation utilities
├── extractors.py         # Data extraction utilities
├── parsers.py            # Natural language parsing
└── response_helpers.py   # Response formatting
```

**Total new lines:** ~500 lines of helpers split across 4 files (125 lines each max)

---

### 3e. Update Imports Across Codebase

After splitting, update imports in:
- chatbot_orchestrator.py
- main.py
- tests/

Check: `grep -r "from models import" example/`
Update any broken imports.

---

### 3f. Run Full Test Suite

```bash
pytest tests/ -v --tb=short
pytest tests/ --cov=example --cov-report=term-missing
```

**Must Pass:**
- ✅ All Phase 1 tests
- ✅ All Phase 2 tests
- ✅ No import errors
- ✅ No regressions in behavior

---

## IMPLEMENTATION ORDER

### Phase 2 (Do in order - each depends on previous)

1. **2a: ScratchpadManager** - Foundation layer
   - No dependencies
   - Test with test_scratchpad.py

2. **2b: ConfirmationGenerator** - Depends on ScratchpadManager
   - Reads scratchpad structure
   - Test formatting independently

3. **2c: BookingIntentDetector** - Independent
   - Uses ValidatedIntent from Phase 1
   - Test triggering logic

4. **2d: ConfirmationHandler** - Depends on ScratchpadManager
   - Updates scratchpad
   - Test action detection & field updates

5. **2e: ServiceRequestBuilder** - Depends on ScratchpadManager
   - Reads confirmed scratchpad
   - Outputs for backend API

6. **2f: BookingStateMachine** - Independent
   - Test state transitions
   - Add to orchestrator later

7. **2g: ChatbotOrchestrator integration** - Depends on 2a-2f
   - Add _handle_booking_flow() method
   - Integrate state machine

8. **2h: BookingFlowManager** - Depends on 2a-2g
   - High-level orchestrator
   - Facade pattern

9. **2i: main.py routes** - Depends on 2h
   - Add /api/confirmation endpoint

10. **2j-l: Tests** - Parallel with implementation
    - Write tests alongside code
    - E2E test in 2k

11. **2m: Integration** - After all components done
    - Run full test suite
    - Check Phase 1 still works

12. **2n: Documentation** - Final step
    - Update status doc

---

### Phase 3 (After Phase 2 Complete)

1. **3a: Refactor models.py** - Don't break tests
   - Change from models.py import → from models.domain import
   - Ensure __init__.py re-exports everything

2. **3b: Refactor retroactive_validator.py**
   - Create helpers/extractors.py
   - Create helpers/validators.py
   - Update imports in retroactive_validator.py

3. **3c: Refactor chatbot_orchestrator.py**
   - Create response_helpers.py
   - Extract methods into helpers
   - Keep orchestrator focused

4. **3d: Create helpers/ package**
   - Organize all new helper files
   - Create __init__.py with exports

5. **3e: Update all imports**
   - Check all files for broken imports
   - Test

6. **3f: Final test suite**
   - Full regression test
   - Coverage report

---

## FILE STRUCTURE AFTER PHASE 2+3

```
example/
├── main.py                              (232 → 245 lines, +booking route)
├── chatbot_orchestrator.py              (332 → 280 lines, refactored Phase 3)
├── template_manager.py                  (145 lines, unchanged)
├── data_extractor.py                    (211 lines, unchanged)
├── retroactive_validator.py             (357 → 200 lines, refactored Phase 3)
├── pywa_integration.py                  (193 lines, unchanged)
├── response_composer.py                 (145 lines, unchanged)
├── template_strings.py                  (164 lines, unchanged)
├── signatures.py                        (194 lines, unchanged)
├── modules.py                           (166 lines, unchanged)
│
├── models/                              (NEW - Phase 3)
│   ├── __init__.py                      (20 lines)
│   ├── domain.py                        (200 lines)
│   ├── validation.py                    (150 lines)
│   └── responses.py                     (80 lines)
│
├── helpers/                             (NEW - Phase 3)
│   ├── __init__.py                      (30 lines)
│   ├── validators.py                    (80 lines)
│   ├── extractors.py                    (120 lines)
│   ├── parsers.py                       (100 lines)
│   └── response_helpers.py              (150 lines)
│
├── booking/                             (NEW - Phase 2)
│   ├── __init__.py                      (20 lines)
│   ├── scratchpad.py                    (145 lines)
│   ├── confirmation.py                  (98 lines)
│   ├── booking_detector.py              (75 lines)
│   ├── confirmation_handler.py          (115 lines)
│   ├── service_request.py               (140 lines)
│   ├── state_manager.py                 (115 lines)
│   └── booking_flow_integration.py      (180 lines)
│
├── tests/
│   ├── test_api.py
│   ├── test_intent_classifier.py
│   ├── test_template_manager_intent.py
│   ├── test_sentiment_signature.py
│   ├── test_validated_intent.py
│   ├── conversation_simulator.py
│   ├── test_example.py
│   ├── test_scratchpad.py               (NEW - Phase 2)
│   ├── test_confirmation_flow.py        (NEW - Phase 2)
│   └── test_service_request.py          (NEW - Phase 2)
│
├── docs/                                (Archive, exists already)
│   ├── FINAL_SUMMARY_FOR_USER.md
│   ├── PHASE_1_vs_PHASE_2_SUMMARY.md
│   ├── ... (7 files moved from root)
│
├── INTENT_AND_STAGES_PLAN.md           (unchanged, 19K)
├── PHASE_1_ANALYSIS_AND_PHASE_2_INTEGRATION.md (updated Phase 3, +200 lines)
└── PHASE_2_3_DETAILED_TODO.md          (THIS FILE, for tracking)
```

---

## METRICS & COMMITMENTS

### After Phase 2
- ✅ Phase 1 + Phase 2 features complete
- ✅ All tests passing
- ❌ Code organization still needs work (Phase 3)
- ✅ Booking flow end-to-end functional
- ✅ Data audit trail working

### After Phase 3
- ✅ All files <150 lines
- ✅ Clear separation of concerns
- ✅ Models organized by domain
- ✅ Helpers separated from core logic
- ✅ Imports clean and consistent
- ✅ Full test coverage maintained

---

## DANGER ZONES & SAFEGUARDS

### 3 Things That Will Break Everything

1. **Phase 2 without tests**
   - **Safeguard:** Write test for each component BEFORE integrating
   - **Check:** Run `pytest tests/ -v` after each 2a-2i

2. **Phase 3 refactoring breaks imports**
   - **Safeguard:** Always re-export from __init__.py
   - **Check:** Grep for broken imports: `grep -r "ImportError\|ModuleNotFoundError" tests/`

3. **Orphaned Phase 1 references**
   - **Safeguard:** After refactoring, trace all imports backward
   - **Check:** Run full test suite without selective test filtering

---

## SUCCESS CRITERIA

### Phase 2 Complete When:
- ✅ 8 new Python files created (<150 lines each)
- ✅ 3 new test files created (all green)
- ✅ E2E test passing: greeting → collection → confirmation → booking
- ✅ All Phase 1 tests still passing
- ✅ main.py has /api/confirmation route
- ✅ Documentation updated

**Expected Time: 36-40 hours**

### Phase 3 Complete When:
- ✅ All Python files <150 lines (except booking_flow_integration.py at 180, justified)
- ✅ models.py split into models/ package
- ✅ retroactive_validator.py uses helpers
- ✅ helpers/ package organized
- ✅ All imports updated
- ✅ Full test suite green
- ✅ Coverage >85%

**Expected Time: 20-24 hours**

---

## Next Steps

1. Review this document
2. Confirm Phase 2 go/no-go
3. Start with 2a: ScratchpadManager
4. After each component, run tests
5. After 2a-2i complete, run integration test
6. Document, then move to Phase 3

Questions? Uncertainties? Ask before starting.
