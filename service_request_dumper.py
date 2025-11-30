"""Service Request JSON Dumper - saves confirmed bookings to datadump folder."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


def dump_service_request(
    service_request_id: str,
    conversation_id: str,
    scratchpad,
    confirmation_method: str,
    additional_metadata: Dict[str, Any] = None
) -> Path:
    """
    Dump service request data to JSON file in datadump folder.

    Args:
        service_request_id: Unique service request ID (e.g., SR-A324BAF3)
        conversation_id: Conversation ID this booking belongs to
        scratchpad: ScratchpadManager instance with booking data
        confirmation_method: "chat" or "button" - how booking was confirmed
        additional_metadata: Optional extra metadata to include

    Returns:
        Path to the created JSON file

    Note:
        This function is called from EITHER:
        - orchestrator/message_processor.py (CHAT mode)
        - main.py /api/confirmation endpoint (BUTTON mode)

        Only ONE will execute per conversation based on CONFIRMATION_MODE setting.
    """
    # Build complete service request data with scratchpad details
    service_data = {
        "service_request_id": service_request_id,
        "conversation_id": conversation_id,
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "customer": {
            k: v.value for k, v in scratchpad.form.customer.items() if v.value is not None
        },
        "vehicle": {
            k: v.value for k, v in scratchpad.form.vehicle.items() if v.value is not None
        },
        "appointment": {
            k: v.value for k, v in scratchpad.form.appointment.items() if v.value is not None
        },
        "metadata": {
            "completeness": scratchpad.get_completeness(),
            "confirmation_method": confirmation_method,
            **(additional_metadata or {})
        }
    }

    # Save to datadump folder with service_request_id as filename
    # Find the example directory (works from both orchestrator/ and main.py)
    current_file = Path(__file__)
    example_dir = current_file.parent  # We're in example/
    datadump_dir = example_dir / "datadump"
    datadump_dir.mkdir(exist_ok=True)

    filename = f"{service_request_id}.json"
    filepath = datadump_dir / filename

    with open(filepath, 'w') as f:
        json.dump(service_data, f, indent=2)

    logger.info(f"💾 SERVICE REQUEST DUMPED: {filepath} (method={confirmation_method})")

    return filepath