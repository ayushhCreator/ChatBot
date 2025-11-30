"""
DSPy modules (predictors) for different tasks.
Uses history_utils for clean conversation history handling.
"""
import dspy
from history_utils import get_default_history
from config import config as _config
# inside modules.py, replace NameExtractor.forward with this implementation
from types import SimpleNamespace
from typing import Any
from signatures import (
    SentimentAnalysisSignature,
    NameExtractionSignature,
    VehicleDetailsExtractionSignature,
    PhoneExtractionSignature,
    DateParsingSignature,
    ResponseGenerationSignature,
    IntentClassificationSignature,
    SentimentToneSignature,
    ToneAwareResponseSignature,
    TypoCorrectionSignature,
    ConfirmationIntentSignature,
    StateAwareResponseSignature,
)


class SentimentAnalyzer(dspy.Module):
    """Analyze customer sentiment across multiple dimensions."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SentimentAnalysisSignature)

    def forward(self, conversation_history=None, current_message: str = ""):
        """Analyze sentiment with proper conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_message=current_message
        )


class IntentClassifier(dspy.Module):
    """Classify user intent using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(IntentClassificationSignature)

    def forward(self, conversation_history=None, current_message: str = ""):
        """Classify user intent with conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_message=current_message
        )




# small helper: a dict that allows attribute access (keeps dict semantics too)
class AttrDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

class NameExtractor(dspy.Module):
    """Extract customer name from unstructured text with conservative post-filters."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(NameExtractionSignature)
        # cache stopwords set once
        self._greeting_stopwords = {s.lower() for s in _config.GREETING_STOPWORDS}

    def _token_name_score(self, tok: str) -> int:
        alpha_count = sum(1 for c in tok if c.isalpha())
        return 1 if alpha_count >= 2 else 0

    def _looks_like_name_multi_token(self, tokens):
        scores = [self._token_name_score(t) for t in tokens if t.strip()]
        if not scores:
            return False
        return sum(scores) >= max(1, len(scores) // 2)

    def _is_single_token_greeting(self, token_lower: str):
        token_clean = token_lower.strip(" .,!?:;\"'`")
        return token_clean in self._greeting_stopwords

    def _explicit_name_intent(self, user_message: str) -> bool:
        lc = user_message.lower()
        triggers = ["my name is", "call me", "you can call me", "this is", "i am ", "i'm "]
        return any(p in lc for p in triggers)

    def _safe_extract_from_raw(self, raw: Any):
        if isinstance(raw, dict):
            first = (raw.get("first_name") or "").strip()
            last = (raw.get("last_name") or "").strip()
            conf = (raw.get("confidence") or "").strip().lower()
            raw_type = "dict"
        else:
            first = getattr(raw, "first_name", "") or ""
            last = getattr(raw, "last_name", "") or ""
            conf = getattr(raw, "confidence", "") or ""
            conf = conf.strip().lower() if isinstance(conf, str) else ""
            raw_type = "obj"
        return first, last, conf, raw_type

    def _wrap_output(self, out_dict: dict, raw_type: str):
        if raw_type == "dict":
            return AttrDict(out_dict)
        else:
            return SimpleNamespace(**out_dict)

    def forward(self, conversation_history=None, user_message: str = "", context: str = "") -> AttrDict | SimpleNamespace:
        
        conversation_history = get_default_history(conversation_history)

        raw = self.predictor(
            conversation_history=conversation_history,
            user_message=user_message,
            context=context or "collecting customer name"
        )

        first, last, confidence, raw_type = self._safe_extract_from_raw(raw)

        # Compose candidate
        candidate = ""
        if first and last:
            candidate = f"{first} {last}".strip()
        elif first:
            candidate = first.strip()
        else:
            if isinstance(raw, dict):
                candidate = (raw.get("full_name") or "").strip()
            else:
                candidate = getattr(raw, "full_name", "") or ""
            candidate = (candidate or "").strip()

        # Explicit intent - highest priority
        if self._explicit_name_intent(user_message):
            if not candidate:
                lc = user_message.lower()
                for trigger in ["my name is", "call me", "you can call me", "this is"]:
                    idx = lc.find(trigger)
                    if idx != -1:
                        candidate = user_message[idx + len(trigger):].strip().strip(".")
                        break
            if not candidate:
                out = {"first_name":"", "last_name":"", "confidence":"low"}
                return self._wrap_output(out, raw_type)
            toks = candidate.split()
            out = {"first_name": toks[0].title(), "last_name": " ".join(toks[1:]).title() if len(toks)>1 else "", "confidence":"high"}
            return self._wrap_output(out, raw_type)

        if not candidate:
            out = {"first_name":"", "last_name":"", "confidence":"low"}
            return self._wrap_output(out, raw_type)

        tokens = [t.strip() for t in candidate.split() if t.strip()]
        lower_tokens = [t.lower() for t in tokens]

        # Single-token candidate: be conservative
        if len(tokens) == 1:
            tok = tokens[0]
            tok_lower = lower_tokens[0].strip(" .,!?:;\"'`")
            if self._is_single_token_greeting(tok_lower):
                return self._wrap_output({"first_name":"", "last_name":"", "confidence":"low"}, raw_type)
            if len(tok) <= 1:
                return self._wrap_output({"first_name":"", "last_name":"", "confidence":"low"}, raw_type)
            if confidence == "high":
                out_conf = "high"
            elif confidence == "medium":
                out_conf = "medium"
            else:
                return self._wrap_output({"first_name":"", "last_name":"", "confidence":"low"}, raw_type)
            return self._wrap_output({"first_name": tok.title(), "last_name":"", "confidence": out_conf}, raw_type)

        # Multi-token candidate: allow with checks.
        if self._looks_like_name_multi_token(tokens):
            first_lower = lower_tokens[0].strip(" .,!?:;\"'`")
            if first_lower in self._greeting_stopwords:
                out_conf = "medium" if confidence != "high" else "high"
                toks = tokens
                return self._wrap_output({"first_name": toks[0].title(), "last_name":" ".join(toks[1:]).title(), "confidence": out_conf}, raw_type)
            out_conf = confidence if confidence in ("high","medium") else "medium"
            toks = tokens
            return self._wrap_output({"first_name": toks[0].title(), "last_name":" ".join(toks[1:]).title(), "confidence": out_conf}, raw_type)

        return self._wrap_output({"first_name":"", "last_name":"", "confidence":"low"}, raw_type)


class VehicleDetailsExtractor(dspy.Module):
    """Extract vehicle details from unstructured text."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(VehicleDetailsExtractionSignature)

    def forward(self, conversation_history=None, user_message: str = ""):
        """Extract vehicle details with conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            user_message=user_message
        )


class PhoneExtractor(dspy.Module):
    """Extract phone number from unstructured text."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(PhoneExtractionSignature)

    def forward(self, conversation_history=None, user_message: str = ""):
        """Extract phone number with conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            user_message=user_message
        )


class DateParser(dspy.Module):
    """Parse natural language dates."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(DateParsingSignature)

    def forward(self, conversation_history=None, user_message: str = "", current_date: str = ""):
        """Parse date with conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            user_message=user_message,
            current_date=current_date
        )


class EmpathyResponseGenerator(dspy.Module):
    """Generate empathetic, context-aware responses."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(ResponseGenerationSignature)

    def forward(self, conversation_history=None, current_state: str = "", user_message: str = "", sentiment_context: str = ""):
        """Generate response with full conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_state=current_state,
            user_message=user_message,
            sentiment_context=sentiment_context
        )


class SentimentToneAnalyzer(dspy.Module):
    """Analyze sentiment scores and determine appropriate tone and brevity."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SentimentToneSignature)

    def forward(
        self,
        interest_score: float = 5.0,
        anger_score: float = 1.0,
        disgust_score: float = 1.0,
        boredom_score: float = 1.0,
        neutral_score: float = 1.0
    ):
        """Determine tone and brevity based on sentiment scores."""
        return self.predictor(
            interest_score=str(interest_score),
            anger_score=str(anger_score),
            disgust_score=str(disgust_score),
            boredom_score=str(boredom_score),
            neutral_score=str(neutral_score)
        )


class ToneAwareResponseGenerator(dspy.Module):
    """Generate concise, tone-appropriate responses respecting brevity constraints."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(ToneAwareResponseSignature)

    def forward(
        self,
        conversation_history=None,
        user_message: str = "",
        tone_directive: str = "be helpful",
        max_sentences: str = "3",
        current_state: str = "greeting",
        collected_data: str = ""
    ):
        """Generate response adapted to tone and sentence limit.

        Args:
            collected_data: String representation of data already collected from USER.
                           Prevents LLM from asking for data user already provided.
        """
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            user_message=user_message,
            tone_directive=tone_directive,
            max_sentences=max_sentences,
            current_state=current_state,
            collected_data=collected_data
        )


class TypoDetector(dspy.Module):
    """Detect typos in confirmation responses and suggest corrections.

    Only triggers when:
    - Service card/confirmation was shown with action buttons
    - User response appears to be typo/gibberish
    - Response is NOT a valid one-word answer
    """

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(TypoCorrectionSignature)

    def forward(
        self,
        last_bot_message: str = "",
        user_response: str = "",
        expected_actions: str = "confirm, edit, cancel"
    ):
        """Detect typos and suggest corrections."""
        return self.predictor(
            last_bot_message=last_bot_message,
            user_response=user_response,
            expected_actions=expected_actions
        )


class ConfirmationIntentDetector(dspy.Module):
    """Detect if user is confirming their booking using DSPy reasoning."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(ConfirmationIntentSignature)

    def forward(self, conversation_history=None, current_state: str = "", user_message: str = ""):
        """Detect confirmation intent with conversation context."""
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_state=current_state,
            user_message=user_message
        )


class StateAwareResponseGenerator(dspy.Module):
    """Generate responses aligned with state goals and personality traits."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(StateAwareResponseSignature)

    def forward(
        self,
        conversation_history=None,
        current_state: str = "",
        state_goal: str = "",
        state_personality: str = "",
        user_message: str = "",
        collected_fields: str = "",
        need_next_fields: str = ""
    ):
        """Generate response aligned with state context.

        Args:
            conversation_history: Full conversation history
            current_state: Current conversation state name
            state_goal: Goal for this state (from ConversationScriptManager)
            state_personality: Personality directive for this state
            user_message: Latest user message
            collected_fields: String of fields already collected
            need_next_fields: String of fields still needed

        Returns:
            DSPy prediction with response and quality_reasoning
        """
        conversation_history = get_default_history(conversation_history)
        return self.predictor(
            conversation_history=conversation_history,
            current_state=current_state,
            state_goal=state_goal,
            state_personality=state_personality,
            user_message=user_message,
            collected_fields=collected_fields,
            need_next_fields=need_next_fields
        )