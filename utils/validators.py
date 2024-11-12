def validate_agent_name(name: str) -> bool:
    """
    Validate agent name format.
    Only allows letters, numbers, underscore, and hyphen.
    """
    if not name:
        return False
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
