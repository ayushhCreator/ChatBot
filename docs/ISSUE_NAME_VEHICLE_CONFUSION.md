# 🔴 CRITICAL ISSUE: Name Extractor Confusing Vehicle Names with Customer Names

**Issue ID**: ISSUE_NAME_VEHICLE_CONFUSION
**Severity**: P0 - CRITICAL (Data Corruption)
**Date Identified**: 2025-11-28
**Discovered In**: Phase 2 E2E Simulator Test

---

## 📋 Problem Description

The NameExtractor DSPy module is extracting vehicle brand/model combinations as customer names, causing data corruption in the booking flow.

### Example from Simulator:

```
Turn 5 - User Input: "Mahindra Scorpio"

❌ WRONG EXTRACTION:
{
    'first_name': 'Mahindra',        ← VEHICLE BRAND extracted as first name!
    'last_name': 'Scorpio',          ← VEHICLE MODEL extracted as last name!
    'full_name': 'Mahindra Scorpio',
    'vehicle_brand': 'Mahindra',     ← Correct vehicle extraction
    'vehicle_model': 'Scorpio'       ← Correct vehicle extraction
}

✅ CORRECT CUSTOMER NAME (from Turn 3):
{
    'first_name': 'Kavita',
    'last_name': 'Verma',
    'full_name': 'Kavita Verma'
}
```

**Result**: Customer "Kavita Verma" gets overwritten with "Mahindra Scorpio"

---

## 🎯 Root Cause

### 1. **Extraction Coordinator Runs Name Extraction in ALL States**

```python
# File: orchestrator/extraction_coordinator.py:58-68
# Phase 1 behavior: Extract name in ANY state (not state-gated)

def extract_for_state(self, state, user_message, history):
    extracted = {}

    # Try extracting NAME in any state (Phase 1 behavior)
    try:
        name_data = self.data_extractor.extract_name(user_message, history)
        if name_data:
            first_name = str(name_data.first_name).strip()
            if first_name and first_name.lower() not in ["none", "n/a", "unknown"]:
                extracted["first_name"] = first_name  # ← NO VALIDATION!
```

**Problem**: No validation to check if extracted "name" is actually a vehicle brand

### 2. **DSPy NameExtractor is Too Greedy**

The LLM-based name extractor sees "Mahindra Scorpio" and treats it as:
- "Mahindra" = First Name
- "Scorpio" = Last Name

**Why?** The signature doesn't have context about what a vehicle brand is.

### 3. **Retroactive Validator Amplifies the Problem**

```
Server Log - Turn 6:
2025-11-28 16:40:51,470 - INFO - ✅ scan_for_name: Successfully extracted 'Mahindra'
2025-11-28 16:40:51,470 - INFO - Retroactively filled name: Mahindra Scorpio
2025-11-28 16:40:59,590 - WARNING - ⚡ RETROACTIVE IMPROVEMENTS:
    ['first_name', 'last_name', 'full_name', 'vehicle_brand', 'vehicle_model']
```

The retroactive validator scans conversation history and:
1. Finds "Mahindra Scorpio" in a previous message
2. Extracts it as a name (WRONG)
3. Overwrites correct customer name

---

## 💥 Impact

### **Data Corruption**
- ❌ Customer's real name replaced with vehicle brand
- ❌ Booking confirmation shows wrong customer name
- ❌ Database stores incorrect customer information

### **Scratchpad Misleading**
```
Scratchpad: 92.3% complete
BUT: Contains wrong customer name!
```

### **Cascading Failures**
Later in conversation (Turn 7):
```
2025-11-28 16:46:09,127 - INFO - ✅ scan_for_name: Successfully extracted 'Scorpio'
2025-11-28 16:46:09,127 - INFO - Retroactively filled name: Scorpio Mahindra
```

Now customer name is completely backwards!

---

## 🔍 Evidence from Logs

### Turn 3: Correct Name Extracted ✅
```
User: "I am Kavita Verma"
Extracted: {'first_name': 'Kavita', 'last_name': 'Verma', 'full_name': 'Kavita Verma'}
State: greeting → name_collection
Scratchpad: 23.1%
```

### Turn 5: Vehicle Overwrites Name ❌
```
User: "Mahindra Scorpio"
Extracted: {
    'first_name': 'Mahindra',        ← OVERWRITES "Kavita"
    'last_name': 'Scorpio',          ← OVERWRITES "Verma"
    'full_name': 'Mahindra Scorpio',
    'vehicle_brand': 'Mahindra',
    'vehicle_model': 'Scorpio'
}
State: vehicle_details → date_selection
Scratchpad: 92.3%
```

### Turn 6: Retroactive Validator Makes It Worse ❌
```
Server Log:
2025-11-28 16:40:51,470 - INFO - Retroactively filled name: Mahindra Scorpio
2025-11-28 16:40:59,590 - WARNING - ⚡ RETROACTIVE IMPROVEMENTS:
    ['first_name', 'last_name', 'full_name']
```

---

## 🎯 Proposed Solution

### **Option 1: Use VehicleBrandEnum for Validation (RECOMMENDED)**

We already have a comprehensive vehicle brand enum in `models.py:113`:

```python
# models.py:113-204
class VehicleBrandEnum(str, Enum):
    TOYOTA = "Toyota"
    HONDA = "Honda"
    TATA = "Tata"
    MAHINDRA = "Mahindra"
    MARUTI = "Maruti Suzuki"
    # ... 80+ vehicle brands
```

**Implementation**:
```python
# orchestrator/extraction_coordinator.py
from models import VehicleBrandEnum

def _is_vehicle_brand(self, text: str) -> bool:
    """Check if text matches any known vehicle brand."""
    text_lower = text.lower()
    return any(
        brand.value.lower() in text_lower or text_lower in brand.value.lower()
        for brand in VehicleBrandEnum
    )

# In extract_for_state():
if name_data:
    first_name = str(name_data.first_name).strip()
    # Reject if it's a vehicle brand
    if first_name and not self._is_vehicle_brand(first_name):
        if first_name.lower() not in ["none", "n/a", "unknown"]:
            extracted["first_name"] = first_name
```

**Benefits**:
✅ Leverages existing comprehensive brand list (80+ brands)
✅ Single source of truth for vehicle brands
✅ No hardcoded lists to maintain separately

### **Option 2: Add Context to DSPy Signature**

Update `NameExtractionSignature` to be context-aware:

```python
# signatures.py
class NameExtractionSignature(dspy.Signature):
    """Extract customer name from conversation.

    IMPORTANT: Do NOT extract vehicle brand names (like Mahindra, Toyota, Honda)
    as customer names. Only extract actual human names.
    """
    # ... rest of signature
```

### **Option 3: Extract Name Only in Specific States**

Revert to state-gated extraction for names:

```python
# Only extract name if we're in GREETING or NAME_COLLECTION state
if state in [ConversationState.GREETING, ConversationState.NAME_COLLECTION]:
    name_data = self.data_extractor.extract_name(user_message, history)
```

**Problem**: This reintroduces the circular dependency we fixed in Phase 1

---

## 📊 Related Issues

- **ISSUE_RETROACTIVE_TIMEOUT.md**: Retroactive validator amplifies this problem
- **ISSUE_SPURIOUS_DATE_EXTRACTION.md**: Similar greedy extraction issue

---

## ✅ Acceptance Criteria

Fix is successful when:
1. ✅ User says "Mahindra Scorpio" → Only `vehicle_brand` and `vehicle_model` extracted
2. ✅ `first_name`, `last_name`, `full_name` remain as "Kavita Verma"
3. ✅ Retroactive validator doesn't extract vehicle brands as names
4. ✅ Scratchpad shows correct customer name throughout flow
5. ✅ Final booking confirmation has correct customer name

---

## 🚀 Implementation Priority

**Priority**: P0 - CRITICAL
**Estimated Effort**: 2 hours
**Dependencies**: None
**Recommended Approach**: Option 1 (Use VehicleBrandEnum)

---

## 📝 Notes

- This issue was introduced in Phase 1 when we made extraction "always-on" to fix circular dependency
- The fix needs to balance Phase 1's always-on extraction with Phase 2's data validation
- Must test with simulator to ensure no regression
