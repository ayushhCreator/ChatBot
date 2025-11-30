# Phase 2 Implementation: Priority Order & Decision Points

---

## BEFORE YOU START PHASE 2

### Prerequisite: Complete Phase 1 Gaps

**These MUST be done first** (blocking for Phase 2):

#### Task P1-A: Add ValidatedIntent Model to models.py
**Time:** 10 minutes
**Why First:** Phase 2 needs ValidatedIntent objects

```python
# ADD TO models.py after ValidatedVehicleDetails

class ValidatedIntent(BaseModel):
    """Classified user intent with reasoning and confidence."""
    intent_class: Literal[
        "pricing",
        "catalog",
        "booking",
        "general_inquiry",
        "complaint",
        "small_talk",
        "reschedule"
    ] = Field(..., description="Classified intent")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in classification")
    reasoning: str = Field(..., min_length=10, max_length=2000)
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
```

#### Task P1-B: Update IntentClassifier to Return ValidatedIntent
**Time:** 5 minutes
**Why First:** Phase 2 code depends on ValidatedIntent objects

```python
# IN modules.py - IntentClassifier.forward()

def forward(self, conversation_history=None, current_message: str = ""):
    from models import ValidatedIntent  # Add import

    result = self.predictor(
        conversation_history=conversation_history,
        current_message=current_message
    )

    return ValidatedIntent(
        intent_class=result.intent_class.lower().strip(),
        confidence=0.85,
        reasoning=result.reasoning,
        metadata=ExtractionMetadata(
            confidence=0.85,
            extraction_method="dspy",
            extraction_source=current_message,
            timestamp=datetime.now()
        )
    )
```

#### Task P1-C: Update template_manager.decide_response_mode Signature
**Time:** 3 minutes
**Why First:** Prevents type errors in Phase 2

```python
# IN template_manager.py - change line 45-46

def decide_response_mode(
    self,
    user_message: str,
    intent: ValidatedIntent,  # Changed from str
    sentiment_interest: float = 5.0,
    sentiment_anger: float = 1.0,
    sentiment_disgust: float = 1.0,
    sentiment_boredom: float = 1.0,
    current_state: str = "greeting"
) -> Tuple[ResponseMode, str]:
    """..."""
    intent_class = intent.intent_class  # Add this line
    # Then use intent_class in all comparisons below
```

#### Task P1-D: Verify All 5 Sentiment Dimensions Displayed
**Time:** 2 minutes
**Why First:** Phase 2 assumes this works

Check `conversation_simulator.py` around line ~147:
```python
# Should show all 5: Interest, Anger, Disgust, Boredom, Neutral
# If missing any, update the f-string
```

---

## DECISION CHECKPOINT: Should We Do Phase 2?

### Questions to Ask

1. **Data Governance:** Do you need audit trail of where each field came from?
   - YES → Continue Phase 2
   - NO → Stop here, Phase 1 is sufficient

2. **User Confirmation:** Do you want users to confirm data before booking?
   - YES → Continue Phase 2
   - NO → Skip Phase 2, auto-confirm when data ready

3. **Edit Capability:** Do users need to correct extracted data?
   - YES → Continue Phase 2
   - NO → Skip Phase 2, trust extractions

4. **Time Budget:** Do you have ~40 hours for Phase 2?
   - YES → Continue with full Phase 2
   - NO → Do Phase 2a only (data layer), skip confirmation UI

### Go/No-Go Decision
- **If YES to Questions 1-3 AND YES to Question 4:** → Full Phase 2 (40 hours)
- **If YES to 1-2, NO to 3, YES to 4:** → Phase 2a + 2c (25 hours, skip edit)
- **If YES to 1, NO to 2-3, ANY on 4:** → Phase 2a only (16 hours, no confirmation UI)
- **If NO to 1:** → STOP, Phase 1 is done

---

## Phase 2 Implementation Order

### Timeline: Sequential Completion

```
Week 1: Phase 2a - Infrastructure (16 hours)
├─ Day 1-2: ScratchpadManager (4h) + tests (2h)
├─ Day 3: ConfirmationGenerator (2h) + tests (2h)
├─ Day 4: ServiceRequestBuilder (2h) + tests (2h)
└─ Day 5: MockDatabaseService (2h) + tests (2h)

Week 2: Phase 2b - Detection (8 hours)
├─ Day 1: BookingIntentDetector (2h) + tests (2h)
├─ Day 2: ConfirmationHandler (2h) + tests (2h)
└─ Day 3: Integration tests (4h)

Week 3: Phase 2c - Orchestrator (12 hours)
├─ Day 1-2: Scratchpad init (2h) + scratchpad updates (3h)
├─ Day 3: Confirmation trigger (2h)
├─ Day 4: Confirmation flow handler (3h)
└─ Day 5: End-to-end test (2h)

Week 4: Phase 2d - Hardening (8 hours)
├─ Day 1-2: Bug prevention checks (4h)
├─ Day 3: Edge case testing (3h)
└─ Day 4: Performance & cleanup (1h)

Total: 44 hours (across 4 weeks at ~11h/week)
```

---

## Phase 2a: Infrastructure (First Priority)

### START HERE → scratchpad.py

**Why First:** Everything else depends on ScratchpadManager

**Deliverable:** Single file with 3 classes
1. FieldEntry - Single field metadata
2. ScratchpadForm - Entire form structure
3. ScratchpadManager - CRUD operations

**Tests Needed:**
```python
test_add_field_valid()           # Add field with all metadata
test_add_field_invalid_source()  # Reject unknown source
test_get_field()                 # Retrieve field entry
test_completeness_calculation()  # 85% when 17/20 fields filled
test_add_field_updates_timestamp() # Updates last_updated
```

**Success Criteria:**
- [ ] Can create ScratchpadManager for conversation
- [ ] Can add 10 fields with different sources
- [ ] Completeness calculates correctly
- [ ] All tests pass

---

### SECOND → confirmation.py

**Why:** Needed for displaying scratchpad to user

**Deliverable:** Two methods
1. generate_summary() - Human readable
2. generate_with_sources() - Debug version

**Tests Needed:**
```python
test_summary_shows_only_filled_fields()  # Hides None values
test_summary_includes_turn_numbers()     # Shows [from Turn 3]
test_summary_with_sources()              # Debug output
test_summary_formatting()                # Readable output
```

**Success Criteria:**
- [ ] Summary is readable, clear formatting
- [ ] Only non-null fields shown
- [ ] Turn numbers displayed correctly

---

### THIRD → service_request.py

**Why:** Needed to save confirmed bookings

**Deliverable:** Two classes
1. ServiceRequest - Backend format
2. ServiceRequestBuilder - Transform scratchpad → request

**Tests Needed:**
```python
test_build_extracts_customer_data()      # All customer fields
test_build_extracts_vehicle_data()       # All vehicle fields
test_build_creates_collection_sources()  # Audit trail
test_build_filters_null_values()         # No None in request
test_service_request_id_unique()         # SR-ABC123 format
```

**Success Criteria:**
- [ ] ServiceRequest has all required fields
- [ ] collection_sources contains all fields' metadata
- [ ] IDs are unique and formatted correctly

---

### FOURTH → mock_database.py

**Why:** Needed to persist bookings

**Deliverable:** One class
1. MockDatabaseService - In-memory storage

**Tests Needed:**
```python
test_save_service_request()               # Save and retrieve
test_get_nonexistent_request()            # Returns None
test_list_all_requests()                  # All saved requests
test_save_logs_properly()                 # Logging works
```

**Success Criteria:**
- [ ] Can save and retrieve service requests
- [ ] Lists all saved requests
- [ ] Logging shows confirmation with ID

---

## Phase 2b: Detection & Handling

### FIFTH → booking_detector.py

**Why:** Identifies when to show confirmation

**Deliverable:** One class
1. BookingIntentDetector - Detects booking trigger

**Tests Needed:**
```python
test_detects_confirm_keyword()    # "confirm"
test_detects_book_keyword()       # "book"
test_detects_schedule_keyword()   # "schedule"
test_detects_intent_booking()     # Intent == "booking"
test_ignores_random_text()        # "hi there" returns False
```

**Success Criteria:**
- [ ] Detects all confirmation keywords
- [ ] Detects booking intent
- [ ] Doesn't trigger on unrelated text

---

### SIXTH → confirmation_handler.py

**Why:** Handles user's choices at confirmation

**Deliverable:** Two classes
1. ConfirmationAction - Enum for actions
2. ConfirmationHandler - Process user input

**Tests Needed:**
```python
test_detect_confirm_action()      # "yes", "confirm"
test_detect_edit_action()         # "edit", "change"
test_detect_cancel_action()       # "no", "cancel"
test_handle_edit_field()          # Update field value
test_edit_updates_source()        # source becomes "user_input"
```

**Success Criteria:**
- [ ] Correctly detects action from user input
- [ ] Edits update field value and metadata
- [ ] Edits mark source as "user_input"

---

## Phase 2c: Orchestrator Integration

### SEVENTH → Update chatbot_orchestrator.py

**Why:** Connects everything together

**Changes Needed:**

1. **Add scratchpad storage**
```python
def __init__(self):
    # ... existing code ...
    self.scratchpads = {}  # conversation_id → ScratchpadManager
```

2. **Initialize scratchpad on first message**
```python
def process_message(self, conversation_id, user_message, current_state):
    if conversation_id not in self.scratchpads:
        self.scratchpads[conversation_id] = ScratchpadManager(conversation_id)
```

3. **Add extracted data to scratchpad**
```python
scratchpad_mgr = self.scratchpads[conversation_id]

# After direct extraction
if extracted_data.get("first_name"):
    scratchpad_mgr.add_field(
        section="customer",
        field_name="first_name",
        value=extracted_data["first_name"],
        source="direct_extraction",
        turn=self._get_current_turn(conversation_id),
        confidence=0.95,
        extraction_method="dspy"
    )

# Similar for vehicle, appointment...
```

4. **Add retroactive extracted data to scratchpad**
```python
# In retroactive_validator.py or after it's called
if retroactively_filled_data:
    for field_name, field_value in retroactively_filled_data.items():
        scratchpad_mgr.add_field(
            section=section,  # Infer from field_name
            field_name=field_name,
            value=field_value,
            source="retroactive_extraction",
            turn=current_turn,
            confidence=0.75,
            extraction_method="dspy"
        )
```

5. **Check for booking intent trigger**
```python
if BookingIntentDetector.should_trigger_confirmation(
    user_message, intent, current_state
):
    return self._handle_confirmation_flow(
        conversation_id,
        self.scratchpads[conversation_id],
        user_message
    )
```

6. **Add confirmation flow handler**
```python
def _handle_confirmation_flow(self, conversation_id, scratchpad_mgr, user_message):
    scratchpad = scratchpad_mgr.scratchpad

    # Generate confirmation
    confirmation_text = ConfirmationGenerator.generate_summary(scratchpad)

    # Handle user action
    handler = ConfirmationHandler(scratchpad)
    action = handler.detect_action(user_message)

    if action == ConfirmationAction.CONFIRM:
        # Save booking
        service_request = ServiceRequestBuilder.build(scratchpad, conversation_id)
        self.db_service.save_service_request(service_request)
        return {"status": "booked", "sr_id": service_request.service_request_id}

    elif action == ConfirmationAction.EDIT:
        return {"status": "awaiting_edit", "message": "Which field to edit?"}

    elif action == ConfirmationAction.CANCEL:
        return {"status": "cancelled", "message": "Booking cancelled"}
```

---

## Phase 2d: Hardening & Testing

### Bug Prevention Checklist Implementation

**Add to ScratchpadManager:**
```python
# In add_field() method:

# 1. Validate source
ALLOWED_SOURCES = ["direct_extraction", "retroactive_extraction", "user_input", "inferred"]
if source not in ALLOWED_SOURCES:
    raise ValueError(f"Invalid source {source}, must be one of {ALLOWED_SOURCES}")

# 2. Validate confidence
if not (0.0 <= confidence <= 1.0):
    raise ValueError(f"Confidence must be 0.0-1.0, got {confidence}")

# 3. Validate turn
if not isinstance(turn, int) or turn < 0:
    raise ValueError(f"Turn must be positive int, got {turn}")

# 4. Warn if confidence low
if confidence < 0.7:
    logger.warning(f"Low confidence ({confidence}) for {section}.{field_name}")
```

**Add to ConfirmationGenerator:**
```python
# In generate_summary():

# 1. Filter out None values
if field_entry.value is not None:  # Skip None values
    summary += f"   Name: {field_entry.value}\n"

# 2. Show confidence if low
if field_entry.confidence and field_entry.confidence < 0.8:
    summary += f"⚠️ Low confidence: {field_entry.confidence:.0%}\n"
```

**Add to ServiceRequestBuilder:**
```python
# In build():

# 1. Validate required fields
REQUIRED_CUSTOMER = ["first_name"]
REQUIRED_VEHICLE = ["brand", "model", "plate"]
REQUIRED_APPOINTMENT = ["date"]

for field in REQUIRED_CUSTOMER:
    if field not in customer_data or customer_data[field] is None:
        raise ValueError(f"Missing required field: customer.{field}")

# Similar for vehicle, appointment...

# 2. Check for duplicates (idempotency)
idempotency_key = hash((
    scratchpad.conversation_id,
    scratchpad.customer.get("first_name"),
    scratchpad.vehicle.get("plate")
))
if self.seen_keys.get(idempotency_key):
    logger.warning(f"Duplicate booking detected: {idempotency_key}")
    return self.existing_requests[idempotency_key]  # Return existing
```

---

## Testing Strategy

### Unit Tests (Phase 2a-2b)
- Each class has 4-5 tests
- Test happy path + edge cases
- Run before integration

### Integration Tests (Phase 2c)
```
Flow: Extract → Scratchpad → Confirmation → ServiceRequest → Database

Test conversations:
1. Complete data (direct extraction) → Auto-confirm
2. Partial data + retroactive → Show confirmation with sources
3. User edits data at confirmation
4. User cancels booking
5. Duplicate submission (should return same SR ID)
6. Low confidence extractions (should flag in UI)
```

### Edge Cases (Phase 2d)
```
1. Empty scratchpad (no data extracted yet)
2. User asks to edit non-existent field
3. User provides type mismatch (date instead of string)
4. Very long field values (>500 chars)
5. Special characters in names (O'Brien, José, etc.)
6. Concurrent requests for same conversation_id
7. Confirmation triggered before data collected
8. Database save fails (graceful fallback)
```

---

## Rollback Plan

If Phase 2 has critical issues:

1. **Disable Confirmation Flow**
```python
# In BookingIntentDetector
if not PHASE_2_ENABLED:
    return False  # Skip confirmation
```

2. **Fall Back to Phase 1**
```python
# Auto-confirm when phase 2 disabled
if scratchpad_mgr and not PHASE_2_ENABLED:
    auto_confirm()
```

3. **Keep Scratchpad Optional**
```python
# Phase 2a code doesn't break if scratchpad not available
if scratchpad_mgr is None:
    use_extracted_data_directly()
```

---

## Key Success Metrics

### At End of Phase 2a (Infrastructure)
- [ ] ScratchpadManager creates/stores 50 fields without error
- [ ] ConfirmationGenerator produces readable output
- [ ] ServiceRequestBuilder creates valid requests
- [ ] MockDatabaseService saves 10 requests, retrieves correctly
- [ ] All unit tests pass

### At End of Phase 2b (Detection)
- [ ] BookingIntentDetector triggers on 20 test cases correctly
- [ ] ConfirmationHandler detects confirm/edit/cancel accurately
- [ ] Integration tests pass

### At End of Phase 2c (Orchestrator)
- [ ] End-to-end flow: message → extract → scratchpad → confirmation → database
- [ ] User data visible in confirmation UI
- [ ] Edits persist correctly
- [ ] Database contains audit trail

### At End of Phase 2d (Hardening)
- [ ] All bug prevention checks implemented
- [ ] Edge cases handled gracefully
- [ ] No duplicate bookings created
- [ ] Data completeness calculated correctly
- [ ] Performance acceptable (< 500ms per operation)

---

## Estimated Remaining Work After Phase 1

### If Doing Full Phase 2:
```
Phase 2a: 16 hours (4 days)
Phase 2b: 8 hours (2 days)
Phase 2c: 12 hours (3 days)
Phase 2d: 8 hours (2 days)
─────────────────────────
TOTAL: 44 hours (11 days at ~4h/day)
```

### If Doing Phase 2a + Minimal 2c (No UI):
```
Phase 2a: 16 hours (4 days)
Phase 2c (partial): 8 hours (2 days)
─────────────────────────
TOTAL: 24 hours (6 days at ~4h/day)
```

### Critical Path:
1. Complete Phase 1 gaps (1 hour)
2. ScratchpadManager (4 hours)
3. ServiceRequestBuilder (2 hours)
4. Integrate with orchestrator (3 hours)
**= 10 hours minimum for basic Phase 2 data layer**

---

## Decision: Go/No-Go on Phase 2

After reviewing this plan, decide:

**Option A: Full Phase 2** (40+ hours)
- Data governance with audit trail
- User confirmation of data
- Edit capability
- Complete booking process

**Option B: Phase 2a Only** (16 hours)
- Data collection layer only
- No confirmation UI
- No edit capability
- Prepare for future Phase 2b-2d

**Option C: No Phase 2** (0 hours)
- Keep Phase 1 (intent + sentiment routing)
- Data remains in extracted_data dict
- No user confirmation
- Simpler system

**My Recommendation:** Phase 2a + 2c (25 hours) gives you data governance + confirmation without full complexity
