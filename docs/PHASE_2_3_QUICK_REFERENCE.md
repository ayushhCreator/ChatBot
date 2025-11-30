# Phase 2 & 3 Quick Reference

## 📊 Big Picture

```
PHASE 1 (DONE ✅)              PHASE 2 (36-40 hrs)           PHASE 3 (20-24 hrs)
├─ Intent Detection       →    ├─ ScratchpadManager    →    ├─ Split models.py
├─ Sentiment Analysis     →    ├─ ConfirmationGenerator →   ├─ Refactor retroactive_validator
├─ Data Extraction        →    ├─ BookingDetector      →    ├─ Refactor orchestrator
├─ Response Routing       →    ├─ ConfirmationHandler  →    ├─ Create helpers/
└─ Sentiment-Aware Tone   →    ├─ ServiceRequest       →    └─ Test & cleanup
                               ├─ BookingStateMachine  →
                               ├─ Integrate in Orchestrator →
                               ├─ BookingFlowManager   →
                               ├─ main.py routes      →
                               ├─ Tests               →
                               └─ Documentation       →
```

## 🎯 Phase 2: Component Summary

| Component | File | Lines | Purpose | Status |
|-----------|------|-------|---------|--------|
| ScratchpadManager | scratchpad.py | <150 | Collect data with metadata | 📝 TO-DO |
| ConfirmationGenerator | confirmation.py | <100 | Format confirmation message | 📝 TO-DO |
| BookingIntentDetector | booking_detector.py | <80 | Detect booking intent | 📝 TO-DO |
| ConfirmationHandler | confirmation_handler.py | <120 | Handle confirm/edit/cancel | 📝 TO-DO |
| ServiceRequest | service_request.py | <150 | Build backend request | 📝 TO-DO |
| BookingStateMachine | state_manager.py | <120 | Track conversation state | 📝 TO-DO |
| Orchestrator Integration | chatbot_orchestrator.py | +30-50 | Add _handle_booking_flow() | 📝 TO-DO |
| BookingFlowManager | booking_flow_integration.py | <200 | High-level coordinator | 📝 TO-DO |
| API Routes | main.py | +15-20 | Add /api/confirmation | 📝 TO-DO |
| Tests | test_*.py | <100 each | Validate each component | 📝 TO-DO |

## 📂 Phase 2 File Structure

```
example/
├── booking/                    (NEW PACKAGE)
│   ├── scratchpad.py          (145 lines) ← foundation
│   ├── confirmation.py        (98 lines)
│   ├── booking_detector.py    (75 lines)
│   ├── confirmation_handler.py (115 lines)
│   ├── service_request.py     (140 lines)
│   ├── state_manager.py       (115 lines)
│   └── booking_flow_integration.py (180 lines) ← orchestrator
│
├── tests/
│   ├── test_scratchpad.py     (NEW)
│   ├── test_confirmation_flow.py (NEW)
│   └── test_service_request.py (NEW)
│
└── main.py                     (+ /api/confirmation route)
```

## 🔄 Data Flow: Phase 2

```
USER MESSAGE
    ↓
[Phase 1: Intent + Sentiment Detection]
    ↓
data_extractor → extracts {first_name: "John", ...}
    ↓
[Phase 2: ScratchpadManager]
  .add_field("customer", "first_name", "John", source="direct", turn=1)
    ↓
[BookingIntentDetector checks: should show confirmation?]
    ├─ NO: Continue conversation
    └─ YES: ↓
      [ConfirmationGenerator formats scratchpad]
      📋 BOOKING CONFIRMATION
      Name: John
      Phone: 555-0123
      [Confirm] [Edit] [Cancel]
        ↓
      USER CHOOSES ACTION
        ├─ "confirm" → ConfirmationHandler.detect_action() → CONFIRM
        │   ↓
        │   ServiceRequestBuilder.build() → ServiceRequest object
        │   ↓
        │   POST /api/backend → "Booking created: SR-ABC123"
        │
        ├─ "edit name" → ConfirmationHandler.detect_action() → EDIT
        │   ↓
        │   scratchpad.update_field("customer", "first_name", "Jane")
        │   ↓
        │   ConfirmationGenerator formats updated scratchpad
        │   ↓
        │   Shows confirmation form again
        │
        └─ "cancel" → ConfirmationHandler.detect_action() → CANCEL
            ↓
            scratchpad = None
            state = GREETING
            ↓
            "Booking cancelled. How else can we help?"
```

## 🎨 Phase 3: Refactoring Targets

### Before Phase 3
```
example/
├── models.py                   916 lines ❌ TOO LONG
├── retroactive_validator.py    357 lines ❌ TOO LONG
├── chatbot_orchestrator.py     332 lines ⚠️  WILL EXCEED
└── (no helpers package)        ❌ MIXED CONCERNS
```

### After Phase 3
```
example/
├── models/
│   ├── __init__.py            (20 lines) ✅ Re-exports
│   ├── domain.py              (200 lines) ✅ Customer, Vehicle, Appointment
│   ├── validation.py          (150 lines) ✅ ValidatedIntent, Metadata
│   └── responses.py           (80 lines) ✅ ResponseMode, Sentiment
├── helpers/
│   ├── __init__.py            (30 lines) ✅ Exports
│   ├── validators.py          (80 lines) ✅ Validation helpers
│   ├── extractors.py          (120 lines) ✅ Extraction functions
│   ├── parsers.py             (100 lines) ✅ NLP parsing
│   └── response_helpers.py    (150 lines) ✅ Response formatting
├── retroactive_validator.py    200 lines ✅ Uses helpers
└── chatbot_orchestrator.py     280 lines ✅ Clean and focused
```

## 📋 Phase 2 Checklist

### 2a: ScratchpadManager
- [ ] Create scratchpad.py
- [ ] Define FieldEntry (Pydantic model)
- [ ] Define ScratchpadForm (Pydantic model)
- [ ] Implement ScratchpadManager class (CRUD + completeness)
- [ ] Write test_scratchpad.py (5 test cases)
- [ ] All tests pass ✅

### 2b: ConfirmationGenerator
- [ ] Create confirmation.py
- [ ] Implement generate_summary() method
- [ ] Implement generate_with_sources() method
- [ ] Test with various scratchpad states
- [ ] Verify formatting (emoji, line breaks)
- [ ] All tests pass ✅

### 2c: BookingIntentDetector
- [ ] Create booking_detector.py
- [ ] Define CONFIRMATION_TRIGGERS list
- [ ] Implement should_trigger_confirmation() logic
- [ ] Test trigger detection
- [ ] Test intent-based detection
- [ ] Test state-based detection

### 2d: ConfirmationHandler
- [ ] Create confirmation_handler.py
- [ ] Define ConfirmationAction enum
- [ ] Implement detect_action() logic
- [ ] Implement handle_edit() for field updates
- [ ] Implement handle_confirm() / handle_cancel()
- [ ] Test all three action paths

### 2e: ServiceRequest
- [ ] Create service_request.py
- [ ] Define ServiceRequest model
- [ ] Implement ServiceRequestBuilder
- [ ] Test with full/partial data
- [ ] Verify audit trail (collection_sources)
- [ ] Test ID generation & timestamps

### 2f: BookingStateMachine
- [ ] Create state_manager.py
- [ ] Define BookingState enum
- [ ] Implement BookingStateMachine class
- [ ] Implement state transition validation
- [ ] Test valid transitions allowed
- [ ] Test invalid transitions blocked

### 2g: Orchestrator Integration
- [ ] Update chatbot_orchestrator.py
- [ ] Add _handle_booking_flow() method
- [ ] Add self.scratchpad instance variable
- [ ] Add self.booking_state instance variable
- [ ] Integrate in process_message() flow
- [ ] Test integration

### 2h: BookingFlowManager
- [ ] Create booking_flow_integration.py
- [ ] Implement process_for_booking() method
- [ ] Implement facade pattern (hides complexity)
- [ ] Test coordinate all Phase 2 components
- [ ] Test error handling

### 2i: API Routes
- [ ] Update main.py
- [ ] Add POST /api/confirmation route
- [ ] Implement request/response handling
- [ ] Test all three actions (confirm/edit/cancel)

### 2j-l: Test Suite
- [ ] test_scratchpad.py (CRUD, metadata, completeness)
- [ ] test_confirmation_flow.py (E2E flow)
- [ ] test_service_request.py (builder, audit trail)

### 2m: Integration Testing
- [ ] Run `pytest tests/ -v`
- [ ] Verify Phase 1 tests still pass
- [ ] Verify Phase 2 tests all pass
- [ ] No regressions

### 2n: Documentation
- [ ] Update PHASE_1_ANALYSIS_AND_PHASE_2_INTEGRATION.md
- [ ] Add completion status for each component
- [ ] Update file structure diagram

---

## 📋 Phase 3 Checklist

### 3a: Refactor models.py
- [ ] Create models/ directory
- [ ] Split into domain.py (200), validation.py (150), responses.py (80)
- [ ] Create __init__.py with re-exports
- [ ] Update all imports in codebase
- [ ] Tests still pass

### 3b: Refactor retroactive_validator.py
- [ ] Create helpers/extractors.py (120 lines)
- [ ] Create helpers/validators.py (80 lines)
- [ ] Extract functions from retroactive_validator.py
- [ ] Keep core logic in retroactive_validator.py (200 lines)
- [ ] Update imports
- [ ] Tests still pass

### 3c: Refactor chatbot_orchestrator.py
- [ ] Create helpers/response_helpers.py (150 lines)
- [ ] Extract response formatting logic
- [ ] Keep orchestration logic in orchestrator (280 lines)
- [ ] Update imports
- [ ] Tests still pass

### 3d: Create helpers/ Package
- [ ] Create helpers/ directory
- [ ] Create __init__.py (30 lines, exports all)
- [ ] Organize validators.py, extractors.py, parsers.py, response_helpers.py
- [ ] Verify all imports work

### 3e: Update Imports
- [ ] Search for `from models import`
- [ ] Update to `from models.domain import` or `from models import`
- [ ] Search for broken imports
- [ ] Test

### 3f: Final Test Suite
- [ ] Run `pytest tests/ -v --tb=short`
- [ ] Run coverage: `pytest tests/ --cov=example`
- [ ] Check coverage >85%
- [ ] All tests pass ✅

---

## ⏱️ Time Estimates

### Phase 2 (36-40 hours total)

| Task | Time | Cumulative |
|------|------|-----------|
| 2a: ScratchpadManager | 3-4 hrs | 3-4 |
| 2b: ConfirmationGenerator | 2-3 hrs | 5-7 |
| 2c: BookingIntentDetector | 1.5-2 hrs | 6.5-9 |
| 2d: ConfirmationHandler | 3-4 hrs | 9.5-13 |
| 2e: ServiceRequest | 3-4 hrs | 12.5-17 |
| 2f: BookingStateMachine | 2-3 hrs | 14.5-20 |
| 2g: Orchestrator Integration | 4-5 hrs | 18.5-25 |
| 2h: BookingFlowManager | 3-4 hrs | 21.5-29 |
| 2i: API Routes | 2-3 hrs | 23.5-32 |
| 2j-l: Tests | 3-4 hrs | 26.5-36 |
| 2m: Integration Testing | 1-2 hrs | 27.5-38 |
| 2n: Documentation | 1-2 hrs | 28.5-40 |

### Phase 3 (20-24 hours total)

| Task | Time | Cumulative |
|------|------|-----------|
| 3a: Refactor models.py | 4-5 hrs | 4-5 |
| 3b: Refactor retroactive_validator | 3-4 hrs | 7-9 |
| 3c: Refactor orchestrator | 2-3 hrs | 9-12 |
| 3d: Create helpers/ | 2 hrs | 11-14 |
| 3e: Update imports | 2-3 hrs | 13-17 |
| 3f: Final test suite | 2-3 hrs | 15-20 |
| Contingency (refactoring surprises) | 4-4 hrs | 19-24 |

---

## 🚀 When Ready to Start

Phase 2 go/no-go decision needed:

**YES, start Phase 2:**
- Ready for 36-40 hour investment
- Want booking flow complete this session
- Willing to refactor (Phase 3) after

**NO, wait:**
- Phase 1 needs more testing first
- Want to revisit architecture before Phase 2
- Prefer shorter sessions

> **Current Status:** Phase 1 ✅ COMPLETE | Phase 2 📝 PLANNED | Phase 3 📋 DESIGNED

Next: Confirm Phase 2 go/no-go. Ready when you are.
