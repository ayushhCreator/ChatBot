"""
Simplified chatbot orchestrator using DSPy ReAct agent for intelligent decision-making.
Removes artificial delays, message chunking, and over-engineered state machine.
"""
import dspy
import logging
from typing import Dict, Any, Optional
from config import ConversationState
from conversation_manager import ConversationManager
from sentiment_analyzer import SentimentAnalysisService
from data_extractor import DataExtractionService
from response_composer import ResponseComposer
from template_manager import TemplateManager
from models import ValidatedChatbotResponse, ValidatedSentimentScores, ValidatedIntent, ExtractionMetadata
from dspy_config import ensure_configured
from retroactive_validator import final_validation_sweep
from booking.scratchpad import ScratchpadManager

logger = logging.getLogger(__name__)


class ChatbotOrchestrator:
    """Main orchestrator using ReAct agent for intelligent template + LLM decisions."""

    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.sentiment_service = SentimentAnalysisService()
        self.data_extractor = DataExtractionService()
        self.response_composer = ResponseComposer()
        self.template_manager = TemplateManager()
        # Scratchpad manager for tracking booking data collection
        self.scratchpad_managers: Dict[str, ScratchpadManager] = {}

    def _detect_typos_in_confirmation(
        self,
        extracted_data: Dict[str, Any],
        user_message: str,
        history: dspy.History
    ) -> Optional[Dict[str, str]]:
        """Detect typos in extracted data using DSPy TypoDetector module."""
        from modules import TypoDetector

        ensure_configured()
        try:
            typo_detector = TypoDetector()
            corrections = {}

            # Check each extracted field for typos
            for field_name, value in extracted_data.items():
                if isinstance(value, str) and len(value.strip()) > 0:
                    result = typo_detector(
                        input_text=value,
                        conversation_history=history,
                        field_name=field_name
                    )
                    if result and hasattr(result, 'has_typo') and result.has_typo:
                        if hasattr(result, 'correction') and result.correction:
                            corrections[field_name] = result.correction

            return corrections if corrections else None
        except Exception as e:
            logger.debug(f"Typo detection failed: {e}")
            return None

    def _get_or_create_scratchpad(self, conversation_id: str) -> ScratchpadManager:
        """Get or create scratchpad for a conversation."""
        if conversation_id not in self.scratchpad_managers:
            self.scratchpad_managers[conversation_id] = ScratchpadManager(conversation_id)
        return self.scratchpad_managers[conversation_id]

    def process_message(
        self,
        conversation_id: str,
        user_message: str
    ) -> ValidatedChatbotResponse:
        """
        Process incoming user message with intelligent sentiment + template-aware decisions.

        Flow:
        1. Store message in conversation
        2. Get current state from conversation context
        3. Analyze sentiment (multi-dimensional)
        4. Determine response mode (template, LLM, or both)
        5. Extract structured data if needed for current state
        6. Compose final response
        7. Update state based on intent/context

        State is managed internally - NOT provided by client.
        """

        # 1. Store user message and get conversation context
        context = self.conversation_manager.add_user_message(conversation_id, user_message)
        history = self.conversation_manager.get_dspy_history(conversation_id)

        # 2. Get current state from stored conversation context
        current_state = context.state

        # 2a. Classify user intent
        intent = self._classify_intent(history, user_message)

        # 2b. Analyze sentiment (interest, anger, disgust, boredom, neutral)
        sentiment = self.sentiment_service.analyze(history, user_message)

        # 2c. Convert sentiment values to float (handle JSON string deserialization)
        if sentiment:
            try:
                sentiment.interest = float(sentiment.interest)
                sentiment.anger = float(sentiment.anger)
                sentiment.disgust = float(sentiment.disgust)
                sentiment.boredom = float(sentiment.boredom)
            except (ValueError, TypeError):
                # Fallback to defaults if conversion fails
                sentiment.interest = 5.0
                sentiment.anger = 1.0
                sentiment.disgust = 1.0
                sentiment.boredom = 1.0

        # 3. Decide response mode based on INTENT + SENTIMENT
        # Intent OVERRIDES sentiment (e.g., pricing inquiry always shows pricing template)
        response_mode, template_key = self.template_manager.decide_response_mode(
            user_message=user_message,
            intent=intent.intent_class,
            sentiment_interest=sentiment.interest if sentiment else 5.0,
            sentiment_anger=sentiment.anger if sentiment else 1.0,
            sentiment_disgust=sentiment.disgust if sentiment else 1.0,
            sentiment_boredom=sentiment.boredom if sentiment else 1.0,
            current_state=current_state.value
        )

        # 4. Extract structured data if in data collection state
        extracted_data = self._extract_for_state(current_state, user_message, history)

        # 5. Generate LLM response if needed (empathetic conversation)
        llm_response = ""
        if self.template_manager.should_send_llm_response(response_mode):
            llm_response = self._generate_empathetic_response(
                history, user_message, current_state, sentiment, extracted_data
            )

        # 6. Compose final response (combines LLM + template intelligently)
        response = self.response_composer.compose_response(
            user_message=user_message,
            llm_response=llm_response,
            intent=intent.intent_class,
            sentiment_interest=sentiment.interest if sentiment else 5.0,
            sentiment_anger=sentiment.anger if sentiment else 1.0,
            sentiment_disgust=sentiment.disgust if sentiment else 1.0,
            sentiment_boredom=sentiment.boredom if sentiment else 1.0,
            current_state=current_state.value,
            template_variables=self._get_template_variables(extracted_data)
        )

        # 6.5. Run typo detection ONLY in CONFIRMATION state with extracted data
        typo_corrections = None
        if current_state == ConversationState.CONFIRMATION and extracted_data:
            typo_corrections = self._detect_typos_in_confirmation(extracted_data, user_message, history)

        # 7. Store extracted data in conversation context
        if extracted_data:
            for key, value in extracted_data.items():
                self.conversation_manager.store_user_data(conversation_id, key, value)

        # 7.5. Retroactively validate and complete missing prerequisite data
        try:
            logger.warning(f"🔄 RETROACTIVE: Starting sweep. State={current_state.value}, Extracted={extracted_data}")
            # Call synchronously - no async/await needed
            retroactive_data = final_validation_sweep(
                current_state=current_state.value,
                extracted_data=extracted_data if extracted_data else {},
                history=history
            )
            logger.warning(f"🔄 RETROACTIVE: Result={retroactive_data}")
            # Merge retroactively filled data with existing extracted data
            if retroactive_data:
                if not extracted_data:
                    extracted_data = {}
                # Track what changed (including improvements to "Unknown" values)
                improved_fields = []
                for key, value in retroactive_data.items():
                    old_value = extracted_data.get(key)
                    if old_value != value:
                        if str(old_value).lower() == "unknown" and str(value).lower() != "unknown":
                            improved_fields.append(f"{key}: {old_value}→{value}")
                        elif key not in extracted_data or old_value is None:
                            improved_fields.append(key)
                    extracted_data[key] = value
                if improved_fields:
                    logger.warning(f"⚡ RETROACTIVE IMPROVEMENTS: {improved_fields}")
                # Store retroactively filled data
                for key, value in retroactive_data.items():
                    self.conversation_manager.store_user_data(conversation_id, key, value)
        except Exception as e:
            logger.error(f"❌ Retroactive validation ERROR: {type(e).__name__}: {e}", exc_info=True)

        # 8. Determine next state (simplified - based on sentiment + extracted data)
        next_state = self._determine_next_state(
            current_state, sentiment, extracted_data, user_message
        )
        if next_state != current_state:
            reason = self._determine_state_change_reason(
                user_message, sentiment, extracted_data
            )
            self.conversation_manager.update_state(conversation_id, next_state, reason)

        # 9. Update scratchpad AFTER state transition (use next_state, not current_state)
        scratchpad = self._get_or_create_scratchpad(conversation_id)
        if extracted_data:
            for key, value in extracted_data.items():
                # Use next_state here so scratchpad updates correctly
                self._update_scratchpad_from_extraction(scratchpad, next_state, key, value)

        # 9. Create validated response
        # Set should_confirm to True if we're in CONFIRMATION state with all required data
        should_confirm = (
            next_state == ConversationState.CONFIRMATION and
            extracted_data is not None and
            len(extracted_data) > 0
        )

        # Check if new data was extracted in this turn
        data_extracted_this_turn = extracted_data is not None and len(extracted_data) > 0

        # Get scratchpad completeness percentage
        scratchpad_completeness = scratchpad.get_completeness()

        return ValidatedChatbotResponse(
            message=response["response"],
            should_proceed=True,
            extracted_data=extracted_data,
            sentiment=sentiment.to_dict() if sentiment else None,
            suggestions={},
            processing_time_ms=0,
            confidence_score=0.85,
            should_confirm=should_confirm,
            scratchpad_completeness=scratchpad_completeness,
            state=next_state.value,
            data_extracted=data_extracted_this_turn,
            typo_corrections=typo_corrections
        )

    def _extract_for_state(
        self,
        state: ConversationState,
        user_message: str,
        history: dspy.History
    ) -> Optional[Dict[str, Any]]:
        """
        Extract relevant data based on current conversation state.

        PHASE 1 BEHAVIOR: Extraction happens in ALL states (not just specific ones).
        This allows the retroactive validator and state machine to work properly.
        """
        extracted = {}

        # Try extracting NAME in any state (Phase 1 behavior)
        try:
            name_data = self.data_extractor.extract_name(user_message, history)
            if name_data:
                first_name = str(name_data.first_name).strip()
                if first_name and first_name.lower() not in ["none", "n/a", "unknown"]:
                    extracted["first_name"] = first_name
                    extracted["last_name"] = str(name_data.last_name).strip() if hasattr(name_data, 'last_name') else ""
                    extracted["full_name"] = f"{first_name} {extracted['last_name']}".strip()
        except Exception as e:
            logger.debug(f"Name extraction failed: {e}")

        # Try extracting PHONE in any state (Phase 1 behavior)
        # IMPORTANT: Extract phone BEFORE vehicle to avoid confusion with plate numbers
        try:
            phone_data = self.data_extractor.extract_phone(user_message, history)
            if phone_data:
                phone_number = str(phone_data.phone_number).strip() if phone_data.phone_number else None
                if phone_number and phone_number.lower() not in ["none", "unknown", "n/a"]:
                    extracted["phone"] = phone_number
        except Exception as e:
            logger.debug(f"Phone extraction failed: {e}")

        # Try extracting VEHICLE in any state (Phase 1 behavior)
        try:
            vehicle_data = self.data_extractor.extract_vehicle_details(user_message, history)
            if vehicle_data:
                brand = str(vehicle_data.brand).strip() if vehicle_data.brand else None
                if brand and brand.lower() not in ["none", "unknown"]:
                    extracted["vehicle_brand"] = brand
                    extracted["vehicle_model"] = str(vehicle_data.model).strip() if vehicle_data.model else "Unknown"
                    extracted["vehicle_plate"] = str(vehicle_data.number_plate).strip() if vehicle_data.number_plate else "Unknown"
        except Exception as e:
            logger.debug(f"Vehicle extraction failed: {e}")

        # Try extracting DATE in any state (Phase 1 behavior)
        try:
            date_data = self.data_extractor.parse_date(user_message, history)
            if date_data:
                date_str = str(date_data.date_str).strip() if date_data.date_str else None
                if date_str and date_str.lower() not in ["none", "unknown"]:
                    extracted["appointment_date"] = date_str
        except Exception as e:
            logger.debug(f"Date extraction failed: {e}")

        # Return extracted data if any, otherwise None
        return extracted if extracted else None

    def _generate_empathetic_response(
        self,
        history: dspy.History,
        user_message: str,
        current_state: ConversationState,
        sentiment: Optional[ValidatedSentimentScores],
        extracted_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate empathetic LLM response based on context and sentiment using DSPy pipeline."""
        from modules import SentimentToneAnalyzer, ToneAwareResponseGenerator

        try:
            # Step 1: Analyze sentiment and determine appropriate tone + brevity
            tone_analyzer = SentimentToneAnalyzer()
            tone_result = tone_analyzer(
                interest_score=sentiment.interest if sentiment else 5.0,
                anger_score=sentiment.anger if sentiment else 1.0,
                disgust_score=sentiment.disgust if sentiment else 1.0,
                boredom_score=sentiment.boredom if sentiment else 1.0,
                neutral_score=sentiment.neutral if sentiment else 1.0
            )

            tone_directive = tone_result.tone_directive if tone_result else "be helpful"
            max_sentences = tone_result.max_sentences if tone_result else "3"

            # Step 2: Generate response with tone and brevity constraints
            response_generator = ToneAwareResponseGenerator()
            result = response_generator(
                conversation_history=history,
                user_message=user_message,
                tone_directive=tone_directive,
                max_sentences=max_sentences,
                current_state=current_state.value
            )

            response = result.response if result else ""

            # Log the tone decision for debugging
            logger.debug(
                f"🎯 TONE ANALYSIS: tone='{tone_directive}' max_sentences={max_sentences}"
            )

            # Ensure we never return empty string
            if not response or not response.strip():
                return "I understand. How can I help?"
            return response
        except Exception as e:
            logger.warning(f"Tone-aware generation failed: {e}, using fallback")
            return "I understand. How can I help?"

    def _determine_next_state(
        self,
        current_state: ConversationState,
        sentiment: Optional[ValidatedSentimentScores],
        extracted_data: Optional[Dict[str, Any]],
        user_message: str
    ) -> ConversationState:
        """Determine next state based on sentiment, extracted data, and context."""

        # If angry/upset, offer help instead of pushing forward
        if sentiment and sentiment.anger > 6.0:
            return ConversationState.SERVICE_SELECTION

        # If user confirms at confirmation state, move to COMPLETED
        if current_state == ConversationState.CONFIRMATION:
            confirm_keywords = ["yes", "confirm", "confirmed", "correct", "proceed", "ok", "go", "book", "let's", "lets"]
            if any(kw in user_message.lower() for kw in confirm_keywords):
                return ConversationState.COMPLETED

        # If data extracted, advance state
        if extracted_data:
            # PHASE 1 FIX: Add missing GREETING → NAME_COLLECTION transition
            if current_state == ConversationState.GREETING:
                # If we extracted name data, move to NAME_COLLECTION state
                if any(k in extracted_data for k in ["first_name", "full_name"]):
                    return ConversationState.NAME_COLLECTION
            elif current_state == ConversationState.NAME_COLLECTION:
                return ConversationState.VEHICLE_DETAILS
            elif current_state == ConversationState.VEHICLE_DETAILS:
                return ConversationState.DATE_SELECTION
            elif current_state == ConversationState.DATE_SELECTION:
                return ConversationState.CONFIRMATION

        # If user asks about services/pricing, go to service selection
        service_keywords = ["service", "price", "cost", "offer", "plan", "what do you"]
        if any(kw in user_message.lower() for kw in service_keywords):
            if current_state != ConversationState.SERVICE_SELECTION:
                return ConversationState.SERVICE_SELECTION

        # Otherwise stay in current state
        return current_state

    def _determine_state_change_reason(
        self,
        user_message: str,
        sentiment: Optional[ValidatedSentimentScores],
        extracted_data: Optional[Dict[str, Any]]
    ) -> str:
        """Determine human-readable reason for state change."""
        if extracted_data:
            data_type = list(extracted_data.keys())[0]
            return f"Extracted {data_type} from message"
        if sentiment and sentiment.anger > 6.0:
            return "Customer upset - offering service selection"
        return "User interest detected"

    def _get_template_variables(self, extracted_data: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extract variables needed for template rendering."""
        if not extracted_data:
            return {}
        return {k: str(v) for k, v in extracted_data.items()}

    def _update_scratchpad_from_extraction(
        self,
        scratchpad: ScratchpadManager,
        state: ConversationState,
        field_name: str,
        value: Any
    ) -> None:
        """Update scratchpad based on extracted data field and current state."""
        # Map extracted fields to scratchpad sections
        if state == ConversationState.NAME_COLLECTION:
            section = "customer"
            # Map field names
            if field_name in ["first_name", "last_name", "full_name"]:
                scratchpad.add_field(section, field_name, value, "extraction", turn=0)

        elif state == ConversationState.VEHICLE_DETAILS:
            section = "vehicle"
            # Map vehicle fields
            field_mapping = {
                "vehicle_brand": "brand",
                "vehicle_model": "model",
                "vehicle_plate": "plate"
            }
            scratchpad_field = field_mapping.get(field_name, field_name)
            scratchpad.add_field(section, scratchpad_field, value, "extraction", turn=0)

        elif state == ConversationState.DATE_SELECTION:
            section = "appointment"
            field_mapping = {
                "appointment_date": "date"
            }
            scratchpad_field = field_mapping.get(field_name, field_name)
            scratchpad.add_field(section, scratchpad_field, value, "extraction", turn=0)

    def _classify_intent(self, history: dspy.History, user_message: str) -> ValidatedIntent:
        """Classify customer intent (pricing, booking, complaint, etc.)."""
        from modules import IntentClassifier

        ensure_configured()
        try:
            classifier = IntentClassifier()
            result = classifier(
                conversation_history=history,
                current_message=user_message
            )
            intent_class = str(result.intent_class).strip().lower()
            return ValidatedIntent(
                intent_class=intent_class,
                confidence=0.8,
                reasoning=str(result.reasoning),
                metadata=ExtractionMetadata(
                    confidence=0.8,
                    extraction_method="dspy",
                    extraction_source=user_message
                )
            )
        except Exception as e:
            logger.warning(f"Intent classification failed: {type(e).__name__}: {e}, defaulting to inquire")
            return ValidatedIntent(
                intent_class="inquire",
                confidence=0.0,
                reasoning="Failed to classify intent, using default",
                metadata=ExtractionMetadata(
                    confidence=0.0,
                    extraction_method="fallback",
                    extraction_source=user_message
                )
            )