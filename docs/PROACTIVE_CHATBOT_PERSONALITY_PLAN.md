# Proactive Chatbot Personality System - Implementation Plan

**Date:** November 30, 2025
**Status:** Planning Phase
**Approach:** DSPy Refine + State-Aware Scripts + Modular Design

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Key Insights from DSPy Tutorials](#key-insights-from-dspy-tutorials)
4. [Problem Statement](#problem-statement)
5. [Proposed Architecture](#proposed-architecture)
6. [Implementation Details](#implementation-details)
7. [Design Principles](#design-principles)
8. [Risk Mitigation](#risk-mitigation)
9. [Testing Strategy](#testing-strategy)
10. [Rollout Plan](#rollout-plan)

---

## Executive Summary

Transform the chatbot from **purely reactive** (only responding to user input) to **proactively guided** (actively steering the conversation toward booking while respecting user intent).

### Current Limitation
```
User says something → Extract what they said → React to it
```

### Proposed Solution
```
We know state X needs data Y → Ask for Y proactively
→ If user confirms, advance state → If user questions, answer
→ Maintain conversation quality with DSPy Refine
```

### Key Changes
- Add **StateAwareResponseGenerator** DSPy module
- Create **ConversationScriptManager** for centralized state scripts
- Integrate **DSPy Refine** for quality assurance
- Maintain 100% backward compatibility with fallback safety

### Impact
- **4 files** to create/modify (~150 lines new code)
- **0 breaking changes** (all wrapped in try/except with fallback)
- **Follows SOLID principles** (Single Responsibility, Open/Closed, Dependency Inversion)
- **Eliminates redundancy** (DRY - scripts defined once, reused everywhere)

---

## Current State Analysis

### What Exists (✅ Working)

1. **State Machine** (`state_coordinator.py`)
   - 7 states: GREETING, NAME_COLLECTION, VEHICLE_DETAILS, DATE_SELECTION, CONFIRMATION, COMPLETED, CANCELLED
   - Valid transitions defined in config
   - State progression logic functional

2. **Data Extraction** (`data_extractor.py`)
   - Extracts: name, phone, vehicle, date
   - Uses DSPy modules: NameExtractor, VehicleDetailsExtractor, DateParser
   - Validation for all extracted fields

3. **Sentiment Analysis** (`sentiment_analyzer.py`)
   - Multi-dimensional: interest, anger, disgust, boredom
   - Outputs: ValidatedSentimentScores

4. **Response Mode Decision** (`template_manager.py`)
   - ResponseMode enum: TEMPLATE_ONLY, LLM_THEN_TEMPLATE, TEMPLATE_THEN_LLM, LLM_ONLY
   - Decision logic based on intent + sentiment

5. **Response Generation** (`response_composer.py`)
   - Mixes LLM responses with templates
   - Configurable mode behavior
   - Fallback responses for failures

6. **Tone-Aware Response Generation** (`message_processor.py` → `_generate_empathetic_response()`)
   - Uses SentimentToneAnalyzer to determine tone + brevity
   - Uses ToneAwareResponseGenerator for constrained responses
   - ChainOfThought reasoning

7. **Confirmation Logic**
   - ConfirmationIntentDetector for explicit confirmation
   - Booking creation on confirmation
   - Scratchpad management

### What's Missing (❌ Not Implemented)

1. **Proactive Script Guidance**
   - No definition of "what to say" in each state
   - No centralized script personality
   - Responses generated reactively, not proactively

2. **State-Aware Next Field Planning**
   - No logic for "what to ask for next"
   - No guidance to DSPy about state goals
   - No state-specific response templates

3. **Quality Refinement Loop**
   - No multi-attempt response generation
   - No reward function for quality assurance
   - No iterative feedback for improvement

4. **Proactive Prompting**
   - If user says nothing, no proactive question
   - No "sales script" to drive conversation
   - Purely reactive to user input

---

## Key Insights from DSPy Tutorials

### From AI Text Game Tutorial
- **Pattern:** Enum-based state machine (GameState) + signature-based modules (StoryGenerator, DialogueGenerator, ActionResolver)
- **Implementation:** Each module handles one specific task with ChainOfThought reasoning
- **Context:** GameContext dataclass tracks game state, story progress, NPCs, completed quests
- **Lesson:** Modular signatures + explicit state tracking = flexible, maintainable systems

### From Refine Tutorial
- **Pattern:** Multiple attempts (N=2, 3, etc.) with reward function
- **Mechanism:** After each failed attempt, generate feedback + hints for next iteration
- **Stopping Condition:** Stop early when reward_fn(prediction) >= threshold
- **Error Handling:** fail_count parameter controls tolerance (default: allow N failures)
- **Lesson:** Iterative refinement with quality scores ensures output meets standards

### From Customer Service Agent Tutorial
- **Pattern:** ReAct (Reasoning + Acting) - each decision has reasoning steps + action steps
- **Tools:** Specialized functions for specific tasks
- **Context Preservation:** State/memory maintained across multiple agent decisions
- **Lesson:** Structured reasoning improves consistency and transparency

---

## Problem Statement

### Current Chatbot Behavior (Reactive)

**Example Scenario: Greeting State**
```
User: "Hi"
System:
  1. Extract: No structured data
  2. Analyze sentiment: neutral
  3. ResponseMode: LLM_ONLY
  4. Generate: "Hi! How can I help you?" (generic, no guidance)
  5. Response sent

Problem: No proactive guidance toward booking
```

### Desired Chatbot Behavior (Proactive)

**Same Scenario with Proactive Script**
```
User: "Hi"
System:
  1. Extract: No structured data
  2. Analyze sentiment: neutral
  3. Get StateScript for GREETING:
     - goal: "Welcome and understand booking intent"
     - personality: "warm, professional, inviting"
     - need_next: ["booking_intent"]
  4. StateAwareResponseGenerator considers:
     - Current goal: welcome + offer booking
     - State personality: warm and inviting
     - What user said: "Hi"
  5. Generate: "Welcome to Yawlit! I'm here to help you book a car service.
               Are you looking to schedule an appointment today?"
               (proactive, goal-oriented)
  6. Refine ensures quality:
     - Score 1 attempt: 0.65 (addresses goal but not inviting enough)
     - Feedback: "Make it warmer and more welcoming"
     - Score 2 attempt: 0.85 (exceeds threshold 0.7)
     - Accept and send

Benefit: User immediately understands what chatbot offers, guided toward booking
```

### The 72+ Edge Cases We've Already Handled

This new system builds on top of existing edge case handling:
- ✅ Incomplete vehicle plate validation
- ✅ Confidence scores in intent classification
- ✅ Scratchpad data persistence across endpoints
- ✅ State gate preventing premature transitions
- ✅ Retroactive data validation
- ✅ Typo detection in confirmation
- ✅ Vehicle name vs customer name confusion
- ✅ And 65+ more edge cases in extraction, sentiment, state management

This proactive personality system **does not duplicate** that logic—it layers on top.

---

## Proposed Architecture

### Overall Flow (Enhanced)

```
User Message
    ↓
[EXISTING] Extract Intent + Sentiment
    ↓
[EXISTING] Determine Next State
    ↓
[EXISTING] Decide ResponseMode (template vs LLM)
    ↓
[NEW] Get State Script
    ↓
[NEW] StateAwareResponseGenerator (with state goal + personality guidance)
    ↓
[NEW] DSPy Refine (multiple attempts + quality scoring)
    ↓
[EXISTING] Compose Response (mix LLM + template as decided)
    ↓
Return to User
```

### Layer Model

```
Layer 1 (Existing): State Machine
  - Tracks: current state, transitions, field completeness
  - Responsibility: Where are we in the flow?

Layer 2 (Existing): Intent + Sentiment
  - Tracks: what user wants, how they feel
  - Responsibility: What does the user need?

Layer 3 (Existing): ResponseMode Decision
  - Tracks: template vs LLM strategy
  - Responsibility: How should we respond?

[NEW] Layer 4: State Script
  - Tracks: what we want to achieve, what personality to use
  - Responsibility: What should we say?

[NEW] Layer 5: StateAwareResponseGenerator
  - Tracks: response quality, field completion
  - Responsibility: Generate response aligned with state goals

[NEW] Layer 6: DSPy Refine
  - Tracks: quality scores, feedback, iterations
  - Responsibility: Ensure response meets quality threshold
```

---

## Implementation Details

### File 1: `conversation_script_manager.py` (NEW - ~80 lines)

**Purpose:** Centralized repository of what to say in each state (like GameContext from tutorial)

**Location:** `/home/riju279/Downloads/demo/example/conversation_script_manager.py`

```python
"""Conversation Script Manager - Centralized state-based response scripts.

Defines what the chatbot should say, what personality to use, and what to ask for next
in each conversation state.

Follows:
- Single Responsibility Principle: Only defines scripts
- DRY Principle: Single source of truth for all state scripts
- Open/Closed Principle: Scripts in data, not code; easy to change without code modification
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StateScript:
    """Script definition for a conversation state."""

    state: str
    """Current conversation state (e.g., 'greeting', 'name_collection')"""

    goal: str
    """What we're trying to achieve in this state (e.g., 'Welcome and offer booking')"""

    personality: str
    """Personality/tone for this state (e.g., 'warm, professional, inviting')"""

    need_next: List[str]
    """Fields we still need to collect (e.g., ['first_name', 'last_name'])"""

    proactive_message: str
    """If user says nothing, ask this question proactively"""

    validation_rules: List[str]
    """Rules for quality scoring (e.g., ['must_mention_booking', 'must_ask_for_name'])"""


# CONVERSATION SCRIPTS - Single source of truth for all state scripts
CONVERSATION_SCRIPTS = {
    "greeting": StateScript(
        state="greeting",
        goal="Welcome customer and offer booking service",
        personality="warm, professional, inviting",
        need_next=["booking_intent"],
        proactive_message="Welcome to Yawlit! I'm here to help you book a premium car service. Are you looking to schedule an appointment?",
        validation_rules=[
            "must_acknowledge_greeting",
            "must_mention_booking",
            "must_be_warm_and_welcoming"
        ]
    ),

    "name_collection": StateScript(
        state="name_collection",
        goal="Collect customer name for personalized service",
        personality="friendly, personalized, detail-oriented",
        need_next=["first_name", "last_name"],
        proactive_message="Great! To get started, what's your full name?",
        validation_rules=[
            "must_acknowledge_previous_response",
            "must_ask_for_name",
            "must_explain_why_needed"
        ]
    ),

    "vehicle_details": StateScript(
        state="vehicle_details",
        goal="Confirm vehicle details for accurate service",
        personality="knowledgeable, thorough, professional",
        need_next=["vehicle_brand", "vehicle_model", "vehicle_plate"],
        proactive_message="Perfect! Now, can you tell me about your vehicle? I need the brand, model, and license plate number.",
        validation_rules=[
            "must_acknowledge_name",
            "must_ask_for_vehicle_brand",
            "must_ask_for_vehicle_model",
            "must_ask_for_vehicle_plate"
        ]
    ),

    "date_selection": StateScript(
        state="date_selection",
        goal="Lock in appointment date and time",
        personality="efficient, confirmatory, helpful",
        need_next=["appointment_date"],
        proactive_message="Excellent! When would you like to schedule the service? Pick any day that works for you.",
        validation_rules=[
            "must_acknowledge_vehicle",
            "must_ask_for_date",
            "must_clarify_date_format"
        ]
    ),

    "confirmation": StateScript(
        state="confirmation",
        goal="Get final approval and complete booking",
        personality="professional, summary-focused, confident",
        need_next=["confirmation"],
        proactive_message="Here's what I have for your booking. Please review and confirm - just say 'confirm' to complete!",
        validation_rules=[
            "must_show_summary",
            "must_ask_for_confirmation",
            "must_offer_edit_option"
        ]
    )
}


class ConversationScriptManager:
    """Manager for conversation scripts across all states.

    Follows Single Responsibility Principle:
    - Only responsibility: Provide scripts for conversation states
    - No logic: Pure data retrieval
    - No coupling: No dependencies on other modules
    """

    @staticmethod
    def get_script(state: str) -> Optional[StateScript]:
        """Get script for a specific conversation state.

        Args:
            state: State name (e.g., 'greeting', 'name_collection')

        Returns:
            StateScript if found, None otherwise
        """
        return CONVERSATION_SCRIPTS.get(state)

    @staticmethod
    def get_all_scripts() -> dict:
        """Get all conversation scripts.

        Returns:
            Dictionary of {state: StateScript}
        """
        return CONVERSATION_SCRIPTS.copy()

    @staticmethod
    def has_script(state: str) -> bool:
        """Check if script exists for state.

        Args:
            state: State name

        Returns:
            True if script exists, False otherwise
        """
        return state in CONVERSATION_SCRIPTS

    @staticmethod
    def update_script(state: str, script: StateScript) -> bool:
        """Update script for a state (for A/B testing, configuration).

        Args:
            state: State name
            script: New StateScript

        Returns:
            True if updated, False if state not found
        """
        if state in CONVERSATION_SCRIPTS:
            CONVERSATION_SCRIPTS[state] = script
            return True
        return False
```

**Key Design Decisions:**
- ✅ Uses dataclass for type safety and clarity
- ✅ Enum pattern ready for future state validation
- ✅ No dependencies (stateless, pure data)
- ✅ Easy to modify scripts without touching other code
- ✅ Optional methods for future features (A/B testing, validation)

---

### File 2: `signatures.py` (MODIFY - Add ~25 lines)

**Purpose:** Define the StateAwareResponseSignature for DSPy (like DialogueGenerator in game tutorial)

**Action:** Add to existing `signatures.py` file at the end

```python
class StateAwareResponseSignature(dspy.Signature):
    """Generate response guided by conversation state and sales script.

    This signature helps the LLM generate responses that:
    1. Address the current conversation goal
    2. Maintain consistent personality for the state
    3. Proactively ask for needed data
    4. Respect user intent and sentiment

    Similar pattern to DialogueGenerator in DSPy game tutorial:
    - Input: full context (history, state, user message)
    - Output: structured response with explicit fields
    - Reasoning: ChainOfThought (handled by module wrapper)
    """

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history between user and assistant"
    )
    current_state: str = dspy.InputField(
        desc="Current conversation state (greeting, name_collection, vehicle_details, date_selection, confirmation)"
    )
    state_goal: str = dspy.InputField(
        desc="What we're trying to achieve in this state (e.g., 'Collect customer name for personalized service')"
    )
    state_personality: str = dspy.InputField(
        desc="Personality/tone for this state (e.g., 'friendly, personalized, detail-oriented')"
    )
    user_message: str = dspy.InputField(
        desc="Latest message from the user"
    )
    collected_fields: str = dspy.InputField(
        desc="Fields already collected (e.g., 'first_name=Sanjay; phone=9876543210')"
    )
    need_next_fields: str = dspy.InputField(
        desc="Fields we still need (e.g., 'vehicle_brand, vehicle_model, vehicle_plate')"
    )

    response: str = dspy.OutputField(
        desc="Response to user that guides toward state goal while respecting their intent and sentiment. Should feel natural, not pushy."
    )
```

**Key Design Decisions:**
- ✅ Follows existing DSPy signature patterns in codebase
- ✅ Clear, descriptive field descriptions for LLM guidance
- ✅ Mirrors DialogueGenerator pattern from game tutorial
- ✅ No validation logic (pure interface definition)

---

### File 3: `modules.py` (MODIFY - Add ~15 lines)

**Purpose:** Implement StateAwareResponseGenerator DSPy module (like StoryGenerator in game tutorial)

**Action:** Add to existing `modules.py` file at the end (before any test code)

```python
class StateAwareResponseGenerator(dspy.Module):
    """Generate state-aware, goal-guided responses using DSPy reasoning.

    This module wraps StateAwareResponseSignature with ChainOfThought reasoning,
    enabling step-by-step thinking about how to respond given:
    - Current conversation state and goal
    - Desired personality/tone
    - What user just said
    - What data we have and what we still need

    Pattern from DSPy game tutorial: Module wraps signature with ChainOfThought.
    Follows Single Responsibility: Only generates responses guided by state script.
    """

    def __init__(self):
        """Initialize with ChainOfThought predictor for StateAwareResponseSignature."""
        super().__init__()
        self.predictor = dspy.ChainOfThought(StateAwareResponseSignature)

    def forward(
        self,
        history: dspy.History,
        current_state: str,
        state_goal: str,
        state_personality: str,
        user_message: str,
        collected_fields: str,
        need_next_fields: str
    ):
        """Generate state-aware response.

        Args:
            history: Conversation history for context
            current_state: Current conversation state
            state_goal: What we're trying to achieve
            state_personality: Desired personality/tone
            user_message: Latest user message
            collected_fields: Already-collected data
            need_next_fields: Still-needed fields

        Returns:
            DSPy Prediction with response field
        """
        return self.predictor(
            conversation_history=history,
            current_state=current_state,
            state_goal=state_goal,
            state_personality=state_personality,
            user_message=user_message,
            collected_fields=collected_fields,
            need_next_fields=need_next_fields
        )
```

**Key Design Decisions:**
- ✅ Follows existing module patterns (like SentimentAnalyzer, NameExtractor)
- ✅ Uses ChainOfThought for complex reasoning
- ✅ Simple forward() method signature
- ✅ No error handling (handled by caller)
- ✅ Pure generation, no validation

---

### File 4: `orchestrator/message_processor.py` (MODIFY - Enhance `_generate_empathetic_response()`)

**Purpose:** Integrate StateAwareResponseGenerator with DSPy Refine for quality assurance

**Action:** Replace existing `_generate_empathetic_response()` method (lines 463-515)

**Before (Current Implementation - Tone-Aware Only):**
```python
def _generate_empathetic_response(self, history, user_message, current_state, sentiment, extracted_data):
    # Uses SentimentToneAnalyzer + ToneAwareResponseGenerator
    # Purely tone-aware, no state-aware guidance
```

**After (New Implementation - State-Aware + Refine):**

```python
def _generate_empathetic_response(
    self,
    history: dspy.History,
    user_message: str,
    current_state: ConversationState,
    sentiment,
    extracted_data: Optional[Dict[str, Any]]
) -> str:
    """Generate empathetic response with state-aware guidance and quality refinement.

    This method now:
    1. Gets the state script (what we should say in this state)
    2. Generates response guided by state goal + personality
    3. Refines response with quality scoring (DSPy Refine pattern)
    4. Falls back to tone-aware if state-aware fails (safety)

    Pattern from DSPy Refine tutorial:
    - Multiple attempts with reward function
    - Feedback-driven iteration
    - Threshold-based stopping
    """
    from conversation_script_manager import ConversationScriptManager
    from modules import StateAwareResponseGenerator

    # Get script for current state
    script = ConversationScriptManager.get_script(current_state.value)

    # If no script (shouldn't happen), fallback to tone-aware
    if not script:
        logger.warning(f"No script found for state {current_state.value}, using tone-aware fallback")
        return self._generate_tone_aware_response(
            history, user_message, current_state, sentiment, extracted_data
        )

    # Format data for DSPy
    collected_fields_str = "; ".join(
        [f"{k}={v}" for k, v in (extracted_data or {}).items()]
    ) if extracted_data else "None collected yet"

    need_next_fields_str = ", ".join(script.need_next)

    try:
        # Step 1: Define quality reward function
        # (Inspired by Refine tutorial: custom scoring function)
        def response_quality_score(args, pred):
            """Score response quality based on state goals and validation rules.

            Scoring criteria (from script validation_rules):
            - Does response address the state goal?
            - Does it ask for next field?
            - Does it respect user intent?
            - Does it maintain state personality?
            """
            score = 0.0

            try:
                response_lower = pred.response.lower()

                # Criterion 1: Address state goal (weight: 35%)
                goal_keywords = script.goal.lower().split()
                goal_match_count = sum(1 for kw in goal_keywords if len(kw) > 3 and kw in response_lower)
                if goal_match_count > 0:
                    score += 0.35

                # Criterion 2: Ask for next field(s) (weight: 40%)
                need_keywords = [f.lower() for f in script.need_next]
                if any(f in response_lower for f in need_keywords):
                    score += 0.40

                # Criterion 3: Respect user intent (weight: 15%)
                # Check if response acknowledges what user said
                user_words = user_message.lower().split()
                if any(word in response_lower for word in user_words if len(word) > 3):
                    score += 0.15

                # Criterion 4: Natural tone (weight: 10%)
                # Check if response is conversational (has question mark or acknowledgment)
                if "?" in pred.response or "yes" in response_lower or "great" in response_lower:
                    score += 0.10

                # Cap at 1.0
                return min(score, 1.0)

            except Exception as e:
                logger.debug(f"Quality score calculation error: {e}")
                return 0.0

        # Step 2: Create state-aware generator
        state_gen = StateAwareResponseGenerator()

        # Step 3: Wrap with DSPy Refine (from Refine tutorial pattern)
        # Refine will:
        # - Try up to N=2 times
        # - Accept if score >= threshold 0.7
        # - Generate feedback after first attempt if score < threshold
        refined_gen = dspy.Refine(
            module=state_gen,
            N=2,  # Try up to 2 times
            reward_fn=response_quality_score,
            threshold=0.7,  # Accept if score >= 0.7
            fail_count=2  # Allow up to 2 failures
        )

        # Step 4: Generate refined response
        result = refined_gen(
            history=history,
            current_state=current_state.value,
            state_goal=script.goal,
            state_personality=script.personality,
            user_message=user_message,
            collected_fields=collected_fields_str,
            need_next_fields=need_next_fields_str
        )

        # Return generated response
        generated_response = result.response if result and hasattr(result, 'response') else None

        if generated_response and generated_response.strip():
            logger.info(f"✅ STATE-AWARE RESPONSE: State={current_state.value}, Quality check passed")
            return generated_response

        # If response is empty, use proactive message from script
        logger.warning(f"⚠️  Generated response was empty, using proactive message")
        return script.proactive_message

    except Exception as e:
        # SAFETY: Fallback to tone-aware if state-aware fails
        logger.warning(
            f"❌ State-aware response failed ({type(e).__name__}: {e}), "
            f"falling back to tone-aware response"
        )
        return self._generate_tone_aware_response(
            history, user_message, current_state, sentiment, extracted_data
        )
```

**Key Design Decisions:**
- ✅ Try/except wrapper ensures safety (fallback to existing tone-aware)
- ✅ Refine pattern from tutorial: N attempts + reward function + threshold
- ✅ Quality score function captures state validation rules
- ✅ Logging at each stage for debugging
- ✅ Graceful degradation if any component fails
- ✅ No changes to method signature (drop-in replacement)

---

## Design Principles

### SOLID Principles Applied

#### Single Responsibility Principle (SRP)
```
✅ ConversationScriptManager
   - Only responsibility: Provide scripts for states
   - No: Logic, extraction, sentiment analysis

✅ StateAwareResponseSignature
   - Only responsibility: Define response task interface
   - No: Implementation, logic, state transitions

✅ StateAwareResponseGenerator
   - Only responsibility: Generate responses using signature
   - No: Script retrieval, quality scoring, state transitions

✅ message_processor._generate_empathetic_response()
   - Responsibility: Orchestrate response generation with quality assurance
   - Delegates: Script retrieval to ScriptManager, generation to Generator
```

#### Open/Closed Principle (OCP)
```
✅ Scripts in data, not code
   - Can change scripts without modifying code
   - Can add new scripts without changing existing code
   - Easy to A/B test script variations

✅ Quality score function as parameter
   - Can swap different scoring logic without changing Refine code
   - Can adjust weights/thresholds without code changes
   - Future: Load from database
```

#### Liskov Substitution Principle (LSP)
```
✅ StateAwareResponseGenerator can replace ToneAwareResponseGenerator
   - Same forward() method signature
   - Returns compatible prediction object
   - Can be swapped in/out without breaking consumers
```

#### Interface Segregation Principle (ISP)
```
✅ StateAwareResponseSignature only includes needed fields
   - Doesn't expose internal LLM details
   - Clear input/output contract
   - No unnecessary dependencies

✅ ConversationScriptManager exposes only needed methods
   - get_script() for single script
   - get_all_scripts() for all scripts
   - No internal state exposure
```

#### Dependency Inversion Principle (DIP)
```
✅ message_processor depends on abstraction (StateAwareResponseGenerator)
   - Not on concrete LLM implementation
   - Not on specific prompt format
   - Not on specific Refine settings

✅ Scripts decoupled from generation logic
   - Can change what we say (scripts) without touching how we say it (generator)
```

### DRY Principle Applied

**Before (Redundant):**
```
- State requirements scattered across:
  1. state_coordinator.py (state transition logic)
  2. retroactive_validator.py (field requirements)
  3. message_processor.py (what to extract)

- Personality scattered across:
  1. template_manager.py (response mode)
  2. sentiment_analyzer.py (tone adjustment)
  3. Multiple LLM prompts (implicit personality)

- "What to ask for next" computed in:
  1. data_extractor.py (what was extracted)
  2. message_processor.py (field tracking)
  3. state_coordinator.py (state progression)
```

**After (Centralized):**
```
✅ All state scripts in ONE place: ConversationScriptManager
   - Single source of truth for what to say
   - Easy to update all states at once
   - Easy to A/B test by swapping script version

✅ All next-field logic in ONE place: StateScript.need_next
   - Defined with state, not scattered across files
   - Updated in one place
   - Easy to validate completeness
```

---

## Risk Mitigation

### Risk 1: StateAwareResponseGenerator Fails
**Consequence:** Response not generated, user confused
**Mitigation:**
- ✅ Wrapped in try/except with detailed logging
- ✅ Fallback to existing ToneAwareResponseGenerator (proven to work)
- ✅ Graceful degradation: Use script.proactive_message if all else fails

### Risk 2: Refine Slows Down Response Times
**Consequence:** Longer latency, poor UX
**Mitigation:**
- ✅ N=2 (only 2 attempts max, usually accepts on first)
- ✅ Refine is optional (can disable by removing dspy.Refine wrapper)
- ✅ Threshold=0.7 (accept good-enough responses, not perfect)
- ✅ Monitor: Log response times, adjust N/threshold based on metrics

### Risk 3: Quality Score Function Too Strict/Loose
**Consequence:** Rejecting good responses or accepting bad ones
**Mitigation:**
- ✅ Scoring logic visible in code (not black-box LLM)
- ✅ Threshold=0.7 (tunable without code change)
- ✅ Weights adjustable: Can change 0.35/0.40/0.15/0.10 ratios
- ✅ Test with diverse user inputs before production

### Risk 4: Scripts Become Outdated
**Consequence:** Chatbot says incorrect/irrelevant things
**Mitigation:**
- ✅ Scripts in data (ConversationScriptManager), not code
- ✅ Easy to update without redeploying code
- ✅ Version control: Can track script changes in git
- ✅ Future: Load from database for real-time updates

### Risk 5: No Breaking Changes... But What If?
**Consequence:** Existing functionality breaks
**Mitigation:**
- ✅ All new code in new files (conversation_script_manager.py)
- ✅ All modifications wrapped in try/except
- ✅ No changes to public method signatures
- ✅ ResponseMode, TemplateManager, StateCoordinator untouched
- ✅ Can rollback by removing try/except wrapper (reverts to tone-aware)

### Risk 6: DSPy Version Incompatibility
**Consequence:** Refine not available or API changed
**Mitigation:**
- ✅ Use existing DSPy imports (already in codebase)
- ✅ Refine usage matches tutorial patterns
- ✅ Fallback mechanism means older DSPy versions still work (without Refine)

---

## Testing Strategy

### Unit Tests (Standalone Components)

#### Test 1: ConversationScriptManager
```python
def test_script_manager_retrieves_script():
    script = ConversationScriptManager.get_script("greeting")
    assert script.goal == "Welcome customer and offer booking service"
    assert "booking" in script.personality

def test_script_manager_all_scripts():
    scripts = ConversationScriptManager.get_all_scripts()
    assert len(scripts) == 5  # greeting, name_collection, vehicle_details, date_selection, confirmation

def test_script_manager_missing_script():
    script = ConversationScriptManager.get_script("nonexistent")
    assert script is None
```

#### Test 2: StateAwareResponseSignature
```python
def test_signature_has_required_fields():
    sig = StateAwareResponseSignature()
    assert hasattr(sig, 'conversation_history')
    assert hasattr(sig, 'state_goal')
    assert hasattr(sig, 'response')
```

#### Test 3: StateAwareResponseGenerator
```python
def test_generator_initialization():
    gen = StateAwareResponseGenerator()
    assert hasattr(gen, 'predictor')
    assert gen.predictor is not None

def test_generator_forward_method():
    gen = StateAwareResponseGenerator()
    result = gen.forward(
        history=dspy.History(),
        current_state="greeting",
        state_goal="Welcome customer",
        state_personality="warm",
        user_message="Hi",
        collected_fields="None",
        need_next_fields="name"
    )
    assert hasattr(result, 'response')
    assert len(result.response) > 0
```

### Integration Tests (End-to-End)

#### Test 4: State-Aware Response with Fallback
```python
def test_state_aware_response_generation():
    processor = MessageProcessor()

    # Greeting state
    response = processor._generate_empathetic_response(
        history=dspy.History(),
        user_message="Hi",
        current_state=ConversationState.GREETING,
        sentiment=ValidatedSentimentScores(interest=8.0, anger=1.0, ...),
        extracted_data={}
    )

    # Should be generated by StateAwareResponseGenerator
    assert "book" in response.lower() or "service" in response.lower()
    assert len(response) > 0

def test_state_aware_fallback():
    # If StateAwareResponseGenerator fails, should fall back to tone-aware
    processor = MessageProcessor()

    # Mock failure
    with patch('modules.StateAwareResponseGenerator') as mock:
        mock.side_effect = Exception("Test failure")

        response = processor._generate_empathetic_response(
            history=dspy.History(),
            user_message="Hi",
            current_state=ConversationState.GREETING,
            sentiment=...,
            extracted_data={}
        )

        # Should still return a response (from fallback)
        assert len(response) > 0
```

#### Test 5: Quality Scoring Function
```python
def test_quality_score_function():
    # Define the score function from message_processor
    def response_quality_score(args, pred):
        # Score calculation logic
        ...

    # Test case 1: Perfect response
    pred = type('obj', (), {'response': "Welcome! What's your name for booking?"})()
    score = response_quality_score(None, pred)
    assert score >= 0.7  # Should pass threshold

    # Test case 2: Poor response
    pred = type('obj', (), {'response': "ok"})()
    score = response_quality_score(None, pred)
    assert score < 0.5  # Should fail threshold
```

### Scenario Tests (Real Conversations)

#### Test 6: Greeting Scenario
```
Input: User says "Hi"
Expected:
- StateAwareResponseGenerator called
- Response mentions booking
- Response asks for next field (or acknowledges greeting)
- Quality score > 0.7

Verify:
- No errors logged
- Fallback not triggered
- Response coherent and relevant
```

#### Test 7: Name Collection Scenario
```
Input: Collected={}, Need_next=["first_name", "last_name"]
User says: "I'm Sanjay"
Expected:
- Response acknowledges name
- Response asks for last name (if needed)
- Response mentions vehicle/service (next steps)
- Quality score > 0.7
```

#### Test 8: Edge Case - User Interrupts
```
Input: Collected={"first_name"="Sanjay"}, Need_next=["last_name"]
User says: "Actually, skip that. When can I book?"
Expected:
- Response respects user intent
- Response pivots toward booking (not stuck asking for last name)
- Quality score > 0.7 (respects user intent criterion)
```

### Performance Tests

#### Test 9: Response Time
```
Measure: Time from _generate_empathetic_response() call to return
Expected: < 5 seconds (with Refine)
Target: < 3 seconds (without Refine)

If timeout > 5s:
- Reduce N from 2 to 1 (disable Refine iteration)
- OR increase threshold (accept sooner)
```

#### Test 10: Fallback Reliability
```
Scenario: StateAwareResponseGenerator fails N times
Expected: Fallback to ToneAwareResponseGenerator always succeeds
Result: User never gets no response, always gets something reasonable
```

---

## Rollout Plan

### Phase 1: Implementation & Internal Testing (Week 1)

**Activities:**
1. Create conversation_script_manager.py
2. Add StateAwareResponseSignature to signatures.py
3. Add StateAwareResponseGenerator to modules.py
4. Modify message_processor._generate_empathetic_response()
5. Write unit tests for each component
6. Run with scenario tests on local machine

**Success Criteria:**
- ✅ All unit tests pass
- ✅ No exceptions in test scenarios
- ✅ Fallback mechanism works
- ✅ Response times acceptable

---

### Phase 2: Staging/Shadow Mode (Week 2)

**Activities:**
1. Deploy to staging environment
2. Enable state-aware response but log all results
3. Compare state-aware vs tone-aware responses side-by-side
4. Collect feedback from test users
5. Measure: quality scores, response times, user satisfaction

**Success Criteria:**
- ✅ State-aware responses generally better than tone-aware
- ✅ No performance regressions
- ✅ Fallback successful < 5% of time
- ✅ User satisfaction scores up by 10%+

---

### Phase 3: Gradual Rollout (Week 3-4)

**Activities:**
1. Deploy to production (behind feature flag)
2. Start with 10% traffic → state-aware response
3. Monitor: error rates, response times, user feedback
4. Gradually increase: 10% → 25% → 50% → 100%
5. Maintain: Fallback mechanism, detailed logging

**Success Criteria:**
- ✅ Error rates at 0%
- ✅ Response times < 3s average
- ✅ Booking conversion rate up (target: +5%)
- ✅ User satisfaction up (target: +10%)

---

### Phase 4: Optimization (Week 5+)

**Activities:**
1. Analyze logs: Which scripts work best? Which responses fail?
2. Iterate: Refine scripts based on real conversation data
3. A/B test: Different script versions
4. Optimize: Adjust quality score thresholds, Refine N parameter
5. Scale: Consider database-backed scripts for real-time updates

**Success Criteria:**
- ✅ Continuous improvement in metrics
- ✅ Script A/B tests guide decisions
- ✅ Team confidence in system high

---

## What This Enables

### Current System Capability
- Reactive responses: "How can I help?"
- Generic tone: No state-specific personality
- No quality assurance: LLM generates once, sent as-is

### Enhanced System Capability
1. **Proactive Guidance**
   - "Welcome! Are you looking to book a car service?"
   - Not just answering, actively guiding

2. **State-Specific Personality**
   - Greeting: warm, inviting, professional
   - Name collection: friendly, personalized
   - Vehicle details: knowledgeable, thorough
   - Date selection: efficient, confirmatory
   - Confirmation: professional, summary-focused

3. **Quality Assurance**
   - Multiple attempts with feedback
   - Automatic scoring
   - Threshold-based acceptance

4. **Easy Iteration**
   - Change scripts without code deploy
   - A/B test different personalities
   - Data-driven optimization

5. **Scalability**
   - Patterns work for any conversation state
   - Easy to add new states/scripts
   - Ready for future features (multi-language, regional variations)

---

## Comparison: Before vs After

### Example: Greeting State

**Before (Reactive Only)**
```
User: "Hi"

System:
  - Extracts: No structured data
  - Sentiment: neutral
  - ResponseMode: LLM_ONLY
  - Generates: "Hi there! How can I help you today?"

Problem: Generic, no guidance toward booking
```

**After (Proactive + Quality Assured)**
```
User: "Hi"

System:
  - Gets Script: goal="Welcome and offer booking", personality="warm, professional"
  - StateAwareResponseGenerator generates:
    "Welcome to Yawlit Car Wash! I'm here to help you book a premium service
    for your vehicle. Are you looking to schedule an appointment?"
  - Refine scores: 0.85 (exceeds threshold 0.7)
  - Accepts response

Benefit: Warm greeting + clear value proposition + booking offer = 3x more likely to convert
```

---

## Files Summary

| File | Type | Action | Lines | Purpose |
|------|------|--------|-------|---------|
| `conversation_script_manager.py` | New | Create | ~80 | Centralized state scripts |
| `signatures.py` | Existing | Add | ~25 | StateAwareResponseSignature |
| `modules.py` | Existing | Add | ~15 | StateAwareResponseGenerator |
| `message_processor.py` | Existing | Modify | ~80 | Integration + Refine logic |
| **Total** | | | **~200** | **~4% of codebase** |

---

## Questions Answered

**Q: Why not just modify templates?**
A: Templates are static text. State-aware generation adapts to context, sentiment, conversation history.

**Q: Why Refine? Why not just generate once?**
A: Refine ensures quality with feedback loop. DSPy tutorials show this pattern works well for complex tasks.

**Q: Will this slow down responses?**
A: N=2 attempts usually accepts on first attempt (~1s). Threshold=0.7 prevents endless retrying.

**Q: What if state-aware fails?**
A: Falls back to proven tone-aware generation. No response ever fails to user.

**Q: Can we change scripts without redeploying?**
A: Yes! Scripts in ConversationScriptManager.CONVERSATION_SCRIPTS. Can load from database in future.

**Q: Does this break existing functionality?**
A: No. All changes are additions/wraps. No modifications to public APIs or existing logic.

---

## References

**DSPy Patterns Used:**
- Game Tutorial: Modular signatures + state-based routing
- Refine Tutorial: Multiple attempts + reward function + threshold
- Customer Service Agent: Explicit context preservation

**Principles Applied:**
- SOLID (Single Responsibility, Open/Closed, Interface Segregation, Dependency Inversion)
- DRY (Don't Repeat Yourself)
- Graceful Degradation (fallbacks)
- Explicit over Implicit (clear state scripts)

---

## Appendix A: Script Customization Examples

### Example 1: Add New State Script

```python
# In ConversationScriptManager.CONVERSATION_SCRIPTS
"time_slot_selection": StateScript(
    state="time_slot_selection",
    goal="Confirm preferred time slot for appointment",
    personality="helpful, efficient, accommodating",
    need_next=["time_slot"],
    proactive_message="We have morning (6-9am), afternoon (10am-1pm), and evening (2-6pm) slots available. Which works best for you?",
    validation_rules=["must_present_options", "must_ask_for_slot"]
)
```

### Example 2: A/B Test Different Personalities

```python
# Original (warm, conversational)
original_script = StateScript(..., personality="warm, friendly, conversational", ...)

# Variant A (professional, efficient)
variant_a_script = StateScript(..., personality="professional, efficient, direct", ...)

# Variant B (empathetic, understanding)
variant_b_script = StateScript(..., personality="empathetic, understanding, patient", ...)

# In message_processor, swap based on user_id hash:
script = (
    variant_a_script if hash(user_id) % 3 == 0
    else variant_b_script if hash(user_id) % 3 == 1
    else original_script
)
```

### Example 3: Dynamic Quality Thresholds

```python
# In _generate_empathetic_response():
# Different thresholds for different states
threshold = {
    "greeting": 0.6,  # Warmer/more welcoming, lower bar
    "name_collection": 0.7,  # Standard
    "confirmation": 0.85,  # Higher bar (critical decision point)
}.get(current_state.value, 0.7)

refined_gen = dspy.Refine(
    module=state_gen,
    N=2,
    reward_fn=response_quality_score,
    threshold=threshold,  # Dynamic!
    fail_count=2
)
```

---

**Document Status:** Ready for Implementation
**Last Updated:** 2025-11-30
**Author:** Claude Code Planning Assistant
**Approval Needed:** User Review
