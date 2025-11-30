"""
Mock WhatsApp Business API Template Strings for Yawlit Car Wash.
These are pre-approved templates with links that should be sent directly.
"""

# Greeting Template - Generated from config
def _generate_greeting_template() -> dict:
    """Generate greeting template from centralized config."""
    from config import config

    return {
        "name": "greeting_welcome",
        "content": f"""🚗 Welcome to {config.COMPANY_NAME}!

{config.COMPANY_DESCRIPTION}

Type "Hii" to get started or ask us anything!"""
    }

TEMPLATE_GREETING = _generate_greeting_template()

# Catalog Template - Generated from config
def _generate_catalog_template() -> dict:
    """Generate catalog template from centralized config."""
    from config import config

    service_icons = {
        "wash": "🚗",
        "polishing": "💎",
        "detailing": "🔧"
    }

    service_lines = [
        f"{service_icons.get(key, '✨')} *{key.upper()}* - {desc}"
        for key, desc in config.SERVICES.items()
    ]

    service_links = [
        f"[View {key.title()} Plans](https://yawlit.com/plans/{key})"
        for key in config.SERVICES.keys()
    ]

    return {
        "name": "service_catalog",
        "content": f"""📋 *Our Services:*

{chr(10).join(service_lines)}

*Tap below to view plans:*
{chr(10).join(service_links)}"""
    }

TEMPLATE_CATALOG = _generate_catalog_template()

# Service Plans Template - Tier Selection
TEMPLATE_SERVICE_PLANS = {
    "name": "service_plans_{service_type}",
    "content": """*{service_name} Plans:*

🥉 *Basic* - ₹{basic_price}
   Perfect for regular maintenance

🥈 *Standard* - ₹{standard_price}
   Most popular option

🥇 *Premium* - ₹{premium_price}
   Complete luxury treatment

[Book {service_name}](https://yawlit.com/book/{service_type})"""
}

# Vehicle Types Template - Generated from config
def _generate_vehicle_types_template() -> dict:
    """Generate vehicle types template from centralized config."""
    from config import config

    vehicle_icons = {
        "Hatchback": "🚗",
        "Sedan": "🚙",
        "SUV": "🚕",
        "EV": "⚡",
        "Luxury": "👑"
    }

    vehicle_lines = [
        f"{vehicle_icons.get(vtype, '🚗')} {vtype}"
        for vtype in config.VEHICLE_TYPES
    ]

    return {
        "name": "vehicle_types",
        "content": f"""*Select Your Vehicle Type:*

{chr(10).join(vehicle_lines)}

Reply with your vehicle type or type "?help" for guidance"""
    }

TEMPLATE_VEHICLE_TYPES = _generate_vehicle_types_template()

# Optional Fields Enhancement Template - Prompt for service tier, time slot, etc.
def _generate_optional_fields_template() -> dict:
    """Generate optional fields template with available time slots from config."""
    from config import config

    # Build time slot descriptions from config
    time_slots_text = []
    for slot_key, slot_info in config.TIME_SLOTS.items():
        label = slot_info["label"]
        desc = slot_info["description"]
        time_slots_text.append(f"• {label}: {desc}")

    time_slots_str = "\n".join(time_slots_text)

    return {
        "name": "optional_fields_prompt",
        "content": f"""📝 *Quick Details* (Optional but helpful!)

To better serve you, could you share:
• *Service Package*: Basic / Standard / Premium?
• *Preferred Time*:
{time_slots_str}
• *Special Requests*: Any specific care needed?

No worries if you can't decide now - we can finalize on call! ✨"""
    }

TEMPLATE_OPTIONAL_FIELDS_PROMPT = _generate_optional_fields_template()

# Incomplete Booking Confirmation Template - For when optional fields are skipped
TEMPLATE_INCOMPLETE_BOOKING = {
    "name": "incomplete_booking_confirmation",
    "content": """✅ *Booking Confirmed!*

📋 *Your Request:*
• *Customer*: {customer_name}
• *Vehicle*: {vehicle_info}
• *Date*: {appointment_date}

📞 *Next Steps:*
Our team will call you shortly to finalize service details (package, timing, special care).

**Service Request ID**: {service_request_id}

Thank you for choosing us! 🚗✨"""
}

# Pricing Template - Direct Links
TEMPLATE_PRICING = {
    "name": "pricing_guide",
    "content": """💰 *Complete Pricing Guide*

[View All Prices](https://yawlit.com/pricing)
[Service Comparison](https://yawlit.com/compare)

*Quick Pricing:*
• Basic Wash: ₹299-599
• Standard Polish: ₹799-1299
• Premium Detail: ₹1999-3499

Vehicle type affects pricing. Select your vehicle for accurate quote."""
}

# Booking Confirmation Template
TEMPLATE_BOOKING_CONFIRMATION = {
    "name": "booking_confirmation",
    "content": """✅ *Booking Confirmed!*

📝 Service: {service_name}
🚗 Vehicle: {vehicle_brand} {vehicle_model}
📅 Date: {booking_date}
⏰ Time: {booking_time}
💰 Amount: ₹{amount}

[Download Ticket](https://yawlit.com/ticket/{ticket_id})
[Track Service](https://yawlit.com/track/{booking_id})

Ticket #{ticket_id} sent to your email.
Thank you for choosing Yawlit! 🙏"""
}

# Reschedule Template - Alternative Dates
TEMPLATE_ALTERNATIVE_DATES = {
    "name": "alternative_dates",
    "content": """📅 *Selected Date Unavailable*

Available slots nearby:

{date_options}

Reply with your preferred date or type "?show more" for additional options

[Check Full Calendar](https://yawlit.com/calendar)"""
}

# Templates Registry - Easy lookup
TEMPLATES = {
    "greeting": TEMPLATE_GREETING,
    "catalog": TEMPLATE_CATALOG,
    "plans": TEMPLATE_SERVICE_PLANS,
    "vehicles": TEMPLATE_VEHICLE_TYPES,
    "pricing": TEMPLATE_PRICING,
    "confirmation": TEMPLATE_BOOKING_CONFIRMATION,
    "alternatives": TEMPLATE_ALTERNATIVE_DATES,
    "optional_fields_prompt": TEMPLATE_OPTIONAL_FIELDS_PROMPT,
    "incomplete_booking": TEMPLATE_INCOMPLETE_BOOKING,
}


def get_template(template_key: str) -> dict:
    """Retrieve template by key."""
    return TEMPLATES.get(template_key, {})


def render_template(template_key: str, **kwargs) -> str:
    """Render template with variables, using defaults for missing values."""
    template = TEMPLATES.get(template_key, {})
    if not template:
        return ""

    # Default values for common template variables
    defaults = {
        "service_name": "Car Wash",
        "service_type": "wash",
        "basic_price": "299",
        "standard_price": "799",
        "premium_price": "1999",
        "vehicle_brand": "Your",
        "vehicle_model": "Vehicle",
        "booking_date": "TBD",
        "booking_time": "TBD",
        "amount": "TBD",
        "ticket_id": "PENDING",
        "booking_id": "PENDING",
        "date_options": "Please contact us for available dates",
    }

    # Merge user-provided values with defaults (user values take precedence)
    merged_vars = {**defaults, **kwargs}

    content = template.get("content", "")
    for key, value in merged_vars.items():
        content = content.replace(f"{{{key}}}", str(value))

    return content