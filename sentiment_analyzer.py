"""
Sentiment analysis service for customer emotions.
"""
import dspy
from modules import SentimentAnalyzer
from dspy_config import ensure_configured
from models import ValidatedSentimentScores, ExtractionMetadata


class SentimentAnalysisService:
    """Service for analyzing customer sentiment."""

    def __init__(self):
        ensure_configured()
        self.analyzer = SentimentAnalyzer()

    def analyze(
        self,
        conversation_history: dspy.History,
        current_message: str
    ) -> ValidatedSentimentScores:
        """Analyze sentiment from conversation."""
        try:
            result = self.analyzer(
                conversation_history=conversation_history,
                current_message=current_message
            )

            # Parse scores with fallback
            # Create validated sentiment scores object
            metadata = ExtractionMetadata(
                confidence=0.8,  # Default confidence for LLM analysis
                extraction_method="chain_of_thought",
                extraction_source=f"History: {str(conversation_history)[:100]}... | Message: {current_message}",
                processing_time_ms=0.0
            )

            # CRITICAL: Truncate reasoning to max 500 chars (Pydantic validation limit)
            reasoning = result.reasoning[:500] if len(result.reasoning or "") > 500 else result.reasoning

            validated_scores = ValidatedSentimentScores(
                interest=self._parse_score(result.interest_score),
                anger=self._parse_score(result.anger_score),
                disgust=self._parse_score(result.disgust_score),
                boredom=self._parse_score(result.boredom_score),
                neutral=self._parse_score(result.neutral_score),
                reasoning=reasoning,
                metadata=metadata
            )

            return validated_scores
        except Exception as e:
            # Fallback to neutral sentiment
            return self._neutral_sentiment(str(e))

    @staticmethod
    def _parse_score(score_str: str) -> float:
        """Parse score from string, handling various formats."""
        try:
            # Extract first number from string
            import re
            numbers = re.findall(r'\d+\.?\d*', str(score_str))
            if numbers:
                score = float(numbers[0])
                # Clamp score to valid range of 1-10, but be more permissive than strict validation
                clamped_score = max(1.0, min(10.0, score))
                # Round to nearest half-point to match LLM output expectations
                return round(clamped_score * 2) / 2  # Rounds to nearest 0.5
        except (ValueError, IndexError):
            pass
        return 5.0  # Default neutral

    @staticmethod
    def _neutral_sentiment(error_msg: str = "") -> ValidatedSentimentScores:
        """Return neutral sentiment as fallback."""
        # CRITICAL: Truncate error message to avoid exceeding field limits
        max_error_len = 200
        truncated_error = error_msg[:max_error_len] if len(error_msg) > max_error_len else error_msg

        metadata = ExtractionMetadata(
            confidence=0.3,  # Low confidence for fallback
            extraction_method="fallback",
            extraction_source=truncated_error,
            processing_time_ms=0.0
        )

        # CRITICAL: Truncate reasoning to max 500 chars (Pydantic validation limit)
        reasoning_prefix = "Fallback neutral sentiment. "
        max_reasoning_len = 500 - len(reasoning_prefix)
        truncated_reasoning = truncated_error[:max_reasoning_len]
        reasoning = f"{reasoning_prefix}{truncated_reasoning}"

        return ValidatedSentimentScores(
            interest=5.0,
            anger=1.0,
            disgust=1.0,
            boredom=3.0,
            neutral=7.0,
            reasoning=reasoning,
            metadata=metadata
        )
