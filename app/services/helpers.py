from difflib import get_close_matches
import openai
import os

def match_user_input(user_input: str, expected_options: list) -> str | None:
    """Match natural language input to one of the expected options."""
    normalized = user_input.strip().lower()

    # Try keyword match (any word in option in input)
    for option in expected_options:
        option_words = option.lower().split()
        if any(word in normalized for word in option_words):
            return option

    # Try fuzzy match
    matches = get_close_matches(normalized, [opt.lower() for opt in expected_options], n=1, cutoff=0.5)
    if matches:
        for opt in expected_options:
            if opt.lower() == matches[0]:
                return opt
    return None

def llm_match_user_input(user_input: str, expected_options: list) -> str | None:
    """Use OpenAI LLM to match user input to one of the expected options."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    prompt = (
        f"User said: '{user_input}'\n"
        f"Options: {expected_options}\n"
        "Which option best matches the user's intent? "
        "Return only the exact option string from the list, or 'None' if no match."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0,
            api_key=api_key
        )
        result = response.choices[0].message['content'].strip()
        if result in expected_options:
            return result
    except Exception as e:
        pass
    return None 