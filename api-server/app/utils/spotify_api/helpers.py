import re
from typing import Any, TypeGuard


def is_dict_or_none(d: dict | None) -> TypeGuard[dict | None]:
    return isinstance(d, (dict, type(None)))


def is_list_of_dicts_or_none(
    lst: list[dict | None],
) -> TypeGuard[list[dict | None]]:
    return all(is_dict_or_none(item) for item in lst)


def get_list_data_from_response(response: dict[str, Any], key: str):
    """
    Several endpoints in the Spotify API return a list of dictionaries (or None) in the response
    (which contains the data we are interested int), under a specific key.

    This function performs basic validation on such responses and returns the data if it is valid.
    """
    try:
        data = response[key]
    except KeyError:
        raise ValueError(f"Expected '{key}' key not found in response.")
    if not is_list_of_dicts_or_none(data):
        raise ValueError(f"Expected '{key}' in response to be a list of dictionaries.")
    return data


def remove_spotify_id(input_string: str) -> str:
    # Regular expression to match a Spotify 22-character ID
    id_pattern = r"[A-Za-z0-9]{22}"

    # Search for the ID in the input string
    match = re.search(id_pattern, input_string)

    if match:
        # Remove the ID from the string
        cleaned_string = input_string.replace(match.group(), "")
        return cleaned_string
    else:
        return input_string
