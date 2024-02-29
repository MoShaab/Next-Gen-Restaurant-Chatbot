import re

def get_str_from_food_dict(food_dict: dict) -> str:
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result

def extract_session_id(session_str: str) -> str:
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return None  # Return None if extraction is unsuccessful

if __name__ == "__main__":
    print(get_str_from_food_dict({"samosa": 2, "anjera": 3}))
    # print(extract_session_id("projects/next-gen-chatbot-dlnp/agent/sessions/123/contexts/ongoing-order"))
