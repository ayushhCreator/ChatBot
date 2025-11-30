"""
DSPy signatures for different chatbot tasks.
"""
import dspy


class SentimentAnalysisSignature(dspy.Signature):
    """Analyze customer sentiment across multiple dimensions."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history between user and assistant"
    )
    current_message = dspy.InputField(
        desc="Current user message to analyze"
    )

    reasoning = dspy.OutputField(
        desc="Brief explanation of the sentiment analysis"
    )
    interest_score = dspy.OutputField(
        desc="Interest level from 1-10"
    )
    anger_score = dspy.OutputField(
        desc="Anger level from 1-10"
    )
    disgust_score = dspy.OutputField(
        desc="Disgust level from 1-10"
    )
    boredom_score = dspy.OutputField(
        desc="Boredom level from 1-10"
    )
    neutral_score = dspy.OutputField(
        desc="Neutral level from 1-10"
    )


class NameExtractionSignature(dspy.Signature):
    """Extract customer name from unstructured input."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    user_message = dspy.InputField(
        desc="User's message that may contain their name"
    )
    context = dspy.InputField(
        desc="Conversation context indicating we're collecting name"
    )

    first_name = dspy.OutputField(
        desc="Extracted first name only, properly capitalized"
    )
    last_name = dspy.OutputField(
        desc="Extracted last name if provided, empty string otherwise"
    )
    confidence = dspy.OutputField(
        desc="Confidence in extraction (low/medium/high)"
    )


class VehicleDetailsExtractionSignature(dspy.Signature):
    """Extract vehicle details from unstructured input."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    user_message = dspy.InputField(
        desc="User's message containing vehicle information"
    )

    brand = dspy.OutputField(
        desc="Vehicle brand/make (e.g., Toyota, Honda, BMW)"
    )
    model = dspy.OutputField(
        desc="Vehicle model name (e.g., Corolla, Civic, X5)"
    )
    number_plate = dspy.OutputField(
        desc="License plate number in alphanumeric format (NOT phone numbers). Example: MH12AB1234, DL4CAF4321. If unsure, return 'Unknown'."
    )


class PhoneExtractionSignature(dspy.Signature):
    """Extract phone number from unstructured input."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    user_message = dspy.InputField(
        desc="User's message that may contain a phone number"
    )

    phone_number = dspy.OutputField(
        desc="10-digit Indian phone number (e.g., 9876543210, 8888777766). Return 'Unknown' if not found or if the number looks like a license plate."
    )
    confidence = dspy.OutputField(
        desc="Confidence score (0.0-1.0) for the extraction"
    )


class DateParsingSignature(dspy.Signature):
    """Parse natural language date into structured format."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    user_message = dspy.InputField(
        desc="User's message containing date/day reference"
    )
    current_date = dspy.InputField(
        desc="Today's date for reference (YYYY-MM-DD format)"
    )

    parsed_date = dspy.OutputField(
        desc="Parsed date in YYYY-MM-DD format"
    )
    confidence = dspy.OutputField(
        desc="Confidence in parsing (low/medium/high)"
    )


class SentimentToneSignature(dspy.Signature):
    """Determine appropriate tone and brevity based on sentiment scores."""

    interest_score = dspy.InputField(
        desc="Customer interest level (1-10)"
    )
    anger_score = dspy.InputField(
        desc="Customer anger level (1-10)"
    )
    disgust_score = dspy.InputField(
        desc="Customer disgust level (1-10)"
    )
    boredom_score = dspy.InputField(
        desc="Customer boredom level (1-10)"
    )
    neutral_score = dspy.InputField(
        desc="Customer neutral level (1-10)"
    )

    tone_directive = dspy.OutputField(
        desc="Tone instruction (e.g., 'direct and brief', 'engaging and conversational', 'detailed and helpful')"
    )
    max_sentences = dspy.OutputField(
        desc="Maximum number of sentences (1-4)"
    )
    reasoning = dspy.OutputField(
        desc="Why this tone and length"
    )


class ToneAwareResponseSignature(dspy.Signature):
    """Generate response adapted to tone and brevity constraints."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history"
    )
    user_message = dspy.InputField(
        desc="Latest user message"
    )
    tone_directive = dspy.InputField(
        desc="Tone instruction from SentimentToneAnalyzer"
    )
    max_sentences = dspy.InputField(
        desc="Maximum number of sentences to use"
    )
    current_state = dspy.InputField(
        desc="Current conversation state"
    )
    collected_data = dspy.InputField(
        desc="Data already collected from USER (name, phone, vehicle, date). Do NOT ask for this data again."
    )

    response = dspy.OutputField(
        desc="Concise, tone-appropriate response within sentence limit. Do NOT ask for data already in collected_data."
    )


class ResponseGenerationSignature(dspy.Signature):
    """Generate empathetic, context-aware response."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history"
    )
    current_state = dspy.InputField(
        desc="Current conversation state (e.g., collecting name, service selection)"
    )
    user_message = dspy.InputField(
        desc="Latest user message"
    )
    sentiment_context = dspy.InputField(
        desc="Current sentiment analysis summary"
    )

    response = dspy.OutputField(
        desc="Natural, empathetic response that maintains conversation flow"
    )


class IntentClassificationSignature(dspy.Signature):
    """Classify user intent from message in context."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history to understand user's intent"
    )
    current_message = dspy.InputField(
        desc="Current user message to classify"
    )

    reasoning = dspy.OutputField(
        desc="Step-by-step reasoning for the intent classification"
    )
    intent_class = dspy.OutputField(
        desc="The classified intent (one of: book, inquire, complaint, small_talk, cancel, reschedule, payment)"
    )


class TypoCorrectionSignature(dspy.Signature):
    """Detect typos in user response to service cards/action buttons and suggest corrections.

    ONLY triggers when:
    1. A service card with action buttons was just shown (confirmation, options, etc.)
    2. User response is a typo/gibberish/null (not a formed reply)
    3. User response is NOT a proper one-word answer like 'yes', 'no', 'ok'
    """

    last_bot_message = dspy.InputField(
        desc="The last bot message shown to user (service card/confirmation with buttons)"
    )
    user_response = dspy.InputField(
        desc="User's response to the service card (potentially a typo)"
    )
    expected_actions = dspy.InputField(
        desc="List of expected action words from the service card buttons (e.g., 'confirm, edit, cancel')"
    )

    is_typo = dspy.OutputField(
        desc="true if user response is a typo/gibberish, false if it's a valid response (even one word)"
    )
    intended_action = dspy.OutputField(
        desc="The likely intended action based on typo analysis (e.g., 'confirm' from 'confrim'). Empty if not a typo."
    )
    confidence = dspy.OutputField(
        desc="Confidence in typo detection and correction (low/medium/high)"
    )
    suggestion = dspy.OutputField(
        desc="Friendly 'Did you mean...?' message for the user. Empty if not a typo."
    )


class ConfirmationIntentSignature(dspy.Signature):
    """Detect if user is confirming their booking with collected data.

    This signature detects whether user is explicitly trying to confirm,
    proceed with, or finalize their booking/service request.
    """

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history to understand context"
    )
    current_state = dspy.InputField(
        desc="Current conversation state (e.g., date_selection, confirmation)"
    )
    user_message = dspy.InputField(
        desc="User's latest message"
    )

    is_confirming = dspy.OutputField(
        desc="true if user is confirming/proceeding with booking, false otherwise"
    )
    confidence = dspy.OutputField(
        desc="Confidence in confirmation detection (0.0-1.0)"
    )
    reasoning = dspy.OutputField(
        desc="Brief explanation of why this is/isn't a confirmation intent"
    )


class StateAwareResponseSignature(dspy.Signature):
    """Generate response aligned with current state's goal and personality.

    This signature generates responses that:
    1. Follow the state's specific goal and personality
    2. Ask for the next required field(s) in a natural way
    3. Maintain conversational flow while guiding toward booking completion
    4. Be CONCISE - use 1-2 sentences maximum, avoid verbose explanations
    """

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    current_state = dspy.InputField(
        desc="Current conversation state (greeting, name_collection, vehicle_details, etc.)"
    )
    state_goal = dspy.InputField(
        desc="The goal for this state (what we're trying to achieve)"
    )
    state_personality = dspy.InputField(
        desc="Personality directive for this state (friendly, professional, enthusiastic, etc.)"
    )
    user_message = dspy.InputField(
        desc="Latest user message"
    )
    collected_fields = dspy.InputField(
        desc="Fields already collected from user (prevent asking for same data again)"
    )
    need_next_fields = dspy.InputField(
        desc="Fields we still need to collect in this state"
    )

    response = dspy.OutputField(
        desc="CONCISE natural response (1-2 sentences max) aligned with state goal and personality, asking for needed fields. Avoid verbose explanations."
    )
    quality_reasoning = dspy.OutputField(
        desc="Explanation of how this response serves the state's goal"
    )

