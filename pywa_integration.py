"""
Example integration with pyWA WhatsApp chatbot.
This shows how to add intelligence layer to your existing rule-based bot.
"""
from pywa import WhatsApp, filters
from pywa.types import Message
from config import ConversationState
from chatbot_orchestrator import ChatbotOrchestrator
from dspy_config import dspy_configurator


class IntelligentWhatsAppBot:
    """WhatsApp bot with intelligent DSPy layer."""

    def __init__(self, phone_id: str, token: str):
        """Initialize bot with WhatsApp credentials."""
        self.wa = WhatsApp(phone_id=phone_id, token=token)
        self.orchestrator = ChatbotOrchestrator()

        # Initialize DSPy
        dspy_configurator.configure()

        # State is now managed internally by orchestrator
        # No need to track states manually here

        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register message handlers."""

        @self.wa.on_message(filters.text)
        def handle_text_message(client: WhatsApp, msg: Message):
            """Handle incoming text messages."""
            user_id = msg.from_user.wa_id
            user_message = msg.text

            # Process with intelligent layer
            # State is managed internally by orchestrator
            result = self.orchestrator.process_message(
                conversation_id=user_id,
                user_message=user_message
            )

            # Handle based on sentiment and suggestions
            self._handle_response(client, msg, result)
    
    def _handle_response(self, client, msg, result):
        """Handle response based on intelligence layer output."""
        user_id = msg.from_user.wa_id

        # Get current state from orchestrator's conversation manager
        context = self.orchestrator.conversation_manager.get_or_create(user_id)
        current_state = context.state

        # Check if customer is frustrated
        if not result.should_proceed:
            self._send_empathetic_message(
                client,
                user_id,
                "I sense you might be frustrated. Would you like to speak "
                "with a human representative? Or shall we simplify the process?"
            )
            return

        # Process extracted data
        if result.extracted_data:
            self._process_extracted_data(
                user_id,
                result.extracted_data,
                current_state
            )

        # Send appropriate response based on state
        self._send_state_response(client, user_id, current_state, result)
    
    def _process_extracted_data(self, user_id: str, data: dict, state: ConversationState):
        """Process and store extracted data."""
        
        if state == ConversationState.NAME_COLLECTION:
            if "full_name" in data:
                # Store in your database
                print(f"Storing name for {user_id}: {data['full_name']}")
        
        elif state == ConversationState.VEHICLE_DETAILS:
            if "vehicle_brand" in data:
                # Store vehicle details
                print(f"Storing vehicle for {user_id}: {data}")
        
        elif state == ConversationState.DATE_SELECTION:
            if "appointment_date" in data:
                # Check availability in Google Calendar
                print(f"Checking availability for {data['appointment_date']}")
    
    def _send_state_response(self, client, user_id: str, state: ConversationState, result):
        """Send response based on current state."""

        if state == ConversationState.GREETING:
            self._send_greeting(client, user_id)
            # State will be updated automatically by orchestrator

        elif state == ConversationState.NAME_COLLECTION:
            if result.extracted_data and "full_name" in result.extracted_data:
                name = result.extracted_data["full_name"]
                client.send_message(
                    to=user_id,
                    text=f"Great to meet you, {name}! 👋\n\n"
                         "Let me show you our services..."
                )
                self._send_service_catalog(client, user_id)
                # State will be updated automatically by orchestrator
            else:
                client.send_message(
                    to=user_id,
                    text="I'd love to know your name! What should I call you?"
                )

        elif state == ConversationState.VEHICLE_DETAILS:
            if result.extracted_data:
                client.send_message(
                    to=user_id,
                    text="Perfect! I've noted your vehicle details. ✅\n\n"
                         "Now let's schedule your appointment..."
                )
                # State will be updated automatically by orchestrator
            else:
                client.send_message(
                    to=user_id,
                    text="Please provide:\n"
                         "• Vehicle brand (e.g., Honda)\n"
                         "• Model (e.g., City)\n"
                         "• License plate number"
                )
    
    def _send_greeting(self, client, user_id: str):
        """Send initial greeting."""
        client.send_message(
            to=user_id,
            text="🚗 Welcome to Yawlit Car Wash! 🚗\n\n"
                 "Your car deserves the best care.\n\n"
                 "Type 'Hi' to get started!"
        )
    
    def _send_service_catalog(self, client, user_id: str):
        """Send service catalog with buttons."""
        # Note: Actual implementation depends on pyWA's button API
        client.send_message(
            to=user_id,
            text="🌟 Our Services 🌟\n\n"
                 "1️⃣ Wash - Interior & Exterior Car Wash\n"
                 "2️⃣ Polishing - Professional Car Polish\n"
                 "3️⃣ Detailing - Complete Detailing Service\n\n"
                 "Which service interests you?"
        )
    
    def _send_empathetic_message(self, client, user_id: str, message: str):
        """Send empathetic message when customer is frustrated."""
        client.send_message(
            to=user_id,
            text=f"🤝 {message}"
        )
    
    def run(self):
        """Start the bot."""
        print("🤖 Intelligent WhatsApp Bot Started!")
        print("DSPy Intelligence Layer: Active")
        print("Listening for messages...")
        # pyWA handles the event loop


# Example usage
if __name__ == "__main__":
    # Load from environment variables
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
    TOKEN = os.getenv("WHATSAPP_TOKEN")
    
    if not PHONE_ID or not TOKEN:
        print("❌ Error: Please set WHATSAPP_PHONE_ID and WHATSAPP_TOKEN")
        print("Create a .env file with:")
        print("WHATSAPP_PHONE_ID=your_phone_id")
        print("WHATSAPP_TOKEN=your_token")
        exit(1)
    
    bot = IntelligentWhatsAppBot(PHONE_ID, TOKEN)
    bot.run()
