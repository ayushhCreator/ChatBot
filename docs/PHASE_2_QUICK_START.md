# Phase 2 Quick Start Guide

## Import & Use

### Option 1: Use BookingFlowManager (Recommended - Simplest)

```python
from booking import BookingFlowManager

# Initialize
manager = BookingFlowManager(conversation_id="conv-123")

# Process message
response, service_request = manager.process_for_booking(
    user_message="I'd like to confirm my booking",
    extracted_data={
        "first_name": "John",
        "phone": "555-1234",
        "vehicle_brand": "Honda"
    }
)

# Check results
print(response)  # User-friendly message
print(manager.get_state())  # BookingState.CONFIRMATION / BOOKING / etc
print(manager.is_complete())  # True if booking complete
```

### Option 2: Use Bridge for Phase 1 Integration

```python
from booking_orchestrator_bridge import BookingOrchestrationBridge

bridge = BookingOrchestrationBridge()
bridge.initialize_booking("conv-123")

response, service_request = bridge.process_booking_turn(
    user_message="confirm",
    extracted_data={},
    intent=validated_intent_from_phase_1
)
```

### Option 3: Use Individual Components

```python
from booking import (
    ScratchpadManager,
    ConfirmationGenerator,
    BookingIntentDetector,
    ConfirmationHandler,
    ServiceRequestBuilder,
    BookingStateMachine
)

# Create scratchpad
scratchpad = ScratchpadManager(conversation_id="conv-123")

# Add data
scratchpad.add_field(
    section="customer",
    field_name="first_name",
    value="John",
    source="direct_extraction",
    turn=1,
    confidence=0.95
)

# Check if should show confirmation
should_confirm = BookingIntentDetector.should_trigger_confirmation(
    user_message="I want to confirm",
    intent=None,
    current_state="data_collection"
)

if should_confirm:
    # Generate confirmation message
    summary = ConfirmationGenerator.generate_summary(scratchpad.form)
    print(summary)

    # Handle user action
    handler = ConfirmationHandler(scratchpad)
    action = handler.detect_action("yes confirm")

    if action.value == "confirm":
        # Build service request
        request = ServiceRequestBuilder.build(scratchpad, "conv-123")
        print(f"Booked! Reference: {request.service_request_id}")
```

---

## Key Classes

### ScratchpadManager
**Purpose:** Collect and store booking data with full metadata

```python
scratchpad = ScratchpadManager(conversation_id="conv-123")

# Add field
scratchpad.add_field(
    section="customer",
    field_name="first_name",
    value="John",
    source="direct_extraction",
    turn=1,
    confidence=0.95,
    extraction_method="dspy"
)

# Get field
entry = scratchpad.get_field("customer", "first_name")
print(entry.value)  # "John"
print(entry.confidence)  # 0.95

# Check completeness
completeness = scratchpad.get_completeness()  # 0.0 - 100.0
is_ready = scratchpad.is_complete()  # True/False
```

### ConfirmationGenerator
**Purpose:** Format scratchpad into user-friendly messages

```python
# Clean summary
summary = ConfirmationGenerator.generate_summary(scratchpad.form)
# Output:
# 📋 BOOKING CONFIRMATION
# ════════════════════════════════════════
# 👤 CUSTOMER DETAILS:
#    Name: John
#    Phone: 555-1234
# [Edit] [Confirm] [Cancel]

# Debug with sources
detailed = ConfirmationGenerator.generate_with_sources(scratchpad.form)
# Shows sources and confidence scores
```

### BookingIntentDetector
**Purpose:** Detect when user wants to confirm booking

```python
# Check if should trigger confirmation
should_confirm = BookingIntentDetector.should_trigger_confirmation(
    user_message="I want to book this",
    intent=validated_intent,
    current_state="data_collection"
)

# Get confidence score
confidence = BookingIntentDetector.get_confidence(
    user_message="confirm booking",
    intent=None
)
# 0.95 (high confidence due to trigger words)
```

### ConfirmationHandler
**Purpose:** Handle user actions on confirmation screen

```python
handler = ConfirmationHandler(scratchpad)

# Detect action
action = handler.detect_action("edit name Jane")
# ConfirmationAction.EDIT

# Handle actions
if action == ConfirmationAction.CONFIRM:
    handler.handle_confirm()
elif action == ConfirmationAction.EDIT:
    handler.handle_edit("name Jane")  # Updates scratchpad
elif action == ConfirmationAction.CANCEL:
    msg = handler.handle_cancel()  # Clears scratchpad, returns message
```

### BookingStateMachine
**Purpose:** Track conversation state with valid transitions

```python
state_machine = BookingStateMachine()
state_machine.transition(BookingState.DATA_COLLECTION)
state_machine.transition(BookingState.CONFIRMATION)

# Check valid transition
if state_machine.can_transition(BookingState.BOOKING):
    state_machine.transition(BookingState.BOOKING)

# Check current
print(state_machine.get_current_state())  # BookingState.BOOKING

# Valid sequence
# GREETING → DATA_COLLECTION → CONFIRMATION → BOOKING → COMPLETION
# or CONFIRMATION → DATA_COLLECTION (for edits)
# or anywhere → CANCELLED
```

### ServiceRequestBuilder
**Purpose:** Build persistence layer with audit trail

```python
service_request = ServiceRequestBuilder.build(
    scratchpad=scratchpad,
    conversation_id="conv-123"
)

print(service_request.service_request_id)  # "SR-A1B2C3D4"
print(service_request.customer)  # {"first_name": "John", "phone": "..."}
print(service_request.collection_sources)  # Audit trail

# Convert to dict
data = ServiceRequestBuilder.to_dict(service_request)
```

---

## State Machine Transitions

```
GREETING
    ↓
DATA_COLLECTION ←→ (loops back for more data)
    ↓
CONFIRMATION ←→ DATA_COLLECTION (for edits)
    ↓
BOOKING
    ↓
COMPLETION

Any state → CANCELLED (for cancellation)
CANCELLED → GREETING (for new booking)
COMPLETION → GREETING (for new booking)
```

---

## Common Workflows

### Workflow 1: Simple Confirmation

```python
manager = BookingFlowManager("conv-123")

# User provides all data
response1, sr1 = manager.process_for_booking(
    "John, 555-1234, Honda Civic, Dec 15",
    {"first_name": "John", "phone": "555-1234", ...}
)

# User confirms
response2, sr2 = manager.process_for_booking(
    "yes confirm",
    {}
)
# sr2 is now ServiceRequest object
```

### Workflow 2: Edit Before Confirming

```python
manager = BookingFlowManager("conv-123")

# Show confirmation
response1, sr1 = manager.process_for_booking(
    "confirm",
    {"first_name": "John", "phone": "555-1234"}
)
# response1 contains confirmation form

# User edits
response2, sr2 = manager.process_for_booking(
    "edit phone 555-9999",
    {}
)
# Scratchpad updated, shows form again

# User confirms
response3, sr3 = manager.process_for_booking(
    "confirm",
    {}
)
# sr3 is ServiceRequest with edited phone
```

### Workflow 3: Cancel and Restart

```python
manager = BookingFlowManager("conv-123")

# ... some booking flow ...

# User cancels
response, sr = manager.process_for_booking(
    "cancel",
    {}
)
# response: "Booking cancelled..."

# Reset for new booking
manager.reset()
# State back to GREETING, scratchpad cleared
```

---

## Testing

```python
from booking import BookingFlowManager, BookingState

def test_full_booking_flow():
    manager = BookingFlowManager("test-conv")

    # Step 1: Collect data
    response1, _ = manager.process_for_booking(
        "John 555-1234",
        {"first_name": "John", "phone": "555-1234"}
    )

    # Step 2: Trigger confirmation
    response2, _ = manager.process_for_booking(
        "confirm",
        {}
    )
    assert "CONFIRMATION" in response2
    assert manager.get_state() == BookingState.CONFIRMATION

    # Step 3: Confirm booking
    response3, sr = manager.process_for_booking(
        "yes",
        {}
    )
    assert sr is not None
    assert sr.service_request_id.startswith("SR-")
    assert manager.is_complete()
```

---

## API Usage

### Endpoint: POST /api/confirmation

```bash
curl -X POST http://localhost:8002/api/confirmation \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "user_input": "yes confirm",
    "action": "confirm"
  }'
```

**Response:**
```json
{
  "message": "Booking confirmed! Reference: SR-A1B2C3D4",
  "service_request_id": "SR-A1B2C3D4",
  "state": "completion"
}
```

---

## Files Location

```
@example/
├── booking/                      # Phase 2 components
│   ├── scratchpad.py
│   ├── confirmation.py
│   ├── booking_detector.py
│   ├── confirmation_handler.py
│   ├── service_request.py
│   ├── state_manager.py
│   ├── booking_flow_integration.py
│   └── __init__.py
├── booking_orchestrator_bridge.py
├── main.py                       # Contains /api/confirmation
└── tests/
    └── test_booking_flow_integration.py  # E2E tests
```

---

## Debugging

### Check Scratchpad Contents
```python
all_data = manager.scratchpad.get_all_fields()
print(all_data)  # All sections with metadata

# Detailed view
detailed = ConfirmationGenerator.generate_with_sources(
    manager.scratchpad.form
)
print(detailed)
```

### Check State
```python
print(manager.get_state())  # Current state
print(manager.scratchpad.form.metadata)  # Metadata
```

### Check Completeness
```python
completeness = manager.scratchpad.get_completeness()
print(f"Data {completeness}% complete")
```

---

## Best Practices

1. **Always initialize with conversation_id** for audit trail
2. **Check completeness** before showing confirmation
3. **Use BookingFlowManager** unless you need fine control
4. **Handle all 3 actions** (confirm/edit/cancel)
5. **Log service requests** for backend processing
6. **Test your flows** end-to-end

---

**Status:** Phase 2 Production Ready
**Last Updated:** 2024-11-27
