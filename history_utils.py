"""
Lean utilities for DSPy conversation history management.
Follows https://dspy.ai/tutorials/conversation_history/
"""

import dspy
from typing import List, Dict, Any, Optional
from config import config


def empty_dspy_history() -> dspy.History:
    """Return empty dspy.History for modules that need default history."""
    return dspy.History(messages=[])


def get_default_history(history: dspy.History = None) -> dspy.History:
    """
    Factory function to ensure conversation_history is always dspy.History.

    Args:
        history: dspy.History object or None

    Returns:
        Provided history or empty history if None

    Usage in modules:
        conversation_history = get_default_history(conversation_history)
    """
    return history if history is not None else empty_dspy_history()


def create_dspy_history(messages: List[Dict[str, str]], max_messages: Optional[int] = None) -> dspy.History:
    """
    Convert message list to dspy.History object using centralized config.

    Args:
        messages: List of dicts with 'role' and 'content' keys
        max_messages: Keep only recent N messages (defaults to config.MAX_CHAT_HISTORY)

    Returns:
        dspy.History object formatted for DSPy modules
    """
    if max_messages is None:
        max_messages = config.MAX_CHAT_HISTORY

    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

    formatted_messages = []
    for msg in recent_messages:
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            formatted_messages.append({
                "role": msg['role'],
                "content": str(msg['content']).strip()
            })
        elif hasattr(msg, 'role') and hasattr(msg, 'content'):
            formatted_messages.append({
                "role": msg.role,
                "content": str(msg.content).strip()
            })

    return dspy.History(messages=formatted_messages)


def messages_to_dspy_history(conversation_context: Any, max_messages: Optional[int] = None) -> dspy.History:
    """
    Convert ValidatedConversationContext to dspy.History using centralized config.

    Args:
        conversation_context: Object with .messages attribute from conversation_manager
        max_messages: Keep only recent N messages (defaults to config.MAX_CHAT_HISTORY)

    Returns:
        dspy.History ready for DSPy modules
    """
    if not hasattr(conversation_context, 'messages') or not conversation_context.messages:
        return empty_dspy_history()

    if max_messages is None:
        max_messages = config.MAX_CHAT_HISTORY

    return create_dspy_history(
        [{"role": msg.role, "content": msg.content} for msg in conversation_context.messages],
        max_messages=max_messages
    )


def filter_dspy_history_to_user_only(history: dspy.History) -> dspy.History:
    """
    Filter conversation history to include ONLY user messages.

    This prevents LLM extractors from being confused by chatbot's own responses.
    When extracting user data (name, vehicle, date, etc.), the LLM should see
    only what the USER said, not what the chatbot responded with.

    Example:
        - Original: User says "I have Honda City", Chatbot says "Thanks! Now tell me your date"
        - User-only history: User says "I have Honda City"  (chatbot response removed)
        - Result: LLM extracts vehicle cleanly without "date" polluting name extraction

    Args:
        history: dspy.History with both user and assistant messages

    Returns:
        dspy.History with only user messages
    """
    if not history or not hasattr(history, 'messages'):
        return empty_dspy_history()

    user_only_messages = [
        msg for msg in history.messages
        if isinstance(msg, dict) and msg.get('role') == 'user'
    ]

    return dspy.History(messages=user_only_messages)


def get_user_and_assistant_history(history: dspy.History) -> dspy.History:
    """
    Get conversation history with both user and assistant messages.

    Use this when you need full conversation context (e.g., sentiment analysis, intent classification).
    This is the default behavior.

    Args:
        history: dspy.History object

    Returns:
        Same dspy.History (no filtering)
    """
    return history if history is not None else empty_dspy_history()