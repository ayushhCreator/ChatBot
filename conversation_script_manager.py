"""
Conversation Script Manager - Centralized source of truth for state-specific chatbot personality.

Single Responsibility: Provide state-specific scripts, goals, and personality traits.
Reason to change: When chatbot personality, scripts, or state-specific behavior changes.
"""
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StateScript:
    """Defines script and personality for a specific conversation state."""
    state: str
    goal: str  # What we're trying to achieve in this state
    personality: str  # Tone/approach (e.g., "friendly", "professional", "enthusiastic")
    need_next: List[str]  # What fields we still need
    proactive_message: str  # Suggested opening for this state
    validation_rules: Dict[str, str] = field(default_factory=dict)  # Field-specific guidance


class ConversationScriptManager:
    """Manages state-specific conversation scripts and personality traits.

    Single Responsibility: Provide scripts for each state without modifying them.
    """

    # Centralized state scripts - single source of truth
    CONVERSATION_SCRIPTS: Dict[str, StateScript] = {
        "greeting": StateScript(
            state="greeting",
            goal="Warmly welcome customer and establish that we're here to help with car services",
            personality="friendly, warm, welcoming",
            need_next=["name", "vehicle_info", "service_intent"],
            proactive_message="Hi there! Welcome to Yawlit Car Wash. I'm here to help you book a premium car care service. What's your name?",
            validation_rules={
                "first_name": "Should be a real name, not a greeting or courtesy phrase"
            }
        ),
        "name_collection": StateScript(
            state="name_collection",
            goal="Collect and confirm customer name, establish personal connection",
            personality="friendly, attentive, professional",
            need_next=["vehicle_brand", "vehicle_model", "vehicle_plate"],
            proactive_message="Thanks for that! Now, I'd like to help you with your car service. What vehicle do you drive? (Brand and model please)",
            validation_rules={
                "first_name": "Must be at least 2 characters",
                "last_name": "Optional but helps personalization"
            }
        ),
        "service_selection": StateScript(
            state="service_selection",
            goal="Understand customer's service needs and guide them through service options",
            personality="informative, helpful, consultative",
            need_next=["vehicle_brand", "vehicle_model", "vehicle_plate", "service_type"],
            proactive_message="Great! Let me show you our service options. We offer Basic, Standard, and Premium packages. Which service level interests you most?",
            validation_rules={
                "service_type": "Should be one of: Full car wash, Basic wash, Premium detailing, etc."
            }
        ),
        "vehicle_details": StateScript(
            state="vehicle_details",
            goal="Collect all vehicle information needed for service booking",
            personality="professional, detail-oriented, helpful",
            need_next=["vehicle_plate", "appointment_date"],
            proactive_message="Perfect! Just to confirm your vehicle details and help with our service. What's your vehicle's license plate number?",
            validation_rules={
                "vehicle_brand": "Should be a real car brand (Toyota, Honda, Maruti, etc.)",
                "vehicle_model": "Should be a valid model for the brand",
                "vehicle_plate": "Indian plates format typically: 2 letters + 2 digits + 2 letters + 4 digits"
            }
        ),
        "date_selection": StateScript(
            state="date_selection",
            goal="Schedule the appointment - move toward confirmation",
            personality="enthusiastic, helpful, action-oriented",
            need_next=["appointment_date", "time_slot"],
            proactive_message="Great! Now let's schedule your service. When would be a good time for us to service your car?",
            validation_rules={
                "appointment_date": "Should be a valid future date",
                "time_slot": "Should be within working hours (6 AM - 6 PM)"
            }
        ),
        "confirmation": StateScript(
            state="confirmation",
            goal="Get explicit confirmation and complete the booking",
            personality="professional, confident, clear",
            need_next=[],  # All data collected
            proactive_message="Perfect! Here's your booking summary. Please review and confirm to complete your booking.",
            validation_rules={}
        ),
    }

    def __init__(self):
        """Initialize the script manager."""
        self.scripts = self.CONVERSATION_SCRIPTS.copy()

    def get_script(self, state: str) -> Optional[StateScript]:
        """Get script for a specific state.

        Args:
            state: Conversation state name

        Returns:
            StateScript or None if not found
        """
        script = self.scripts.get(state)
        if not script:
            logger.warning(f"⚠️  Script not found for state: {state}")
            return None
        return script

    def get_all_scripts(self) -> Dict[str, StateScript]:
        """Get all conversation scripts.

        Returns:
            Dictionary of all StateScript objects
        """
        return self.scripts.copy()

    def has_script(self, state: str) -> bool:
        """Check if script exists for a state.

        Args:
            state: Conversation state name

        Returns:
            True if script exists, False otherwise
        """
        return state in self.scripts

    def update_script(self, state: str, script: StateScript) -> bool:
        """Update a conversation script at runtime.

        Args:
            state: Conversation state name
            script: New StateScript object

        Returns:
            True if update successful, False otherwise
        """
        if state not in self.scripts:
            logger.warning(f"⚠️  Cannot update unknown state: {state}")
            return False

        self.scripts[state] = script
        logger.info(f"✅ Updated script for state: {state}")
        return True

    def get_state_goal(self, state: str) -> Optional[str]:
        """Get the goal for a specific state.

        Args:
            state: Conversation state name

        Returns:
            Goal string or None if not found
        """
        script = self.get_script(state)
        return script.goal if script else None

    def get_state_personality(self, state: str) -> Optional[str]:
        """Get the personality directive for a specific state.

        Args:
            state: Conversation state name

        Returns:
            Personality string or None if not found
        """
        script = self.get_script(state)
        return script.personality if script else None

    def get_needed_fields(self, state: str) -> List[str]:
        """Get list of fields still needed in a specific state.

        Args:
            state: Conversation state name

        Returns:
            List of field names or empty list if not found
        """
        script = self.get_script(state)
        return script.need_next if script else []

    def get_proactive_message(self, state: str) -> Optional[str]:
        """Get the proactive message for a specific state.

        Args:
            state: Conversation state name

        Returns:
            Proactive message or None if not found
        """
        script = self.get_script(state)
        return script.proactive_message if script else None


# Global instance for singleton access
conversation_script_manager = ConversationScriptManager()