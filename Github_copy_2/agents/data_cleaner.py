import re
"""
Module for data cleaning purposes
"""

def replace_double_quotes(text):
    return text.replace('"',"'")

def remove_after_link(text): # Remove Link segment as it keeps causing enrich_prompt to access the link directly
    # Regular expression pattern to match 'Link:' and everything following it
    pattern = r'Link:.*'
    # Use re.sub() to replace matched text with an empty string
    result = re.sub(pattern, '', text, flags=re.DOTALL)
    return result

def remove_all_brackets(text):
    # Remove square brackets
    text = re.sub(r'\[|\]', '', text)

    # Remove round brackets
    text = re.sub(r'\(|\)', '', text)

    # Remove curly brackets (if any)
    text = re.sub(r'\{|\}', '', text)
    return text