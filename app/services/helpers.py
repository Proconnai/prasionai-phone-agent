from difflib import get_close_matches

def match_user_input(user_input: str, expected_options: list) -> str | None:
    """Match natural language input to one of the expected options."""
    normalized = user_input.strip().lower()

    # Exact keyword in sentence
    for option in expected_options:
        if option.lower() in normalized:
            return option

    # Fuzzy match fallback
    matches = get_close_matches(normalized, expected_options, n=1, cutoff=0.6)
    return matches[0] if matches else None 