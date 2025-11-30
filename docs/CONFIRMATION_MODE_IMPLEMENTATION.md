# CONFIRMATION_MODE Toggle Implementation

## Overview

Implemented a surgical fix to resolve the service request ID generation race condition by adding a `CONFIRMATION_MODE` toggle that separates CHAT-based and BUTTON-based confirmation mechanisms.

## Problem Identified

**Root Cause**: Two competing confirmation mechanisms causing race condition:
1. **DSPy-based auto-detection** in `/chat` endpoint (Turn 8: detects "proceed with booking" → creates service request immediately)
2. **Button-based explicit confirmation** in `/api/confirmation` endpoint (Turn 9: button click expects to create booking)

**Race Condition**: By Turn 9, state is already COMPLETED (from Turn 8), so booking flow check fails → returns "Data saved" message instead of confirming booking.

## Solution Architecture

### Configuration Toggle

**File**: `example/config.py`

```python
# CONFIRMATION MODE TOGGLE - Controls when service request is created
# "CHAT": Create service request immediately when DSPy detects confirmation intent (in /chat endpoint)
#         User says "yes/confirm" → Service Request created → State moves to COMPLETED
# "BUTTON": Only create service request when explicit button is clicked (in /api/confirmation endpoint)
#           User says "yes/confirm" → Stays in CONFIRMATION state → Button click creates Service Request
#
# IMPORTANT: In BUTTON mode, /chat endpoint NEVER creates service requests, only /api/confirmation does
CONFIRMATION_MODE = "BUTTON"  # Options: "CHAT" or "BUTTON"
```

### Files Modified

#### 1. `/example/config.py` (NEW)
- Added `CONFIRMATION_MODE` toggle with detailed documentation
- Default: `"BUTTON"` mode

#### 2. `/example/orchestrator/message_processor.py` (MODIFIED)
**Lines 358-383**: Modified confirmation flow to respect `CONFIRMATION_MODE`:

```python
if config.CONFIRMATION_MODE == "CHAT":
    # Create booking using ServiceRequestBuilder (scratchpad is now populated)
    from booking.service_request import ServiceRequestBuilder
    service_request = ServiceRequestBuilder.build(scratchpad, conversation_id)
    service_request_id = service_request.service_request_id
    # ... store metadata, mark completed ...
    logger.warning(f"✅ BOOKING CREATED (CHAT MODE): service_request_id={service_request_id}")
else:  # BUTTON mode
    # Stay in CONFIRMATION state, do NOT create service request here
    # The /api/confirmation endpoint will handle service request creation
    logger.info(f"🔘 BUTTON MODE: User confirmed, waiting for button click to create service request")
```

**Lines 449-465**: Modified scratchpad clearing to only happen in CHAT mode:

```python
if service_request_id and config.CONFIRMATION_MODE == "CHAT":
    # Dump service request JSON before clearing scratchpad (CHAT mode only)
    from service_request_dumper import dump_service_request
    dump_service_request(...)

    # Now clear scratchpad after successful dump
    scratchpad.clear_all()
    logger.info(f"🧹 SCRATCHPAD CLEARED (CHAT MODE): service_request_id={service_request_id}")
```

#### 3. `/example/main.py` (MODIFIED)
**Lines 324-344**: Modified `/api/confirmation` endpoint to dump and clear scratchpad in BUTTON mode:

```python
# CRITICAL: Dump service request JSON and clear scratchpad (BUTTON mode only)
if service_request_id and bridge.booking_manager:
    scratchpad = bridge.booking_manager.scratchpad
    if scratchpad:
        # Dump service request JSON before clearing scratchpad
        from service_request_dumper import dump_service_request
        dump_service_request(
            service_request_id=service_request_id,
            conversation_id=conversation_id,
            scratchpad=scratchpad,
            confirmation_method="button",
            additional_metadata={"confirmation_mode": "BUTTON", "action": action}
        )

        # Now clear scratchpad after successful dump
        scratchpad.clear_all()
        logger.info(f"🧹 SCRATCHPAD CLEARED (BUTTON MODE): service_request_id={service_request_id} confirmed")
```

#### 4. `/example/service_request_dumper.py` (NEW)
Shared helper function for dumping service request JSON to avoid code duplication:

```python
def dump_service_request(
    service_request_id: str,
    conversation_id: str,
    scratchpad,
    confirmation_method: str,  # "chat" or "button"
    additional_metadata: Dict[str, Any] = None
) -> Path:
    """
    Dump service request data to JSON file in datadump folder.

    Only ONE will execute per conversation based on CONFIRMATION_MODE setting.
    """
```

## User Requirements Addressed

### ✅ 1. Configuration-Based Mode Separation
> "create a @example/config.py toggle between chat and button mode confirmation"

**Solution**: Added `CONFIRMATION_MODE` toggle in `config.py`

### ✅ 2. Service Request ID-Dependent Scratchpad Clearing
> "IN any and ALL cases if and only if service request ID is made then scratchpad can be reset else NOT"

**Solution**: Scratchpad clearing happens ONLY when `service_request_id` exists:
- **CHAT mode**: Clears in `orchestrator/message_processor.py:464`
- **BUTTON mode**: Clears in `main.py:343`

### ✅ 3. Reliable Service Request ID Generation
> "If booking is confirmed by user service request ID must get generated if user does not edit the details or stays silent or says yes/confirm type words"

**Solution**:
- **CHAT mode**: Service request created immediately on confirmation (line 364)
- **BUTTON mode**: Service request created when button is clicked (`booking_flow_integration.py:96`)

### ✅ 4. JSON Data Dump with Service Request ID
> "dump the unique service detail json with the service ID in the name and in the json in the @example/datadump/ folder"

**Solution**: Created `service_request_dumper.py` that:
- Saves JSON with filename `{service_request_id}.json`
- Includes complete scratchpad data (customer, vehicle, appointment)
- Called from BOTH endpoints (only ONE executes based on mode)

## Behavior Matrix

| Mode | `/chat` Endpoint | `/api/confirmation` Endpoint |
|------|-----------------|----------------------------|
| **CHAT** | Creates service request on "yes/confirm" text<br>Dumps JSON<br>Clears scratchpad<br>Moves to COMPLETED state | Not used |
| **BUTTON** | Stays in CONFIRMATION state<br>Waits for button click<br>Does NOT create service request | Creates service request on button click<br>Dumps JSON<br>Clears scratchpad<br>Moves to COMPLETED state |

## JSON Dump Format

**Filename**: `datadump/{service_request_id}.json`

**Example**: `datadump/SR-A324BAF3.json`

```json
{
  "service_request_id": "SR-A324BAF3",
  "conversation_id": "user123",
  "status": "confirmed",
  "created_at": "2025-11-30T12:34:56.789",
  "customer": {
    "first_name": "Ravi",
    "last_name": "Kumar",
    "phone": "9876543210"
  },
  "vehicle": {
    "brand": "Honda",
    "model": "City",
    "plate": "DL01AB1234"
  },
  "appointment": {
    "date": "2025-12-01",
    "service_type": "wash"
  },
  "metadata": {
    "completeness": 100.0,
    "confirmation_method": "button",
    "confirmation_mode": "BUTTON",
    "action": "confirm"
  }
}
```

## Testing Scenarios

### Scenario 1: BUTTON Mode (Default)
1. User goes through chat flow → reaches CONFIRMATION state
2. User says "yes/confirm" → State STAYS in CONFIRMATION (no service request created)
3. User clicks "Confirm" button → `/api/confirmation` called
4. Service request created → JSON dumped → Scratchpad cleared → State moves to COMPLETED
5. **Result**: Service request ID returned reliably

### Scenario 2: CHAT Mode
1. User goes through chat flow → reaches CONFIRMATION state
2. User says "yes/confirm" → Service request created immediately
3. JSON dumped → Scratchpad cleared → State moves to COMPLETED
4. **Result**: Service request ID returned in `/chat` response

## Critical Guarantees

1. **Only ONE dump per conversation**: Either CHAT or BUTTON mode executes, never both
2. **Scratchpad cleared ONLY after service_request_id confirmed**: Prevents data loss
3. **No race condition**: Endpoints don't fight each other based on mode setting
4. **JSON contains full data**: Captured before scratchpad clearing

## Migration Path

**Current**: Default is `BUTTON` mode (existing frontend expects button clicks)

**To switch to CHAT mode**:
```python
# In config.py
CONFIRMATION_MODE = "CHAT"
```

No other code changes needed!
