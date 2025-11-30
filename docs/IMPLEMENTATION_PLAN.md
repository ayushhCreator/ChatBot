# Implementation Plan: Critical Bug Fixes

## ✅ Completed Fixes

### BUG #1: Premature confirmation→completed transition
- **File**: `orchestrator/state_coordinator.py:67-88`
- **Fix**: Added confirmation keyword check before transitioning to COMPLETED
- **Status**: ✅ DONE

### BUG #2: Redundant retroactive scans
- **File**: `orchestrator/message_processor.py:159-169`
- **Fix**: Pass merged data (stored + extracted) to retroactive validator
- **Status**: ✅ DONE

### BUG #3: None/Unknown overwrites
- **File**: `orchestrator/message_processor.py:172-198`
- **Fix**: Skip retroactive data if value is None/Unknown/empty
- **Status**: ✅ DONE

---

## 🔴 Pending Fixes

### FIX #4: Courtesy phrase extraction ("Shukriya", "thank you" → name)
- **Root Cause**: NameExtractor lacks stopword filtering for courtesy phrases
- **Files to modify**:
  - `modules.py`: Add stopword list to NameExtractor
  - `orchestrator/extraction_coordinator.py`: Add post-extraction validation
- **Implementation**:
  ```python
  COURTESY_STOPWORDS = ["shukriya", "thank you", "thanks", "dhanyavaad", "bahut acha"]
  # Filter extracted names against stopwords
  if extracted_name.lower() in COURTESY_STOPWORDS:
      return None  # Invalid name
  ```

### FIX #5: Chatbot history pollution (chatbot responses → extractions)
- **Root Cause**: `filter_dspy_history_to_user_only()` not used consistently
- **Files to check**:
  - `orchestrator/extraction_coordinator.py`: ✅ Already using user-only filter
  - `retroactive_validator.py`: ✅ Already using user-only filter
- **Status**: ✅ ALREADY IMPLEMENTED (verify in testing)

### FIX #6: Confirmation flow (3 requests with scratchpad data)
- **Current Behavior**: State transitions to CONFIRMATION, waits for single "yes"
- **Required Behavior**:
  1. Enter CONFIRMATION state
  2. Send 3 confirmation requests (5s intervals) with scratchpad data
  3. If user says "yes"/"confirm"/"haa kardo" → book
  4. If user provides corrections (key:value pairs) → update scratchpad, repeat
  5. If user silent after 3 attempts → stay in CONFIRMATION

- **Files to modify**:
  - `orchestrator/message_processor.py`: Add confirmation attempt counter to context
  - `orchestrator/state_coordinator.py`: Check confirmation attempts before transitioning
  - `response_composer.py`: Generate confirmation message with scratchpad data
  - `conversation_manager.py`: Add `confirmation_attempts` field to context

- **Implementation**:
  ```python
  # In CONFIRMATION state:
  if current_state == CONFIRMATION:
      attempts = context.metadata.get('confirmation_attempts', 0)

      if attempts < 3:
          # Send confirmation request with scratchpad
          response = format_confirmation_request(scratchpad_data)
          context.metadata['confirmation_attempts'] = attempts + 1
          return response

      # After 3 attempts, check for confirmation
      if user_confirmed(user_message):
          create_booking()  # FIX #7
          clear_scratchpad()
          transition_to_completed()
      elif user_provided_corrections(user_message):
          update_scratchpad(corrections)
          context.metadata['confirmation_attempts'] = 0  # Reset counter
  ```

### FIX #7: Booking creation and scratchpad clearing
- **Current Issue**: No booking ID created, scratchpad not managed correctly
- **Required Flow**:
  1. User confirms → Create ServiceRequest with booking_id
  2. Store booking_id in context.metadata
  3. Clear scratchpad AFTER booking created
  4. Stop retroactive validator (set flag in context)

- **Files to modify**:
  - `booking/confirmation_handler.py`: Create actual booking
  - `orchestrator/message_processor.py`: Add booking_id check, control retroactive validator
  - `conversation_manager.py`: Add `booking_id`, `retroactive_enabled` to metadata

- **Implementation**:
  ```python
  # Only run retroactive validator if:
  if context.metadata.get('retroactive_enabled', True):
      if current_state == GREETING:
          context.metadata['retroactive_enabled'] = True  # Re-enable

      retroactive_data = final_validation_sweep(...)
  else:
      # Skip retroactive after booking completed
      retroactive_data = {}

  # After booking:
  booking_id = create_service_request(scratchpad_data)
  context.metadata['booking_id'] = booking_id
  context.metadata['retroactive_enabled'] = False
  scratchpad.clear()
  ```

### FIX #8: message_processor.py bloat (318 lines → split)
- **Issue**: Single file violating SRP, approaching 400+ lines
- **Solution**: Extract helpers to `orchestrator/message_processing_helpers.py`
  - `_generate_empathetic_response()` → `EmpathyGenerator`
  - `_get_template_variables()` → `TemplateVariableExtractor`
  - Retroactive validation block → `RetroactiveCoordinator`

- **Keep in `message_processor.py`**:
  - Main `process_message()` orchestration flow
  - Coordinator initialization

---

## 📝 Implementation Order

1. ✅ Fix unused `extracted_data` in `_generate_empathetic_response()`
2. ⬜ FIX #4: Courtesy phrase filtering
3. ⬜ FIX #6: Confirmation flow (3 requests)
4. ⬜ FIX #7: Booking creation + scratchpad clearing
5. ⬜ FIX #8: Split message_processor.py
6. ⬜ Test with conversation_simulator_v2.py

---

## 🧪 Testing Criteria

**Scenario 1 (Happy Path) Must Pass:**
- ✅ Confirmation triggered when all 5 fields present
- ✅ Booking completed with valid service_request_id
- ✅ Scratchpad completeness = 100% (not 0%)
- ✅ No "Shukriya" extracted as name
- ✅ No chatbot responses triggering extractions
