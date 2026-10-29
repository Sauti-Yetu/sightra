"""
Product surface flags. Hidden features stay in the codebase and routes;
they are only omitted from primary navigation until we re-enable them.
"""

ACTIVE_NAV = ("home", "vision", "reader", "settings")

# Kept for restore — do not delete feature modules when these are False.
HIDDEN_NAV = ("map", "connect", "voice_assistant")
