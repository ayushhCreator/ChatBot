"""
Conversation manager for handling chat history and state.
"""
from typing import Dict, Any, Optional
from config import ConversationState
from models import ValidatedConversationContext


class ConversationManager:
    """Manages conversation contexts and history."""

    def __init__(self):
        self.conversations: Dict[str, ValidatedConversationContext] = {}

    def get_or_create(
        self,
        conversation_id: str,
        initial_state: ConversationState = ConversationState.GREETING
    ) -> ValidatedConversationContext:
        """Get existing or create new conversation context."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ValidatedConversationContext(
                conversation_id=conversation_id,
                state=initial_state
            )
        return self.conversations[conversation_id]

    def add_user_message(self, conversation_id: str, content: str) -> ValidatedConversationContext:
        """Add user message to conversation."""
        context = self.get_or_create(conversation_id)
        context.add_message("user", content)
        return context

    def add_assistant_message(self, conversation_id: str, content: str) -> ValidatedConversationContext:
        """Add assistant message to conversation."""
        context = self.get_or_create(conversation_id)
        context.add_message("assistant", content)
        return context

    def update_state(self, conversation_id: str, new_state: ConversationState, reason: Optional[str] = None) -> None:
        """Update conversation state with transition tracking."""
        context = self.get_or_create(conversation_id)
        old_state = context.state
        context.state = new_state
        context.add_state_transition(old_state, new_state, reason)

    def store_user_data(self, conversation_id: str, key: str, value: Any) -> None:
        """Store extracted user data."""
        context = self.get_or_create(conversation_id)
        context.user_data[key] = value

    def get_user_data(self, conversation_id: str, key: str, default: Any = None) -> Any:
        """Get stored user data."""
        context = self.get_or_create(conversation_id)
        return context.user_data.get(key, default)

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    def get_dspy_history(self, conversation_id: str):
        """
        Get conversation history as dspy.History object for DSPy modules.

        DSPy modules require conversation_history parameter in dspy.History format.
        This method converts internal ValidatedConversationContext to that format.

        Args:
            conversation_id: ID of the conversation to retrieve

        Returns:
            dspy.History object with conversation messages

        Example:
            >>> history = conversation_manager.get_dspy_history("conv_123")
            >>> result = sentiment_analyzer(
            ...     conversation_history=history,
            ...     current_message="How can I help?"
            ... )
        """
        from history_utils import messages_to_dspy_history
        context = self.get_or_create(conversation_id)
        return messages_to_dspy_history(context)