import re

def extract_session_id(session_str: str):
    """
    Extract the session ID from the session context string.
    Args:
    - session_str (str): The session context string from Dialogflow.

    Returns:
    - str: The extracted session ID.
    """
    match = re.search(r"sessions/(.*?)/contexts", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string
    
    return ""
def get_string_from_fruit_dict(fruit_dict: dict):
    """
    Convert fruit dictionary to a readable string.
    """
    result = ", ".join([f"{int(value)} kg {key}" for key, value in fruit_dict.items()])
    return result

# def get_string_from_fruit_dict(fruit_dict: dict):
#     return "so far you have " + " and ".join(
#     f"{ fruit_dict['unit-weight'][i]['amount']} { fruit_dict['unit-weight'][i]['unit']} { fruit_dict['fruit_item'][i].lower()}"
#     for i in range(len( fruit_dict['fruit_item']))
# )

if __name__ =='__main__':
    print(get_string_from_fruit_dict({
    'unit-weight': [{'amount': 1, 'unit': 'kg'}], 
    'fruit_item': ['Apple'] 
}))
