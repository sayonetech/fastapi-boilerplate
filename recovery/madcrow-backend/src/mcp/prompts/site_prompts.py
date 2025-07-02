"""Site-related MCP prompts for the Beco MCP Server."""

# Import the MCP wrapper
from ...extensions.ext_mcp import mcp_wrapper

mcp = mcp_wrapper


@mcp.prompt(
    name="site_information_assistant",
    description="Generates a comprehensive prompt for site information and venue assistance",
    tags={"site-info", "venue", "location", "assistance"},
)
def site_information_assistant() -> str:
    """
    Creates a prompt that instructs the AI to use the get_site_info tool for venue-related queries.
    """
    return (
        "You are an AI assistant with access to the Beco MCP Server, which provides detailed information "
        "about venues and sites.\n\n"
        "## Available Tools\n\n"
        "### get_site_info\n"
        "This tool retrieves comprehensive information about the current site/venue. Use this tool when you "
        "need to:\n\n"
        "- Provide location-based assistance or navigation help\n"
        "- Answer questions about venue details, operating hours, or contact information\n"
        "- Help users understand the current site's facilities and services\n"
        "- Provide context about the venue for location-based recommendations\n\n"
        "**What this tool returns:**\n"
        "- Site identification (ID, name, type)\n"
        "- Geographic location (latitude, longitude, address)\n"
        "- Operating hours and schedule\n"
        "- Contact information (phone, website)\n"
        "- Timezone and UTC offset\n"
        "- Site type (MALL, AIRPORT, UNIVERSITY, OFFICE, etc.)\n\n"
        "## Usage Guidelines\n\n"
        "1. **When to use get_site_info:**\n"
        "   - User asks about the current location or venue\n"
        "   - User needs information about operating hours\n"
        "   - User wants contact details or website information\n"
        "   - User asks for navigation or location-based assistance\n"
        "   - User inquires about venue type or facilities\n\n"
        "2. **How to respond:**\n"
        "   - Always call the tool first to get current site information\n"
        "   - Present the information in a clear, organized manner\n"
        "   - Use the site context to provide relevant assistance\n"
        "   - Include practical details like operating hours and contact info\n\n"
        "3. **Example interactions:**\n"
        "   - 'What time does this place close?' → Use get_site_info to check operating hours\n"
        "   - 'Where am I?' → Use get_site_info to provide location details\n"
        "   - 'How can I contact this venue?' → Use get_site_info for phone/website info\n"
        "   - 'What type of venue is this?' → Use get_site_info to identify site type\n\n"
        "## Response Format\n\n"
        "When providing site information, structure your response like this:\n\n"
        "**📍 Current Location:** [Site Name]\n"
        "**🏢 Venue Type:** [Type]\n"
        "**📍 Address:** [Full Address]\n"
        "**🕒 Operating Hours:** [Hours with days]\n"
        "**📞 Contact:** [Phone Number]\n"
        "**🌐 Website:** [Website URL]\n"
        "**🕐 Timezone:** [Timezone with UTC offset]\n\n"
        "Then provide any additional context or assistance based on the user's specific needs.\n\n"
        "Remember: Always use the get_site_info tool to get the most current and accurate information about the "
        "venue before providing any location-based assistance."
    )


@mcp.prompt(
    name="venue_navigation_help",
    description="Generates a prompt for navigation and location assistance within venues",
    tags={"navigation", "venue", "location", "help"},
)
def venue_navigation_help(user_question: str) -> str:
    """
    Creates a prompt for helping users with navigation and location questions within venues.
    Args:
        user_question: The user's specific question about location or navigation
    """
    return (
        f'The user is asking: "{user_question}"\n\n'
        "To provide accurate assistance, I need to understand the current venue context. "
        "Let me retrieve the site information first using the get_site_info tool.\n\n"
        "After getting the venue details, I will:\n"
        "1. Provide location-specific information\n"
        "2. Offer navigation guidance if applicable\n"
        "3. Include relevant venue details like operating hours\n"
        "4. Suggest next steps based on the venue type\n\n"
        "Please use the get_site_info tool to get current venue information before responding to the user's question."
    )


@mcp.prompt(
    name="venue_contact_assistant",
    description="Generates a prompt for handling venue contact and information requests",
    tags={"contact", "venue", "information", "assistance"},
)
def venue_contact_assistant(inquiry_type: str = "general") -> str:
    """
    Creates a prompt for handling various types of venue contact and information requests.
    Args:
        inquiry_type: Type of inquiry (general, hours, contact, location, etc.)
    """
    inquiry_prompts = {
        "general": "general venue information",
        "hours": "operating hours and schedule",
        "contact": "contact details and communication",
        "location": "location and address information",
        "facilities": "venue facilities and services",
    }
    inquiry = inquiry_prompts.get(inquiry_type, "venue information")
    return (
        f"The user is requesting {inquiry}.\n\n"
        "I need to provide accurate and up-to-date information about the current venue. "
        "Let me use the get_site_info tool to retrieve the latest venue details.\n\n"
        "Based on the venue information, I will provide:\n"
        "- Relevant details specific to their inquiry\n"
        "- Contact information if needed\n"
        "- Operating hours if relevant\n"
        "- Location details if applicable\n"
        "- Any additional context that might be helpful\n\n"
        "Please use the get_site_info tool to get current venue information before responding."
    )
