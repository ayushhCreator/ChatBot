# Sentiment-Aware Response Generation - DSPy Pipeline

## What Was Fixed

Your system was detecting sentiment and intent perfectly, but **NOT using this data to control the LLM's response tone and length**. This meant:

- Angry customers got the same helpful, lengthy responses as interested ones
- System consumed more tokens/LLM calls than necessary
- Responses didn't match the customer's emotional state

---

## The DSPy Way (Not F-strings)

Instead of hardcoded f-string prompts like:
```python
# ❌ WRONG: Brittle, not optimizable
prompt = f"Customer is VERY ANGRY (anger=8/10) about prices..."
```

We now use **composable DSPy signatures and modules** that:
- Break the problem into smaller steps
- Are independently optimizable by DSPy optimizers
- Allow future training/fine-tuning
- Scale with more dimensions

---

## New Architecture

### 1. **SentimentToneSignature** (signatures.py:103-130)

Takes individual sentiment scores and determines appropriate tone + brevity:

```python
class SentimentToneSignature(dspy.Signature):
    """Determine appropriate tone and brevity based on sentiment scores."""

    # Inputs: Raw sentiment scores
    interest_score = dspy.InputField(desc="Customer interest level (1-10)")
    anger_score = dspy.InputField(desc="Customer anger level (1-10)")
    disgust_score = dspy.InputField(desc="Customer disgust level (1-10)")
    boredom_score = dspy.InputField(desc="Customer boredom level (1-10)")
    neutral_score = dspy.InputField(desc="Customer neutral level (1-10)")

    # Outputs: High-level directives
    tone_directive = dspy.OutputField(
        desc="Tone instruction (e.g., 'direct and brief', 'engaging and conversational')"
    )
    max_sentences = dspy.OutputField(desc="Maximum number of sentences (1-4)")
    reasoning = dspy.OutputField(desc="Why this tone and length")
```

**Why this works:**
- LLM analyzes the sentiment combination and outputs a concise directive
- This directive becomes the **instruction** for the next step
- Future DSPy optimizers can train on this step independently

---

### 2. **ToneAwareResponseSignature** (signatures.py:133-154)

Takes the tone directive and generates a response respecting it:

```python
class ToneAwareResponseSignature(dspy.Signature):
    """Generate response adapted to tone and brevity constraints."""

    # Inputs: Context + tone constraint
    conversation_history: dspy.History = dspy.InputField(...)
    user_message = dspy.InputField(...)
    tone_directive = dspy.InputField(desc="Tone instruction from SentimentToneAnalyzer")
    max_sentences = dspy.InputField(desc="Maximum number of sentences to use")
    current_state = dspy.InputField(...)

    # Output: Constrained response
    response = dspy.OutputField(
        desc="Concise, tone-appropriate response within sentence limit"
    )
```

**Why this works:**
- The tone directive and sentence limit are **explicit constraints**
- LLM must respect them (good models do this well)
- Response length is controlled by design, not hope

---

### 3. **SentimentToneAnalyzer Module** (modules.py:119-141)

```python
class SentimentToneAnalyzer(dspy.Module):
    """Analyze sentiment scores and determine appropriate tone and brevity."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SentimentToneSignature)

    def forward(self, interest_score=5.0, anger_score=1.0, ...):
        """Determine tone and brevity based on sentiment scores."""
        return self.predictor(
            interest_score=str(interest_score),
            anger_score=str(anger_score),
            ...
        )
```

**Maps sentiment scores → tone decisions** through LLM reasoning.

---

### 4. **ToneAwareResponseGenerator Module** (modules.py:144-167)

```python
class ToneAwareResponseGenerator(dspy.Module):
    """Generate concise, tone-appropriate responses respecting brevity constraints."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(ToneAwareResponseSignature)

    def forward(self, conversation_history=None, user_message="",
                tone_directive="be helpful", max_sentences="3", ...):
        """Generate response adapted to tone and sentence limit."""
        return self.predictor(...)
```

**Generates response respecting the tone directive and sentence limit.**

---

## The Pipeline in Action

### Before (Old Way)
```
User message "That's too much" [angry, anger=8.0]
    ↓
SentimentAnalyzer: anger=8.0
    ↓
EmpathyResponseGenerator (ignores sentiment directive):
    → Generates 3-4 sentences of helpful advice
    → NOT adapted to anger level
    → "I understand why you might feel that way..."
```

### After (DSPy Way)
```
User message "That's too much" [angry, anger=8.0]
    ↓
SentimentAnalyzer: anger=8.0
    ↓
SentimentToneAnalyzer:
    Input: anger=8.0
    Output: {
        tone_directive: "Direct, solution-focused, brief",
        max_sentences: "2",
        reasoning: "High anger detected - skip pleasantries"
    }
    ↓
ToneAwareResponseGenerator:
    Input: tone_directive="Direct, solution-focused, brief"
            max_sentences="2"
    Output: "Our cheapest plan is ₹299. Would that work for you?"
```

**Result:** 1 sentence instead of 4, saves tokens, addresses emotion.

---

## Implementation in chatbot_orchestrator.py

Updated `_generate_empathetic_response()` (lines 199-247):

```python
def _generate_empathetic_response(self, ...):
    """Generate empathetic LLM response using DSPy pipeline."""

    # Step 1: Analyze sentiment → determine tone + brevity
    tone_analyzer = SentimentToneAnalyzer()
    tone_result = tone_analyzer(
        interest_score=sentiment.interest,
        anger_score=sentiment.anger,
        disgust_score=sentiment.disgust,
        boredom_score=sentiment.boredom,
        neutral_score=sentiment.neutral
    )

    # Step 2: Generate response respecting tone + brevity
    response_generator = ToneAwareResponseGenerator()
    result = response_generator(
        conversation_history=history,
        user_message=user_message,
        tone_directive=tone_result.tone_directive,      # ← From Step 1
        max_sentences=tone_result.max_sentences,        # ← From Step 1
        current_state=current_state.value
    )

    return result.response
```

---

## Why This Is Better Than F-Strings

| Aspect | F-String Approach | DSPy Signature Approach |
|--------|---|---|
| **Flexibility** | Hardcoded template | LLM decides tone dynamically |
| **Optimizable** | No | Yes (DSPy optimizers) |
| **Composable** | Single monolithic prompt | Two separate signatures |
| **Token Efficient** | Large prompts | Smaller, focused prompts |
| **Future Training** | Requires rewrite | Can fine-tune each signature |
| **Reasoning Visible** | Hidden in prompt | `tone_result.reasoning` logged |
| **Scalability** | Brittle | Elegant |

---

## Sentiment → Tone Mapping (What LLM Learns)

The `SentimentToneSignature` teaches the LLM patterns like:

- **anger > 6.0**
  - Tone: "Direct, solution-focused, brief"
  - Max sentences: 2
  - Example: "₹299 is our cheapest option. Interested?"

- **disgust > 6.0**
  - Tone: "Apologetic, action-oriented, quick"
  - Max sentences: 3
  - Example: "I apologize for the issue. Here's the immediate fix..."

- **boredom > 7.0**
  - Tone: "Engaging, conversational, concise"
  - Max sentences: 3
  - Example: "Here's a cool feature you might love—limited time only!"

- **interest > 7.0**
  - Tone: "Enthusiastic, detailed, helpful"
  - Max sentences: 4
  - Example: "Our premium option includes X, Y, Z. Want to know more about...?"

- **neutral (default)**
  - Tone: "Professional, helpful, clear"
  - Max sentences: 3
  - Example: "Here are your options. What would you prefer?"

---

## What Gets Logged

Now you'll see in DEBUG logs:

```
🎯 TONE ANALYSIS: tone='Direct, solution-focused, brief' max_sentences=2
```

This lets you verify the system is actually making tone decisions.

---

## Future Optimization Possibilities

With this DSPy structure, you can later:

1. **Train optimizers on sentiment tone mapping**
   ```python
   optimizer = dspy.BootstrapFewShotWithRandomSearch(metric=response_quality)
   optimizer.compile(SentimentToneAnalyzer(), ...)
   ```

2. **Add more sentiment-based variations** (e.g., context-specific tone for each state)

3. **Fine-tune the sentence limit** based on actual response quality metrics

4. **Chain multiple modules** (sentiment → tone → response → review)

---

## Files Modified

- `signatures.py`: Added `SentimentToneSignature` + `ToneAwareResponseSignature`
- `modules.py`: Added `SentimentToneAnalyzer` + `ToneAwareResponseGenerator`
- `chatbot_orchestrator.py`: Updated `_generate_empathetic_response()` to use the DSPy pipeline

---

## Testing Next Steps

1. Run conversation simulator
2. Check that angry customer responses are 1-2 sentences
3. Check that interested customers get 3-4 sentences
4. Verify LLM tokens are lower than before
5. Check DEBUG logs for `🎯 TONE ANALYSIS` messages

---

## Key Insight

**Sentiment detection → Tone determination → Constrained generation**

This is a **composable pipeline** that scales. Each step:
- Is independently understandable
- Can be tested in isolation
- Can be optimized separately
- Can be extended with new dimensions

The f-string approach bundles this all into a single prompt. The DSPy approach breaks it into manageable pieces that can evolve with your system.
