# Phase 2 & Phase 3: Complete Implementation Guide

## 📖 Documentation Index

This directory contains comprehensive planning for Phase 2 (Scratchpad/Confirmation) and Phase 3 (Code Cleanup).

### 📄 READ IN THIS ORDER

1. **START HERE:** `PHASE_2_3_SUMMARY.txt`
   - 5-minute overview
   - Quick decisions needed
   - Time estimates

2. **VISUAL GUIDE:** `PHASE_2_3_QUICK_REFERENCE.md`
   - Component summary table
   - File structure diagrams
   - Checklists for each phase

3. **DEEP DIVE:** `PHASE_2_3_DETAILED_TODO.md`
   - 1000+ lines of specs
   - Every component detailed
   - Test cases outlined
   - Integration points
   - Danger zones & safeguards

4. **EXISTING CONTEXT:** `PHASE_1_ANALYSIS_AND_PHASE_2_INTEGRATION.md`
   - Phase 1 completion status
   - Phase 2 architecture overview
   - Links to code locations

5. **PLANNING DOCUMENT:** `INTENT_AND_STAGES_PLAN.md`
   - Original system design
   - Conversation flow
   - Intent classification

---

## ⚡ Quick Start

### If you have 15 minutes:
Read `PHASE_2_3_SUMMARY.txt` → decide YES/NO/PARTIAL on Phase 2

### If you have 1 hour:
Read `PHASE_2_3_SUMMARY.txt` + `PHASE_2_3_QUICK_REFERENCE.md` → understand flow & file structure

### If you have 2+ hours:
Read all documentation → understand every detail before starting

---

## 🎯 Current Status

```
PHASE 1: ✅ COMPLETE (100% tested)
├─ Intent Classification (7 classes)
├─ Sentiment Analysis (5 dimensions)
├─ Data Extraction & Retroactive Validation
├─ Sentiment-Aware Response Tone (NEW - DSPy pipeline)
└─ All 5 sentiment dimensions displayed

PHASE 2: 📋 PLANNED (ready to implement)
├─ ScratchpadManager (foundation)
├─ ConfirmationGenerator (format)
├─ BookingIntentDetector (trigger)
├─ ConfirmationHandler (actions)
├─ ServiceRequestBuilder (persistence)
├─ BookingStateMachine (state tracking)
├─ Orchestrator Integration
├─ BookingFlowManager (coordinator)
└─ API Routes & Tests

PHASE 3: 📋 DESIGNED (refactor after Phase 2)
├─ Split models.py (916 → 400-500 lines)
├─ Refactor retroactive_validator (357 → 200 lines)
├─ Refactor orchestrator (332 → 280 lines)
├─ Create helpers/ package
├─ Update all imports
└─ Final testing & cleanup
```

---

## 📊 Time Investment

| Phase | Components | Hours | Status |
|-------|-----------|-------|--------|
| Phase 1 | 5 | 40-50 | ✅ Done |
| Phase 2 | 12 (8 files + 3 tests + 1 route) | 36-40 | 📋 Ready |
| Phase 3 | 6 (refactoring) | 20-24 | 📋 Designed |
| **TOTAL** | **23** | **96-114** | |

**Note:** Phase 2 and 3 are sequential. Start Phase 3 only after Phase 2 complete.

---

## 🚀 Next Steps

### Decision Point

**Do you want to proceed with Phase 2 implementation?**

Choose one:
- ✅ **YES** - Start immediately with 2a: ScratchpadManager (see `PHASE_2_3_DETAILED_TODO.md`)
- ❌ **NO** - More testing needed on Phase 1 first
- 🟡 **PARTIAL** - Implement only specific Phase 2 components (specify which)

### Questions to Resolve Before Starting

1. **File Organization**: Keep `booking/` package separate, or flatten to root?
2. **Phase 3 Timing**: Do immediately after Phase 2, or separate session?
3. **Component Changes**: Any specs unclear or need adjustment?
4. **Testing Strategy**: Run tests after each component, or batch test at end?

---

## 📁 Current Directory Structure (After Phase 2+3)

```
example/
├── main.py
├── chatbot_orchestrator.py
├── template_manager.py
├── data_extractor.py
├── retroactive_validator.py
├── pywa_integration.py
├── response_composer.py
├── template_strings.py
├── signatures.py
├── modules.py
│
├── models/                    (Phase 3: split from models.py)
│   ├── __init__.py
│   ├── domain.py
│   ├── validation.py
│   └── responses.py
│
├── helpers/                   (Phase 3: new package)
│   ├── __init__.py
│   ├── validators.py
│   ├── extractors.py
│   ├── parsers.py
│   └── response_helpers.py
│
├── booking/                   (Phase 2: new package)
│   ├── __init__.py
│   ├── scratchpad.py
│   ├── confirmation.py
│   ├── booking_detector.py
│   ├── confirmation_handler.py
│   ├── service_request.py
│   ├── state_manager.py
│   └── booking_flow_integration.py
│
├── tests/
│   ├── test_api.py
│   ├── test_intent_classifier.py
│   ├── test_template_manager_intent.py
│   ├── test_sentiment_signature.py
│   ├── test_validated_intent.py
│   ├── conversation_simulator.py
│   ├── test_example.py
│   ├── test_scratchpad.py          (Phase 2)
│   ├── test_confirmation_flow.py   (Phase 2)
│   └── test_service_request.py     (Phase 2)
│
├── docs/                      (Archived documentation)
│   ├── FINAL_SUMMARY_FOR_USER.md
│   ├── PHASE_1_vs_PHASE_2_SUMMARY.md
│   └── (7 other archived files)
│
├── INTENT_AND_STAGES_PLAN.md
├── PHASE_1_ANALYSIS_AND_PHASE_2_INTEGRATION.md
├── PHASE_2_3_SUMMARY.txt              (this session)
├── PHASE_2_3_QUICK_REFERENCE.md      (this session)
├── PHASE_2_3_DETAILED_TODO.md        (this session)
└── README_PHASE_2_3.md               (this file)
```

---

## 🔍 Key Files By Phase

### Phase 1 (Already Complete)
- `signatures.py` - Intent & Sentiment signatures
- `modules.py` - Intent & Sentiment classifiers + NEW Tone pipeline
- `chatbot_orchestrator.py` - Main orchestration
- `template_manager.py` - Response routing
- `retroactive_validator.py` - Data extraction from history
- `data_extractor.py` - Current-turn extraction
- `models.py` - All Pydantic models

### Phase 2 (To Implement)
- `booking/scratchpad.py` - Single source of truth for collected data
- `booking/confirmation.py` - Format confirmation message
- `booking/booking_detector.py` - Detect booking intent
- `booking/confirmation_handler.py` - Handle user actions
- `booking/service_request.py` - Build backend request
- `booking/state_manager.py` - Track conversation state
- `booking/booking_flow_integration.py` - High-level coordinator
- `main.py` - Add `/api/confirmation` route

### Phase 3 (To Refactor)
- `models/` - Split large models.py file
- `helpers/` - Extract utility functions
- Various files - Update imports

---

## 💡 Design Principles

### Phase 2: Scratchpad Architecture
- **Single Source of Truth**: One scratchpad collects all data
- **Complete Metadata**: Track source, turn, confidence, timestamp for each field
- **Audit Trail**: Always know where data came from
- **User Confirmation**: Show summary before booking
- **Editable**: User can fix/change details
- **State Machine**: Prevent invalid transitions

### Phase 3: Code Quality
- **<150 lines per file rule**: Keep files focused and readable
- **Separation of Concerns**: Models, helpers, business logic separate
- **Re-exportable**: `models/__init__.py` re-exports for backward compatibility
- **Testable**: Each module independently testable

---

## ⚠️ Critical Points

### Things That Could Break Everything
1. **Phase 2 without tests** → Write tests alongside code
2. **Phase 3 import breakage** → Always check `from X import Y` works
3. **Orphaned references** → Trace imports backward after refactoring

### Safeguards
- Run `pytest tests/ -v` after each Phase 2 component (2a-2i)
- Run `pytest tests/ --cov=example` before/after Phase 3
- All Phase 1 tests must still pass

---

## 📞 Getting Help

If stuck on:
- **Component specification** → See `PHASE_2_3_DETAILED_TODO.md` section for that component
- **File structure** → See `PHASE_2_3_QUICK_REFERENCE.md` diagrams
- **Integration points** → See `PHASE_2_3_DETAILED_TODO.md` "Integration Points" sections
- **Testing** → See `PHASE_2_3_DETAILED_TODO.md` "Test Cases" for each component
- **Time estimates** → See `PHASE_2_3_SUMMARY.txt` "TIME BREAKDOWN"

---

## ✅ Success Criteria

### Phase 2 Complete When:
- ✅ 8 new Python files created (<150 lines each)
- ✅ 3 new test files created (all green)
- ✅ E2E test: greeting → collection → confirmation → booking
- ✅ All Phase 1 tests still passing
- ✅ `/api/confirmation` route working
- ✅ Documentation updated

### Phase 3 Complete When:
- ✅ All Python files <150 lines
- ✅ models.py split into models/ package
- ✅ helpers/ package created
- ✅ All imports updated
- ✅ Full test suite green
- ✅ Coverage >85%

---

## 🎬 Ready to Start?

1. **Review** `PHASE_2_3_SUMMARY.txt` (5 min)
2. **Decide** Phase 2 go/no-go
3. **Read** `PHASE_2_3_DETAILED_TODO.md` section for 2a: ScratchpadManager
4. **Implement** 2a component
5. **Test** with pytest
6. **Repeat** for 2b through 2n

**Questions? Uncertainties? Ask before starting implementation.**

---

**Status:** Phase 1 ✅ | Phase 2 📋 READY | Phase 3 📋 DESIGNED

**Next Action:** Review documents and confirm Phase 2 go/no-go
