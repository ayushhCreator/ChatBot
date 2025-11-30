"""
Message Processor - Main orchestrator coordinating all chatbot components.

Single Responsibility: Coordinate high-level message processing flow.
Reason to change: Overall message processing flow changes.

This is the ONLY class that should coordinate between components.
All other logic is delegated to specialized coordinators.
"""
import dspy
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from config import ConversationState, config
from conversation_manager import ConversationManager
from sentiment_analyzer import SentimentAnalysisService
from response_composer import ResponseComposer
from template_manager import TemplateManager
from models import ValidatedChatbotResponse
from retroactive_validator import final_validation_sweep

# Import coordinators (SRP-compliant modules)
from .state_coordinator import StateCoordinator
from .extraction_coordinator import ExtractionCoordinator
from .scratchpad_coordinator import ScratchpadCoordinator

# Import optional fields extractor (from parent directory)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from optional_fields_extractor import OptionalFieldsExtractor
from modules import ConfirmationIntentDetector

logger = logging.getLogger(__name__)


class MessageProcessor:
    """
    Main orchestrator coordinating message processing flow.

    Follows Single Responsibility Principle (SRP):
    - Only coordinates high-level flow
    - Delegates to specialized coordinators for specific tasks
    - Does NOT contain extraction, state transition, or scratchpad logic
    """

    def __init__(self):
        """Initialize message processor with all required services and coordinators."""
        # Core services
        self.conversation_manager = ConversationManager()
        self.sentiment_service = SentimentAnalysisService()
        self.response_composer = ResponseComposer()
        self.template_manager = TemplateManager()

        # SRP-compliant coordinators
        self.state_coordinator = StateCoordinator()
        self.extraction_coordinator = ExtractionCoordinator()
        self.scratchpad_coordinator = ScratchpadCoordinator()

        # Optional fields extractor (for enhanced/non-required data)
        self.optional_fields_extractor = OptionalFieldsExtractor()

        # DSPy-based confirmation intent detector
        self.confirmation_intent_detector = ConfirmationIntentDetector()

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
        4. Classify intent
        5. Determine response mode (template, LLM, or both)
        6. Extract structured data
        7. Compose final response
        8. Update state based on intent/context
        9. Update scratchpad

        State is managed internally - NOT provided by client.

        Args:
            conversation_id: Unique conversation identifier
            user_message: User's raw message

        Returns:
            ValidatedChatbotResponse with message, extracted data, state, etc.
        """
        # 1. Store user message and get conversation context
        context = self.conversation_manager.add_user_message(conversation_id, user_message)
        history = self.conversation_manager.get_dspy_history(conversation_id)

        # 2. Get current state from stored conversation context
        current_state = context.state

        # 2a. Classify user intent (delegated to ExtractionCoordinator)
        intent = self.extraction_coordinator.classify_intent(history, user_message)

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

        # 4. Extract structured data (delegated to ExtractionCoordinator)
        extracted_data = self.extraction_coordinator.extract_for_state(
            current_state, user_message, history
        )

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
            template_variables=self._get_template_variables(extracted_data),
            template_key=template_key
        )

        # 6.5. Detect typos in user response - CONFIRMATION state (with template) or when extracted data present
        # User might type "confrim" or "bokking" and we detect and ask "did you mean?"
        typo_correction_message = None

        # CRITICAL: Enable typo correction in ALL states when data is extracted
        # Previously was only in CONFIRMATION state, missing typos in other states
        if response.get("has_template") and extracted_data:
            # Check for typos when user provides data (any state)
            if current_state == ConversationState.CONFIRMATION:
                expected_actions = "confirm, edit, cancel, yes, no, ok, okay, book, proceed"
            else:
                # In other states, expect data field corrections
                expected_actions = "correct, change, edit, update, modify, wrong, typo, misspelled"

            typo_correction_message = self.extraction_coordinator.detect_typos_in_response(
                user_message, history, response["response"],
                expected_actions=expected_actions
            )
            # If typo detected, prepend correction message to response
            if typo_correction_message:
                response["response"] = typo_correction_message + "\n\n" + response["response"]
                logger.info(f"✅ TYPO CORRECTION OFFERED: {typo_correction_message}")

        # 6.6. Run detailed typo detection with extracted data
        # (delegated to ExtractionCoordinator)
        typo_corrections = None
        if extracted_data:
            # Run in all states, not just CONFIRMATION
            typo_corrections = self.extraction_coordinator.detect_typos_in_confirmation(
                extracted_data, user_message, history
            )

        # 7. Store extracted data in conversation context
        if extracted_data:
            for key, value in extracted_data.items():
                self.conversation_manager.store_user_data(conversation_id, key, value)

        # 7.5. Retroactively validate and complete missing prerequisite data
        # OPTIMIZATION: Pass merged data (stored + extracted) to avoid redundant scans
        # CRITICAL: Only run retroactive validator if enabled (disabled after booking)
        try:
            # Merge stored data with current extraction to get complete picture
            context = self.conversation_manager.get_or_create(conversation_id)
            merged_for_retroactive = {**context.user_data, **(extracted_data or {})}

            # Re-enable retroactive validator if returning to GREETING state
            if current_state == ConversationState.GREETING:
                context.metadata['retroactive_enabled'] = True
                logger.info("✅ RETROACTIVE: Re-enabled (state returned to GREETING)")

            # Check if retroactive validator is enabled
            retroactive_enabled = context.metadata.get('retroactive_enabled', True)

            if not retroactive_enabled:
                logger.info("⏭️  RETROACTIVE: Skipped (disabled after booking creation)")
                retroactive_data = {}
            else:
                logger.warning(f"🔄 RETROACTIVE: Starting sweep. State={current_state.value}, Extracted={extracted_data}")
                retroactive_data = final_validation_sweep(
                    current_state=current_state.value,
                    extracted_data=merged_for_retroactive,  # Pass merged data instead of just extracted_data
                    history=history
                )
                logger.warning(f"🔄 RETROACTIVE: Result={retroactive_data}")

            # Merge retroactively filled data with existing extracted data
            # CRITICAL FIX: Only merge if new value is not None/Unknown
            if retroactive_data:
                if not extracted_data:
                    extracted_data = {}
                # Track what changed (including improvements to "Unknown" values)
                improved_fields = []
                for key, value in retroactive_data.items():
                    # CRITICAL FIX: Skip if retroactive value is None or "Unknown"
                    # This prevents overwriting existing valid data with None/Unknown
                    if value is None or str(value).lower() in ["unknown", "none", ""]:
                        logger.debug(f"⏭️  RETROACTIVE: Skipping {key}={value} (invalid value)")
                        continue

                    old_value = merged_for_retroactive.get(key)  # Check against merged data, not just extracted_data
                    if old_value != value:
                        if str(old_value).lower() == "unknown" and str(value).lower() != "unknown":
                            improved_fields.append(f"{key}: {old_value}→{value}")
                        elif key not in merged_for_retroactive or old_value is None:
                            improved_fields.append(key)
                    extracted_data[key] = value
                if improved_fields:
                    logger.warning(f"⚡ RETROACTIVE IMPROVEMENTS: {improved_fields}")
                # Store retroactively filled data (only valid values)
                for key, value in retroactive_data.items():
                    if value is not None and str(value).lower() not in ["unknown", "none", ""]:
                        self.conversation_manager.store_user_data(conversation_id, key, value)
        except Exception as e:
            logger.error(f"❌ Retroactive validation ERROR: {type(e).__name__}: {e}", exc_info=True)

        # 8. Check if ALL required fields are present (needed for state transition decision)
        from retroactive_validator import DataRequirements
        required_fields_confirmation = set(DataRequirements.REQUIREMENTS.get(ConversationState.CONFIRMATION.value, []))
        required_fields_current_state = set(DataRequirements.REQUIREMENTS.get(current_state.value, []))

        # CRITICAL FIX: Merge ConversationManager's stored data with current turn's extracted_data
        # This ensures retroactively-filled fields are included in the field-presence check
        context = self.conversation_manager.get_or_create(conversation_id)
        merged_data = {**context.user_data, **(extracted_data or {})}
        extracted_fields = set(merged_data.keys())

        # Check if ALL required fields are present
        has_all_required = required_fields_confirmation.issubset(extracted_fields)
        can_advance_from_current_state = required_fields_current_state.issubset(extracted_fields)

        # Debug logging to track field completion
        print(f"🔍 flags: has_all_required={has_all_required}, can_advance={can_advance_from_current_state}, merged_keys={list(merged_data.keys())}")

        # Initialize scratchpad early (needed for confirmation flow)
        scratchpad = self.scratchpad_coordinator.get_or_create(conversation_id)

        # 8.4. CRITICAL FIX: Populate scratchpad with ALL collected data BEFORE booking
        # This ensures ServiceRequestBuilder has complete data when creating booking
        # Merge all data sources: conversation_manager stored data + current extraction
        all_collected_data = {**context.user_data, **(extracted_data or {})}

        # Map field names from extracted/stored data to scratchpad sections
        for field_name, value in all_collected_data.items():
            if value is None:
                continue

            # Determine section based on field name
            if field_name in ["first_name", "last_name", "full_name", "phone", "address"]:
                section = "customer"
                scratchpad_field = field_name
            elif field_name in ["vehicle_brand", "vehicle_model", "vehicle_plate", "vehicle_type"]:
                section = "vehicle"
                # Map extracted field names to scratchpad field names
                field_mapping = {
                    "vehicle_brand": "brand",
                    "vehicle_model": "model",
                    "vehicle_plate": "plate",
                    "vehicle_type": "vehicle_type"
                }
                scratchpad_field = field_mapping.get(field_name, field_name)
            elif field_name in ["appointment_date", "service_type", "service_tier", "time_slot", "notes"]:
                section = "appointment"
                # Map extracted field names to scratchpad field names
                field_mapping = {
                    "appointment_date": "date",
                    "service_type": "service_type",
                    "service_tier": "service_tier",
                    "time_slot": "time_slot",
                    "notes": "notes"
                }
                scratchpad_field = field_mapping.get(field_name, field_name)
            else:
                # Unknown field, skip
                logger.debug(f"⏭️  SCRATCHPAD: Skipping unknown field {field_name}")
                continue

            # Add to scratchpad with metadata
            scratchpad.add_field(
                section=section,
                field_name=scratchpad_field,
                value=value,
                source="collection",
                turn=0,
                confidence=1.0,
                extraction_method="collected"
            )
            logger.debug(f"✅ SCRATCHPAD: Added {section}.{scratchpad_field}={value}")

        # 8.5. CONFIRMATION FLOW: Handle 3-attempt confirmation with auto-booking
        service_request_id = None

        if current_state == ConversationState.CONFIRMATION and has_all_required:
            confirmation_attempts = context.metadata.get('confirmation_attempts', 0)

            # Check if user confirmed explicitly (keyword-based)
            confirm_keywords = ["yes", "confirm", "ok", "okay", "book", "proceed", "finalize", "haan", "haa"]
            user_confirmed_keywords = any(kw in user_message.lower() for kw in confirm_keywords)

            # Use DSPy-based confirmation intent detector for more intelligent detection
            try:
                confirmation_result = self.confirmation_intent_detector(
                    conversation_history=history,
                    current_state=current_state.value,
                    user_message=user_message
                )
                user_confirmed_dspy = confirmation_result.is_confirming.lower() == "true"
                dspy_confidence = float(confirmation_result.confidence) if hasattr(confirmation_result, 'confidence') else 0.0
                logger.info(f"🤖 CONFIRMATION (DSPy): is_confirming={user_confirmed_dspy}, confidence={dspy_confidence}, reasoning={confirmation_result.reasoning if hasattr(confirmation_result, 'reasoning') else 'N/A'}")
            except Exception as e:
                logger.warning(f"⚠️  CONFIRMATION (DSPy): Failed to use DSPy detector: {e}, falling back to keywords")
                user_confirmed_dspy = user_confirmed_keywords
                dspy_confidence = 1.0 if user_confirmed_keywords else 0.0

            # Combine both methods: DSPy + keywords (OR logic - either is confirmation)
            user_confirmed = user_confirmed_keywords or user_confirmed_dspy

            # Check if user wants to edit/cancel
            edit_keywords = ["edit", "change", "update", "correct", "modify"]
            cancel_keywords = ["cancel", "no", "abort"]
            user_wants_edit = any(kw in user_message.lower() for kw in edit_keywords)
            user_wants_cancel = any(kw in user_message.lower() for kw in cancel_keywords)

            # Increment confirmation attempts
            confirmation_attempts += 1
            context.metadata['confirmation_attempts'] = confirmation_attempts

            # CRITICAL: Auto-confirm after configured attempts OR explicit confirmation
            auto_confirmed = confirmation_attempts >= config.CONFIRMATION_AUTO_CONFIRM_ATTEMPTS
            if (auto_confirmed and not user_wants_edit and not user_wants_cancel) or user_confirmed:
                # CRITICAL: Check CONFIRMATION_MODE toggle
                # In BUTTON mode: Stay in CONFIRMATION state, wait for button click
                # In CHAT mode: Create service request immediately
                if config.CONFIRMATION_MODE == "CHAT":
                    # PROTECTION: Check if booking already exists (from BUTTON mode or previous call)
                    existing_service_request_id = context.metadata.get('service_request_id')
                    scratchpad_completeness = scratchpad.get_completeness()

                    if existing_service_request_id and scratchpad_completeness == 0.0:
                        # Booking already created by BUTTON mode, scratchpad already cleared
                        service_request_id = existing_service_request_id
                        logger.warning(f"⏭️  REUSE EXISTING: Booking already done (likely BUTTON mode), service_request_id={service_request_id}")
                    else:
                        # Create booking using ServiceRequestBuilder (scratchpad is now populated)
                        from booking.service_request import ServiceRequestBuilder
                        service_request = ServiceRequestBuilder.build(scratchpad, conversation_id)
                        service_request_id = service_request.service_request_id

                        # Store service_request_id (DO NOT disable retroactive validator yet)
                        context.metadata['service_request_id'] = service_request_id

                        # NOTE: scratchpad clearing moved to AFTER response is built (line 418)
                        # This ensures scratchpad_dict has the actual data for API response

                        # Reset confirmation attempts
                        context.metadata['confirmation_attempts'] = 0

                        # CRITICAL: Mark that booking is complete (will disable retroactive after state transition to COMPLETED)
                        context.metadata['booking_completed'] = True

                        logger.warning(f"✅ BOOKING CREATED (CHAT MODE): service_request_id={service_request_id}, attempts={confirmation_attempts}, auto_confirmed={auto_confirmed}")
                else:  # BUTTON mode
                    # Stay in CONFIRMATION state, do NOT create service request here
                    # The /api/confirmation endpoint will handle service request creation
                    logger.info(f"🔘 BUTTON MODE: User confirmed (attempts={confirmation_attempts}, auto={auto_confirmed}), waiting for button click to create service request")
            elif user_wants_edit or user_wants_cancel:
                # Reset confirmation attempts if user wants to edit or cancel
                context.metadata['confirmation_attempts'] = 0
                logger.info(f"🔄 CONFIRMATION: User requested {'cancel' if user_wants_cancel else 'edit'}, resetting attempts")

        # 9. Determine next state (delegated to StateCoordinator)
        # CRITICAL FIX: Pass both flags to prevent premature state jumps
        next_state = self.state_coordinator.determine_next_state(
            current_state, sentiment, extracted_data, user_message,
            all_required_fields_present=has_all_required,
            can_advance_from_current_state=can_advance_from_current_state
        )
        if next_state != current_state:
            reason = self.state_coordinator.determine_state_change_reason(
                user_message, sentiment, extracted_data
            )
            print(f"📊 decision.complete_check: has_all_required={has_all_required}, current_state={current_state.value}, next_state={next_state.value}")
            self.conversation_manager.update_state(conversation_id, next_state, reason)

        # CRITICAL: Disable retroactive validator ONLY when state transitions to COMPLETED after booking
        # This preserves validator functionality for customers who reschedule in same session
        if next_state == ConversationState.COMPLETED and context.metadata.get('booking_completed'):
            context.metadata['retroactive_enabled'] = False
            logger.info("⏭️  RETROACTIVE: Disabled (state transition to COMPLETED after booking)")

        # 10. Update scratchpad AFTER state transition (delegated to ScratchpadCoordinator)
        # Note: scratchpad already initialized earlier, reuse it
        if extracted_data and service_request_id is None:  # Don't update if booking already created
            for key, value in extracted_data.items():
                # Use next_state here so scratchpad updates correctly
                self.scratchpad_coordinator.update_from_extraction(
                    scratchpad, next_state, key, value
                )

        should_confirm = (
            next_state == ConversationState.CONFIRMATION and
            has_all_required
        )

        data_extracted_this_turn = extracted_data is not None and len(extracted_data) > 0
        scratchpad_completeness = scratchpad.get_completeness()

        # CRITICAL FIX: Build scratchpad dict BEFORE any clearing happens
        # This captures the actual scratchpad state to return in API response
        scratchpad_dict = None
        if scratchpad:
            scratchpad_dict = {
                "customer": {k: v.value for k, v in scratchpad.form.customer.items() if v.value is not None},
                "vehicle": {k: v.value for k, v in scratchpad.form.vehicle.items() if v.value is not None},
                "appointment": {k: v.value for k, v in scratchpad.form.appointment.items() if v.value is not None},
                "completeness": scratchpad_completeness
            }

        # Build service request dict for API response (NEW: for v3 visualization)
        service_request_dict = None
        if service_request_id:
            service_request_dict = {
                "service_request_id": service_request_id,
                "status": "confirmed",
                "created_at": datetime.now().isoformat()
            }

        # CRITICAL FIX: Clear scratchpad AFTER all responses have been built
        # Previously was done at line 345 before scratchpad_dict was created
        # ONLY clear in CHAT mode - in BUTTON mode, /api/confirmation endpoint handles clearing
        if service_request_id and config.CONFIRMATION_MODE == "CHAT":
            scratchpad_completeness = scratchpad.get_completeness()

            # PROTECTION: Check if scratchpad is empty (already cleared by BUTTON mode)
            # If service_request_id exists but scratchpad is empty, skip dump (already done)
            if scratchpad_completeness == 0.0:
                logger.warning(f"⏭️  SKIP DUMP: Scratchpad already cleared (booking done in BUTTON mode), service_request_id={service_request_id}")
            else:
                # Dump service request JSON before clearing scratchpad (CHAT mode only)
                from service_request_dumper import dump_service_request
                try:
                    dump_service_request(
                        service_request_id=service_request_id,
                        conversation_id=conversation_id,
                        scratchpad=scratchpad,
                        confirmation_method="chat",
                        additional_metadata={"confirmation_mode": "CHAT"}
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to dump service request: {e}")

                # Now clear scratchpad after successful dump
                scratchpad.clear_all()
                logger.info(f"🧹 SCRATCHPAD CLEARED (CHAT MODE): service_request_id={service_request_id}")

        return ValidatedChatbotResponse(
            message=response["response"],
            should_proceed=True,
            extracted_data=extracted_data,
            sentiment=sentiment.to_dict() if sentiment else None,
            intent=intent.intent_class if intent else None,  # NEW: Include intent class
            intent_confidence=intent.confidence if intent else 0.0,  # NEW: Include confidence
            suggestions={},
            processing_time_ms=0,
            confidence_score=0.85,
            should_confirm=should_confirm,
            scratchpad_completeness=scratchpad_completeness,
            scratchpad=scratchpad_dict,  # NEW: Include scratchpad contents
            state=next_state.value,
            data_extracted=data_extracted_this_turn,
            typo_corrections=typo_corrections,
            service_request_id=service_request_id,  # Include booking ID if created
            service_request=service_request_dict  # NEW: Include full service request
        )

    def _generate_empathetic_response(
        self,
        history: dspy.History,
        user_message: str,
        current_state: ConversationState,
        sentiment,
        extracted_data: Optional[Dict[str, Any]]
    ) -> str:
        """Generate empathetic LLM response based on context, sentiment, and state goals using DSPy Refine.

        NEW: Integrates StateAwareResponseGenerator with DSPy Refine for quality improvement.
        Falls back to ToneAwareResponseGenerator if state scripts unavailable.
        """
        from modules import SentimentToneAnalyzer, ToneAwareResponseGenerator, StateAwareResponseGenerator
        from conversation_script_manager import conversation_script_manager

        try:
            # Step 1: Try to get state script for proactive personality
            state_script = conversation_script_manager.get_script(current_state.value)

            if state_script:
                # NEW: Use StateAwareResponseGenerator with DSPy Refine for quality improvement
                try:
                    logger.info(f"🎯 STATE-AWARE GENERATION: Using script for state '{current_state.value}'")

                    # Format collected fields and needed fields
                    collected_fields_str = ""
                    if extracted_data:
                        collected_fields_str = "; ".join([f"{k}: {v}" for k, v in extracted_data.items()])

                    needed_fields_str = ", ".join(state_script.need_next) if state_script.need_next else "None"

                    # Define response quality scorer
                    def response_quality_score(attempted_output, predicted_output) -> float:
                        """Score response on multiple quality criteria (0.0 to 1.0).

                        DSPy Refine passes both attempted and predicted outputs.
                        We use the predicted output (the LLM's generation).

                        Criteria:
                        - Conciseness (penalize verbose) (30%)
                        - Addresses state goal (30%)
                        - Asks for next fields naturally (25%)
                        - Respects sentiment/intent (15%)
                        """
                        # Extract response text from predicted output
                        response = str(predicted_output.response if hasattr(predicted_output, 'response') else predicted_output)

                        score = 0.0

                        # PRIORITY 1: Conciseness - prefer 1-2 sentences, penalize verbose
                        sentence_count = response.count('.') + response.count('?') + response.count('!')
                        words_count = len(response.split())

                        # Ideal: 1-2 sentences, max ~40 words
                        if sentence_count <= 2 and words_count <= 40:
                            score += 0.30  # Perfect conciseness
                        elif sentence_count <= 2 and words_count <= 60:
                            score += 0.25  # Good conciseness
                        elif sentence_count <= 3 and words_count <= 80:
                            score += 0.15  # Acceptable but verbose
                        else:
                            score += 0.05  # Too verbose, penalize heavily

                        # Check if response acknowledges/addresses state goal
                        goal_keywords = state_script.goal.lower().split()[:5]  # First 5 words of goal
                        if any(kw in response.lower() for kw in goal_keywords if len(kw) > 3):
                            score += 0.30

                        # Check if response naturally asks for next fields
                        field_keywords = [f.lower() for f in state_script.need_next]
                        if any(fk in response.lower() for fk in field_keywords):
                            score += 0.25
                        elif len(response) > 20:  # At least asking something
                            score += 0.15

                        # Check sentiment respect (avoid sounding dismissive if angry)
                        if sentiment and sentiment.anger > 6.0:
                            if any(word in response.lower() for word in ["understand", "sorry", "help", "appreciate"]):
                                score += 0.15
                        else:
                            score += 0.10

                        return min(1.0, score)

                    # Try up to 2 attempts with Refine
                    refined_generator = dspy.Refine(
                        StateAwareResponseGenerator(),
                        N=2,  # Max 2 attempts
                        threshold=0.75,  # Accept if quality >= 75%
                        reward_fn=response_quality_score
                    )

                    result = refined_generator(
                        conversation_history=history,
                        current_state=current_state.value,
                        state_goal=state_script.goal,
                        state_personality=state_script.personality,
                        user_message=user_message,
                        collected_fields=collected_fields_str,
                        need_next_fields=needed_fields_str
                    )

                    response = result.response if result and hasattr(result, 'response') else ""

                    if response and response.strip():
                        logger.info(f"✅ STATE-AWARE RESPONSE: Generated with goal-awareness and Refine")
                        return response

                    logger.warning(f"⚠️  STATE-AWARE RESPONSE: Generated empty, falling back to tone-aware")

                except Exception as e:
                    logger.warning(f"⚠️  STATE-AWARE GENERATION FAILED: {e}, falling back to tone-aware approach")

            # Fallback: Original tone-aware generation
            # Step 2: Analyze sentiment and determine appropriate tone + brevity
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

            # Step 3: Generate response with tone and brevity constraints
            # Pass collected data so LLM doesn't ask for data user already provided
            collected_data_str = ""
            if extracted_data:
                collected_data_str = "; ".join([f"{k}: {v}" for k, v in extracted_data.items()])

            response_generator = ToneAwareResponseGenerator()
            result = response_generator(
                conversation_history=history,
                user_message=user_message,
                tone_directive=tone_directive,
                max_sentences=max_sentences,
                current_state=current_state.value,
                collected_data=collected_data_str
            )

            response = result.response if result else ""

            # Log the tone decision for debugging
            logger.debug(f"🎯 TONE ANALYSIS: tone='{tone_directive}' max_sentences={max_sentences}")

            # Ensure we never return empty string
            if not response or not response.strip():
                return "I understand. How can I help?"
            return response

        except Exception as e:
            logger.warning(f"⚠️  Response generation failed: {e}, using fallback")
            return "I understand. How can I help?"

    def _get_template_variables(self, extracted_data: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Extract variables needed for template rendering."""
        if not extracted_data:
            return {}
        return {k: str(v) for k, v in extracted_data.items()}