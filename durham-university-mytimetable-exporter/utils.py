def normalize_text(text: str) -> str:
    return " ".join(text.split())


def get_bool_from_str_input(input_str) -> bool:
    if input_str in ["YES", "Yes", "Y", "y"]:
        is_affirmative = True
    elif input_str in ["NO", "No", "N", "n"]:
        is_affirmative = False
    else:
        raise ValueError("Invalid input: Please enter y or n.")

    return is_affirmative
