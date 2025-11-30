"""ConfirmationGenerator: Format scratchpad into user-friendly confirmation message."""

from booking.scratchpad import ScratchpadForm


class ConfirmationGenerator:
    """Generate confirmation messages from scratchpad data."""

    @staticmethod
    def generate_summary(scratchpad: ScratchpadForm) -> str:
        """Generate clean, user-friendly confirmation summary."""
        lines = [
            "📋 BOOKING CONFIRMATION",
            "═" * 50,
            ""
        ]

        # Customer section
        if scratchpad.customer:
            lines.append("👤 CUSTOMER DETAILS:")
            name_parts = []
            if "first_name" in scratchpad.customer and scratchpad.customer["first_name"].value:
                name_parts.append(scratchpad.customer["first_name"].value)
            if "last_name" in scratchpad.customer and scratchpad.customer["last_name"].value:
                name_parts.append(scratchpad.customer["last_name"].value)
            if name_parts:
                lines.append(f"   Name: {' '.join(name_parts)}")
            if "phone" in scratchpad.customer and scratchpad.customer["phone"].value:
                lines.append(f"   Phone: {scratchpad.customer['phone'].value}")
            if "email" in scratchpad.customer and scratchpad.customer["email"].value:
                lines.append(f"   Email: {scratchpad.customer['email'].value}")
            lines.append("")

        # Vehicle section
        if scratchpad.vehicle:
            lines.append("🚗 VEHICLE DETAILS:")
            parts = []
            for field in ["brand", "model", "year"]:
                if field in scratchpad.vehicle and scratchpad.vehicle[field].value:
                    parts.append(str(scratchpad.vehicle[field].value))
            if parts:
                lines.append(f"   Vehicle: {' '.join(parts)}")
            if "plate" in scratchpad.vehicle and scratchpad.vehicle["plate"].value:
                lines.append(f"   Plate: {scratchpad.vehicle['plate'].value}")
            if "color" in scratchpad.vehicle and scratchpad.vehicle["color"].value:
                lines.append(f"   Color: {scratchpad.vehicle['color'].value}")
            lines.append("")

        # Appointment section
        if scratchpad.appointment:
            lines.append("📅 APPOINTMENT:")
            if "date" in scratchpad.appointment and scratchpad.appointment["date"].value:
                lines.append(f"   Date: {scratchpad.appointment['date'].value}")
            if "service_type" in scratchpad.appointment and scratchpad.appointment["service_type"].value:
                lines.append(f"   Service: {scratchpad.appointment['service_type'].value}")
            if "time_slot" in scratchpad.appointment and scratchpad.appointment["time_slot"].value:
                lines.append(f"   Time: {scratchpad.appointment['time_slot'].value}")
            lines.append("")

        lines.append("[Edit] [Confirm] [Cancel]")
        return "\n".join(lines)

    @staticmethod
    def generate_with_sources(scratchpad: ScratchpadForm) -> str:
        """Generate detailed summary with source attribution (debug mode)."""
        lines = [
            "DEBUG: Scratchpad with Sources",
            "═" * 50,
            ""
        ]

        sections = [
            ("CUSTOMER", scratchpad.customer),
            ("VEHICLE", scratchpad.vehicle),
            ("APPOINTMENT", scratchpad.appointment)
        ]

        for section_name, section_data in sections:
            if section_data:
                lines.append(f"{section_name}:")
                for field_name, entry in section_data.items():
                    if entry.value is not None:
                        conf = int(entry.confidence * 100) if entry.confidence else 0
                        source = entry.source or "unknown"
                        turn = f"Turn {entry.turn}" if entry.turn else "N/A"
                        method = entry.extraction_method or "N/A"
                        lines.append(
                            f"  • {field_name}: {entry.value} ({conf}%) "
                            f"[{source} - {turn} - {method}]"
                        )
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def is_empty(scratchpad: ScratchpadForm) -> bool:
        """Check if scratchpad has any data."""
        return (
            not any(e.value for e in scratchpad.customer.values()) and
            not any(e.value for e in scratchpad.vehicle.values()) and
            not any(e.value for e in scratchpad.appointment.values())
        )
