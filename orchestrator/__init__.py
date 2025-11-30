"""
Orchestrator package - modular components for chatbot message processing.

Follows Single Responsibility Principle (SRP) by separating concerns:
- StateCoordinator: State transition logic
- ExtractionCoordinator: Data extraction coordination
- ScratchpadCoordinator: Scratchpad management
- MessageProcessor: Main orchestrator (coordinates all components)
"""

from .state_coordinator import StateCoordinator
from .extraction_coordinator import ExtractionCoordinator
from .scratchpad_coordinator import ScratchpadCoordinator
from .message_processor import MessageProcessor

__all__ = [
    "StateCoordinator",
    "ExtractionCoordinator",
    "ScratchpadCoordinator",
    "MessageProcessor",
]