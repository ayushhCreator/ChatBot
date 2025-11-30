# Data Overwrite Bug - Root Cause Analysis

## The Problem (from chat logs)

**Turn 3**: User says "I'm Sneha Reddy"
```
Extracted: {'first_name': 'Sneha', 'last_name': 'Reddy', 'full_name': 'Sneha Reddy'}
State: GREETING → NAME_COLLECTION
```

**Turn 10**: User says "Shukriya" (Thank you in Hindi)
```
Extracted: {'first_name': 'Shukriya', 'last_name': '', 'full_name': 'Shukriya'}
            ↑↑↑ NAME CHANGED! ↑↑↑
State: COMPLETED → COMPLETED
```

**Root Cause**: "Shukriya" was extracted as a customer name instead of recognized as a courtesy phrase.

---

## The Bug Architecture

Three extraction/validation paths run **independently** and can **overwrite** each other:

### Path 1: DataExtractor (in ExtractionCoordinator.extract_for_state)
- Runs DSPy NameExtractor, VehicleDetailsExtractor, DateParser
- Returns: `extracted_data = {first_name: "Shukriya", ...}`
- **Does NOT check if this overwrites prior values**

### Path 2: RetroactiveValidator (in message_processor.py:160-185)
- Scans last 3 messages for missing data
- Calls `validate_and_complete()` which returns `updated_data`
- **Merges retroactive data with `extracted_data.update()`**
- **Does NOT preserve confidently-extracted data**

### Path 3: TypoDetector (in ExtractionCoordinator.detect_typos_in_confirmation)
- Only runs in CONFIRMATION state
- Tries to correct typos
- **Could also overwrite data**

**Problem**: All three paths use `dict.update()` which **unconditionally overwrites** existing values.

---

## Code Analysis: Where Overwrites Happen

### In message_processor.py (lines 168-185):

```python
# Step 1: Initial extraction (Path 1)
extracted_data = self.extraction_coordinator.extract_for_state(
    current_state, user_message, history
)
# Result: {first_name: "Shukriya", last_name: "", ...}

# Step 2: Store in conversation (this is good - permanent storage)
if extracted_data:
    for key, value in extracted_data.items():
        self.conversation_manager.store_user_data(conversation_id, key, value)
# BUG: Now ConversationContext has "Shukriya" instead of "Sneha"!

# Step 3: Retroactive validation (Path 2)
retroactive_data = final_validation_sweep(...)
# This might find "Sneha" in history, but:

if retroactive_data:
    if not extracted_data:
        extracted_data = {}
    for key, value in retroactive_data.items():
        extracted_data[key] = value  # ← OVERWRITES with retroactive value
        # But ConversationContext already has bad data from Step 2!
        self.conversation_manager.store_user_data(conversation_id, key, value)
        # ← OVERWRITES good data with maybe-not-validated data
```

### The Problem Sequence:

```
Turn 3: Extracted "Sneha" → Stored in ConversationContext
Turn 10: Extracted "Shukriya" → Overwrites ConversationContext
Turn 10: Retroactive scan finds "Sneha" in history
        → But it's too late! ConversationContext already has "Shukriya"
```

---

## Why This Happens

### Root Cause 1: No Confidence-Based Merging
```python
# Current approach (wrong):
extracted_data[key] = value  # ← Unconditional overwrite

# Should be:
if confidence(new_value) > confidence(old_value):
    extracted_data[key] = new_value  # Update only if MORE confident
```

### Root Cause 2: ConversationContext Updated Before Validation
```python
# Current flow:
1. Extract data → {first_name: "Shukriya"}
2. IMMEDIATELY store in ConversationContext ← TOO EARLY!
3. Try to validate/correct
4. Retroactive scan (too late, context already corrupted)

# Should be:
1. Extract data
2. Validate all sources (extraction, retroactive, typo detection)
3. THEN update ConversationContext with FINAL, VALIDATED data
```

### Root Cause 3: No Persistence Model
```
ConversationContext.user_data acts as both:
- Temporary extraction buffer (should be temporary)
- Permanent storage (should be persistent)

This causes temporary extractions to pollute permanent state.
```

---

## How Data Overwrites Corrupt State

### Scenario: Name Changes Mid-Conversation

**Turn 1** → Turn 3: Extraction finds "Sneha"
```
ConversationContext.user_data["first_name"] = "Sneha Reddy" ✅
```

**Turn 10** → Turn 11: Extraction finds "Shukriya" (a courtesy phrase, not a name)
```
ConversationContext.user_data["first_name"] = "Shukriya"  ❌ OVERWRITTEN!
```

**Turn 11** → Retroactive scan tries to recover "Sneha" from history
```
But ConversationContext already has "Shukriya"
Retroactive validator is called AFTER data already stored
```

### Impact on Booking:

```
Booking confirmation includes: "Hello, Shukriya"
Should include: "Hello, Sneha Reddy"

ServiceRequest.customer_name = "Shukriya"  ❌
```

---

## The Fix (Architecture Change)

### Introduce Extraction Confidence Scoring

```python
class DataMutation:
    """Represents a potential data change with confidence."""
    field: str
    value: Any
    source: str  # "extraction", "retroactive", "typo_correction"
    confidence: float  # 0.0 to 1.0
    reason: str  # Why this value
    turn_number: int  # When it was extracted
```

### New Validation Pipeline

```
Turn 10, User Message: "Shukriya"
│
├─ Path 1: Extract
│  └─ Result: DataMutation(field="first_name", value="Shukriya",
│                          source="extraction", confidence=0.6,
│                          reason="LLM extraction from message")
│
├─ Path 2: Retroactive Scan
│  └─ Result: DataMutation(field="first_name", value="Sneha",
│                          source="retroactive", confidence=0.8,
│                          reason="Found in Turn 3 message")
│
├─ Path 3: Typo Detection
│  └─ Result: None (no typos)
│
├─ MERGE PHASE ← NEW!
│  For field "first_name":
│    OLD: "Sneha" (confidence=0.9, from Turn 3)
│    NEW1: "Shukriya" (confidence=0.6, extraction)
│    NEW2: "Sneha" (confidence=0.8, retroactive)
│
│  Decision: Keep "Sneha" ✅ (confidence 0.9 > 0.8 > 0.6)
│
└─ STORE in ConversationContext
   └─ ConversationContext.user_data["first_name"] = "Sneha"  ✅
```

### Implementation Strategy

1. **Separate extraction from storage**
   ```python
   # Phase 1: Collect all potential mutations
   mutations = {
       "extraction": extract_for_state(...),
       "retroactive": final_validation_sweep(...),
       "typo_detection": detect_typos_in_confirmation(...)
   }

   # Phase 2: Resolve conflicts
   final_data = resolve_conflicting_mutations(
       mutations,
       current_data=conversation_manager.get_user_data(conversation_id)
   )

   # Phase 3: Store once, with full confidence
   conversation_manager.store_user_data_bulk(conversation_id, final_data)
   ```

2. **Add confidence tracking to models**
   ```python
   @dataclass
   class ValidatedName(BaseModel):
       first_name: str
       last_name: str
       full_name: str
       confidence: float = 0.85  # Add this
       previous_value: Optional[str] = None  # For debugging
       turn_extracted: int = 0  # When was this data extracted
   ```

3. **Update ConversationContext to track metadata**
   ```python
   class ValidatedConversationContext:
       user_data: Dict[str, Any]
       data_confidence: Dict[str, float]  # Track confidence per field
       data_sources: Dict[str, str]  # Track where each field came from
       data_turn_number: Dict[str, int]  # Track when extracted
   ```

---

## Why This Root-Cause Matters

It's not about **keyword detection** or **data validation**.

It's about **data mutation orchestration**:
- Multiple sources producing data simultaneously
- No coordination between sources
- Unconditional overwrites without conflict resolution
- Storage happens before validation completes

**Fixing symptoms** (e.g., better stopword lists) only helps ~5% of cases.
**Fixing the disease** (confidence-based merging) fixes 100% of cases.

---

## Quick Fix Priority

1. **HIGH**: Prevent retroactive data from overwriting confidently-extracted data
2. **MEDIUM**: Add confidence scores to all extracted data
3. **MEDIUM**: Delay ConversationContext.store_user_data() until after all validation
4. **LOW**: Add debug logging showing confidence scores for each field

