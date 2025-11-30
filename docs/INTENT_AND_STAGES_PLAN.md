# Intent Detection & Conversation Stages - Architecture Plan

## Executive Summary

The chatbot currently makes template decisions based **ONLY on sentiment** (interest > 7.0 → show catalog). This is why it pushes catalogs inappropriately.

**Solution:** Add **Intent Classification** layer that detects WHAT the customer wants, then combine with sentiment for smarter decisions.

---

## 1. Intent Taxonomy (7 Classes)

| Intent | Trigger Words | Expected Response | Example |
|--------|---------------|------------------|---------|
| **pricing_inquiry** | "cost?", "charge?", "price?", "rates", "how much", "expensive" | Show pricing template ONLY | "What do you charge?" |
| **catalog_request** | "services", "what do you offer", "menu", "catalog", "options" | Show catalog template | "What services do you offer?" |
| **booking_intent** | "book", "schedule", "appointment", "reserve", "wash", "tomorrow" | Move to discovery/scheduling | "I want to book a wash" |
| **general_inquiry** | "help", "how does it work", "tell me about", "information" | Show LLM response ONLY | "How does the process work?" |
| **complaint** | "problem", "issue", "complaint", "bad", "poor", "wrong", "scratch", "damage" | Escalate to human | "Washed yesterday, left a scratch" |
| **small_talk** | "hi", "hello", "how are you", "thanks", "great" | Brief friendly response | "Hey, how's it going?" |
| **reschedule** | "change date", "different time", "cancel", "postpone", "reschedule" | Move to rescheduling flow | "Can I reschedule my appointment?" |

---

## 2. Conversation Stages (Updated State Machine)

Current stages are TOO COARSE. Need to split into:

```
greeting
    ↓
intent_detection ← **NEW**: Classify what customer wants
    ↓ (branches based on intent)
├─ pricing_inquiry → show_pricing (template only, then done)
├─ catalog_request → show_catalog (template only, then done)
├─ booking_intent → discovery (collect vehicle, date, service)
│   ├─ name_collection
│   ├─ vehicle_details
│   ├─ date_selection
│   └─ service_selection
├─ general_inquiry → answer_question (LLM only, no template)
├─ complaint → escalation (hand to human)
└─ small_talk → rapport (brief response, redirect to task)
    ↓
confirmation (confirm booking details)
    ↓
completion (send confirmation + follow-up)
```

---

## 3. Decision Logic (Intent + Sentiment)

**Current (BROKEN):**
```python
if sentiment_interest > 7.0:
    show_catalog()  # ❌ Always shows catalog regardless of intent
```

**Fixed:**
```python
intent = classify_intent(user_message)

if intent == "pricing_inquiry":
    return (ResponseMode.TEMPLATE_ONLY, "pricing")
elif intent == "catalog_request":
    return (ResponseMode.TEMPLATE_ONLY, "catalog")
elif intent == "booking_intent":
    return (ResponseMode.TEMPLATE_ONLY, "plans")  # Show plans for booking
elif intent == "complaint":
    return escalate_to_human()
elif intent == "small_talk":
    # Brief LLM response based on sentiment
    if sentiment_anger > 6:
        return (ResponseMode.LLM_ONLY, "")  # No template for angry customers
    else:
        return (ResponseMode.LLM_ONLY, "")  # LLM handles it
elif intent == "general_inquiry":
    return (ResponseMode.LLM_ONLY, "")  # Never show templates for questions
else:  # intent == "reschedule"
    return handle_reschedule()
```

---

## 4. Sentiment Dimension Issue - Why Only 3 Shown?

**Current Output:**
```
SENTIMENT: Interest=5.0  Anger=1.0  Boredom=1.0
```

**Model Stores All 5:**
```python
class ValidatedSentimentScores(BaseModel):
    interest: float      # 1-10
    anger: float         # 1-10
    disgust: float       # 1-10 ← NOT DISPLAYED
    boredom: float       # 1-10
    neutral: float       # 1-10 ← NOT DISPLAYED
```

**Root Cause:** conversation_simulator.py line 147 only displays 3:
```python
f"Interest={sentiment.get('interest')} Anger={sentiment.get('anger')} Boredom={sentiment.get('boredom')}"
```

**Problem:** We're NOT using disgust + neutral, making sentiment classification incomplete.

**Fix Plan:**
- LLM should classify all 5 dimensions
- Use all 5 in decision logic (not just interest/anger/boredom)
- Display all 5 in simulator
- Use disgust score to detect sarcasm/irony
- Use neutral score to detect confusion

---

## 5. File-by-File Changes

### A. `signatures.py` - Add/Update Signatures

**Already exists:** `IntentClassificationSignature` ✓
**Need to verify:** Outputs correct intent_class enum

```python
# KEEP as-is
class IntentClassificationSignature(dspy.Signature):
    """Classify user intent from message in context."""
    conversation_history: dspy.History = dspy.InputField(...)
    current_message = dspy.InputField(...)

    reasoning = dspy.OutputField(...)
    intent_class = dspy.OutputField(
        desc="One of: pricing, catalog, booking, general_inquiry, complaint, small_talk, reschedule"
    )
```

**Update SentimentAnalysisSignature** to clarify all 5 dimensions:
```python
class SentimentAnalysisSignature(dspy.Signature):
    """Analyze sentiment across ALL 5 dimensions."""
    conversation_history: dspy.History = dspy.InputField(...)
    current_message = dspy.InputField(...)

    reasoning = dspy.OutputField(...)
    interest_score = dspy.OutputField(desc="Interest/curiosity level 1-10")
    anger_score = dspy.OutputField(desc="Anger/frustration level 1-10")
    disgust_score = dspy.OutputField(desc="Disgust/disappointment level 1-10")
    boredom_score = dspy.OutputField(desc="Boredom/impatience level 1-10")
    neutral_score = dspy.OutputField(desc="Neutral/confused level 1-10")
```

---

### B. `modules.py` - Add/Ensure Modules

**Already exists:** `IntentClassifier` ✓
**Need to ensure:** It returns proper intent_class

```python
class IntentClassifier(dspy.Module):
    """Classify user intent (pricing, catalog, booking, etc.)"""
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(IntentClassificationSignature)

    def forward(self, conversation_history=None, current_message: str = ""):
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_message=current_message
        )
        # Returns: intent_class="pricing" | "catalog" | "booking" | "general_inquiry" | "complaint" | "small_talk" | "reschedule"
```

**Keep as-is:** `SentimentAnalyzer` (already has ChainOfThought) ✓

---

### C. `models.py` - Add Intent Model

**Add new Pydantic model:**
```python
class ValidatedIntent(BaseModel):
    """Classified user intent with reasoning."""
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
    reasoning: str = Field(..., min_length=10, max_length=500)
    metadata: ExtractionMetadata = Field(default_factory=...)
```

**Update SentimentScores** to track all 5:
```python
class ValidatedSentimentScores(BaseModel):
    interest: float = Field(ge=1.0, le=10.0)
    anger: float = Field(ge=1.0, le=10.0)
    disgust: float = Field(ge=1.0, le=10.0)
    boredom: float = Field(ge=1.0, le=10.0)
    neutral: float = Field(ge=1.0, le=10.0)
    reasoning: str = Field(...)
    # ADD method to get "dominant" sentiment
    @property
    def dominant_sentiment(self) -> str:
        scores = {
            "interest": self.interest,
            "anger": self.anger,
            "disgust": self.disgust,
            "boredom": self.boredom,
            "neutral": self.neutral
        }
        return max(scores, key=scores.get)
```

---

### D. `template_manager.py` - Use Intent + Sentiment

**Current (broken):**
```python
if sentiment_interest > self.sentiment_threshold_interested:
    return (ResponseMode.TEMPLATE_THEN_LLM, "catalog")
```

**Fixed:**
```python
def decide_response_mode(
    self,
    user_message: str,
    intent: str,  # ← NEW parameter
    sentiment_interest: float = 5.0,
    sentiment_anger: float = 1.0,
    sentiment_disgust: float = 1.0,  # ← NEW
    sentiment_boredom: float = 1.0,
    current_state: str = "greeting"
) -> Tuple[ResponseMode, str]:
    """Decide response mode based on INTENT + SENTIMENT."""

    # Rule 1: Intent overrides sentiment
    if intent == "pricing":
        return (ResponseMode.TEMPLATE_ONLY, "pricing")
    elif intent == "catalog":
        return (ResponseMode.TEMPLATE_ONLY, "catalog")
    elif intent == "booking":
        return (ResponseMode.TEMPLATE_ONLY, "plans")
    elif intent == "complaint":
        return (ResponseMode.LLM_ONLY, "")  # Escalate via orchestrator
    elif intent == "general_inquiry":
        return (ResponseMode.LLM_ONLY, "")  # Never push templates

    # Rule 2: For small_talk & reschedule, use sentiment
    if sentiment_anger > 6.0 or sentiment_disgust > 6.0:
        return (ResponseMode.LLM_ONLY, "")  # Don't push templates to angry/disgusted

    if sentiment_boredom > 7.0:
        return (ResponseMode.LLM_ONLY, "")  # Don't bore them further

    # Default
    return (ResponseMode.LLM_THEN_TEMPLATE, "catalog")
```

---

### E. `chatbot_orchestrator.py` - Integrate Intent Classifier

**Add intent classification before template decision:**

```python
def process_message(self, conversation_id: str, user_message: str, current_state: ConversationState):
    # ... existing code ...

    # 2a. Classify intent ← NEW
    intent = self._classify_intent(history, user_message)

    # 2b. Analyze sentiment (existing)
    sentiment = self.sentiment_service.analyze(history, user_message)

    # 3. Decide response mode using BOTH intent + sentiment ← UPDATED
    response_mode, template_key = self.template_manager.decide_response_mode(
        user_message=user_message,
        intent=intent.intent_class,  # ← NEW
        sentiment_interest=sentiment.interest if sentiment else 5.0,
        sentiment_anger=sentiment.anger if sentiment else 1.0,
        sentiment_disgust=sentiment.disgust if sentiment else 1.0,  # ← NEW
        sentiment_boredom=sentiment.boredom if sentiment else 1.0,
        current_state=current_state.value
    )

    # ... rest of code ...

def _classify_intent(self, history: dspy.History, user_message: str) -> ValidatedIntent:
    """Classify what the customer wants (pricing, booking, complaint, etc.)"""
    from modules import IntentClassifier

    try:
        classifier = IntentClassifier()
        result = classifier(
            conversation_history=history,
            current_message=user_message
        )
        return ValidatedIntent(
            intent_class=result.intent_class,
            confidence=0.8,  # DSPy confidence
            reasoning=result.reasoning,
            metadata=ExtractionMetadata(...)
        )
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}, defaulting to general_inquiry")
        return ValidatedIntent(
            intent_class="general_inquiry",
            confidence=0.0,
            reasoning="Failed to classify",
            metadata=ExtractionMetadata(...)
        )
```

---

### F. `conversation_simulator.py` - Display All 5 Sentiments

**Update line 147:**
```python
# Old:
f"Interest={sentiment.get('interest')} Anger={sentiment.get('anger')} Boredom={sentiment.get('boredom')}"

# New:
f"Interest={sentiment.get('interest')} Anger={sentiment.get('anger')} Disgust={sentiment.get('disgust')} Boredom={sentiment.get('boredom')} Neutral={sentiment.get('neutral')}"
```

---

## 6. Example Flows After Implementation

### Flow 1: Pricing Inquiry (Current Problem Case)
```
Customer: "What do you charge?"
↓
Intent Classifier: intent="pricing" (confidence=0.95)
Sentiment: interest=5, anger=1, disgust=1, boredom=2, neutral=1
↓
decide_response_mode() logic:
  if intent == "pricing":
    return (ResponseMode.TEMPLATE_ONLY, "pricing")  ✓
↓
Response: Shows pricing template ONLY, no verbose LLM chatter
```

### Flow 2: General Inquiry
```
Customer: "How does the process work?"
↓
Intent Classifier: intent="general_inquiry" (confidence=0.92)
Sentiment: interest=7, anger=1, disgust=1, boredom=1, neutral=1
↓
decide_response_mode() logic:
  if intent == "general_inquiry":
    return (ResponseMode.LLM_ONLY, "")  ✓
↓
Response: Brief LLM explanation, NO template pushed
```

### Flow 3: Complaint with Escalation
```
Customer: "Washed yesterday, driver left a scratch!"
↓
Intent Classifier: intent="complaint" (confidence=0.98)
Sentiment: interest=1, anger=9, disgust=7, boredom=1, neutral=1
↓
decide_response_mode() logic:
  if intent == "complaint":
    return (ResponseMode.LLM_ONLY, "")
  # Then chatbot_orchestrator calls escalate_to_human()
↓
Response: Empathetic acknowledgment + "Transferring to specialist..."
```

---

## 7. Implementation Checklist

- [ ] Verify `IntentClassificationSignature` exists in signatures.py
- [ ] Verify `IntentClassifier` module exists in modules.py
- [ ] Add `ValidatedIntent` model to models.py
- [ ] Update `SentimentAnalysisSignature` to clarify all 5 dimensions
- [ ] Add `dominant_sentiment` property to `ValidatedSentimentScores`
- [ ] Update `template_manager.py` decision logic to use intent
- [ ] Update `chatbot_orchestrator.py` to classify intent
- [ ] Add `_classify_intent()` method to orchestrator
- [ ] Update `conversation_simulator.py` to display all 5 sentiment dimensions
- [ ] Add logging to track intent classifications
- [ ] Test with sample conversations

---

## 8. Hybrid Architecture: Intent × Stage × Sentiment (NEW)

### Strategic Design Decision

**Why Not Full Matrix (385+ combinations)?**
- 7 intents × 11 stages × 5 sentiment dimensions = 385+ possible combinations
- Would require 385+ signatures and modules
- Maintenance nightmare, poor learning efficiency
- Most combinations are illogical (e.g., "complaint" during "completion")

**Better Approach: Hybrid Three-Axis Model**

#### Axis 1: Intent-Specialized Response Modules (5-7 modules)
Each intent gets its own responder module with optimized signatures:
```python
class PricingResponder(dspy.Module):       # intent=pricing_inquiry
class CatalogResponder(dspy.Module):       # intent=catalog_request
class BookingResponder(dspy.Module):       # intent=booking_intent
class ComplaintResponder(dspy.Module):     # intent=complaint
class GeneralResponder(dspy.Module):       # intent=general_inquiry
class SmallTalkResponder(dspy.Module):     # intent=small_talk
class RescheduleResponder(dspy.Module):    # intent=reschedule
```

#### Axis 2: Stage-Aware Logic Within Each Responder
Each responder understands conversation flow:
```python
# Within PricingResponder:
def forward(self, stage, sentiment_context, user_message, history):
    if stage == "greeting":
        return self.show_intro_pricing(...)      # Initial pricing
    elif stage == "service_selection":
        return self.show_tier_prices(...)        # Tier-specific pricing
    elif stage == "confirmation":
        return self.show_final_price(...)        # Final breakdown

# Within BookingResponder:
def forward(self, stage, sentiment_context, user_message, history):
    if stage == "greeting":
        return self.initiate_booking(...)        # Welcome to booking
    elif stage == "name_collection":
        return self.collect_name(...)            # Ask for name
    elif stage == "vehicle_details":
        return self.collect_vehicle(...)         # Ask for vehicle
    # ... etc
```

#### Axis 3: Sentiment as Dynamic Tone (NOT a separate axis)
Sentiment adjusts **how** responses are delivered, not **which** module to use:
```python
# Same responder, different tone based on sentiment
sentiment_context = f"anger={sentiment.anger}, interest={sentiment.interest}, disgust={sentiment.disgust}"

signature = PriceExplanationSignature:
    sentiment_context: dspy.InputField(desc="Customer's emotional state")
    user_message: dspy.InputField()
    conversation_history: dspy.History

    response: dspy.OutputField(desc="Tone-adjusted price explanation")
    # LLM adapts tone based on sentiment_context:
    # - High anger: Empathetic, solution-focused
    # - High interest: Detailed, enthusiastic
    # - High disgust: Direct, facts-only
```

### Comparison: Complexity vs Control

| Aspect | Full Matrix | Hybrid Approach | Current Single |
|--------|-------------|-----------------|-----------------|
| Modules | 385+ | 5-7 | 1 |
| Signatures | 385+ | 5-7 | 1 |
| Control granularity | Per combination | Per intent | Global |
| Tunability | Very high | High | Low |
| Maintainability | Nightmare | Manageable | Easy |
| Learning efficiency | Poor | Good | Baseline |
| DSPy alignment | Overkill | ✓ Matches tutorial | Too monolithic |

### Implementation Phasing

**PHASE 1 (Current - MVP):**
- Add intent detection (single-module approach from INTENT_AND_STAGES_PLAN.md sections 1-7)
- Keep current single EmpathyResponseGenerator
- But **accept intent as a parameter** in decision logic
- Goal: Fix "always pushing catalog" bug quickly
- Metrics: Template push rate drops from 100% to ~30%

**PHASE 2 (After Phase 1 Works):**
- Refactor into intent-specialized responders (PricingResponder, BookingResponder, etc.)
- Each responder gets optimized signatures for that intent/stage combination
- Sentiment becomes a parameter passed to LLM modules, not a branching decision
- Goal: Improve response quality, enable per-intent tuning
- Metrics: Intent classification accuracy, response relevance, CSAT

### Why This Ordering?

1. **Phase 1 is low-risk**: Reuses existing architecture, just adds intent detection layer
2. **Phase 1 solves immediate problem**: Users see improvement quickly
3. **Phase 2 is data-driven**: After Phase 1, we have real conversation logs to validate which intent-stage combinations actually occur
4. **Phase 2 is incremental**: Can refactor one responder at a time without breaking others

### File Organization for Phase 2

```
@example/
├── modules.py                    # Core extraction + base responders
├── responders/                   # NEW FOLDER (Phase 2)
│   ├── __init__.py
│   ├── base_responder.py        # Abstract responder class
│   ├── pricing_responder.py
│   ├── booking_responder.py
│   ├── complaint_responder.py
│   └── general_responder.py
├── signatures.py                 # All signatures (base + responder-specific)
└── responder_factory.py          # NEW: Returns right responder for intent
```

---

## 9. Success Metrics

After implementation, measure:
- Template push rate: Should be ~30% (not 100% as now)
- Intent classification accuracy: Target 90%+
- Customer satisfaction (CSAT): Track improvement
- Escalation rate: Complaints should trigger escalation 100%
- Sentiment distribution: All 5 dimensions tracked

