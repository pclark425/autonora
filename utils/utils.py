
import json

def clean_extract_json(string):
    return clean_keys(json.loads(string))

### remove spaces in keys recursively (for nested dictionaries)
### Motivation: GPT occasionally adds extra unwanted spaces in keys
def clean_keys(data):
    if isinstance(data, dict):
        # Clean dictionary keys and recursively process values
        cleaned_data = {}
        for key, value in data.items():
            cleaned_key = key.strip()
            cleaned_data[cleaned_key] = clean_keys(value)  # Recursive call
        return cleaned_data
    elif isinstance(data, list):
        # Recursively process each item in the list
        return [clean_keys(item) for item in data]
    else:
        # If the data is neither a dict nor a list, return it as is
        return data

'''
# Example usage: change key " scenario" to "scenario"
x = '{"answer": [{"item_number":15," scenario":{"context":"\'Gina learned from HR that Harold will be laid off next week due to budget cuts; Harold suspects nothing.\'","question":"\'Is Harold informed about being laid off next week as Gina knows?\'","correct_answer":"\'No\'"}}]}'

cleaned_json = clean_extract_json(x)
print(json.dumps(cleaned_json, indent=2))
'''

### ======================================================================

from html.parser import HTMLParser

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)

def remove_html_markup(html):
    """Remove HTML markup from the given string."""
    stripper = HTMLStripper()
    stripper.feed(html)
    return normalize_newlines(stripper.get_data())

# ------------------------------

import re

def normalize_newlines(text):
    # Replace multiple blank lines (lines with only whitespace or newlines) with a single newline
    return re.sub(r'(\n\s*\n)+', '\n\n', text.strip())

## replace triple, 4x, .. newlines with a double newline
#def normalize_newlines(text):
#    return re.sub(r'\n{3,}', '\n\n', text)

# ----------------------------------------------------------------------

import sys
import select
import msvcrt
import time

def get_input_with_timeout(prompt, timeout=5):
    print(prompt, end="", flush=True)
    if sys.platform == "win32":
        # Windows implementation
        start_time = time.time()
        input_str = ""
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getche()
                if char == b'\r':  # Enter key
                    print()  # Move to the next line
                    break
                input_str += char.decode()
            if time.time() - start_time > timeout:
                print("\n(Timeout reached)")
                return None
        return input_str
    else:
        # Unix implementation
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            input_str = sys.stdin.readline().strip()
            return input_str
        else:
            print("\n(Timeout reached)")
            return None

"""
# Example usage
response = get_input_with_timeout("Type 'y' to interrupt> ", timeout=5)
if response == "y":
    print("Interrupted!")
else:
    print("Continuing...")
"""

# ----------------------------------------------------------------------

def multiline_input(prompt="Enter your text (end with a blank line): "):
    print(prompt, end="")
    lines = []
    while True:
        line = input()
        if line.strip().lower() == 'q':  # Check for 'q' as an end signal
            return 'q'
        elif line.strip() == "": 
            if lines:  # Check if any lines have been entered
                break
            else:
                print("Please enter something!")
                print(prompt, end="")                
                continue  # Retry input
        lines.append(line)
    return "\n".join(lines)

# ======================================================================
#	GET RID OF SPECIAL CHARACTERS
# ======================================================================
    
# o1 version

import unicodedata

CUSTOM_REPLACEMENTS = {
    8212: ' - ',   # Em dash
    8211: '-',     # En dash
    8220: '"',     # Left double quotation mark
    8221: '"',     # Right double quotation mark
    8216: "'",     # Left single quotation mark
    8217: "'",     # Right single quotation mark
    8230: '...'    # Ellipsis
    # Add more replacements as needed
}

def replace_special_chars_with_ascii(text):
    global CUSTOM_REPLACEMENTS
    result = []

    for char in text:
        code_point = ord(char)
        if code_point in CUSTOM_REPLACEMENTS:
            result.append(CUSTOM_REPLACEMENTS[code_point])
        else:
            normalized_char = unicodedata.normalize('NFKD', char)
            ascii_bytes = normalized_char.encode('ascii', 'ignore')
            ascii_char = ascii_bytes.decode('ascii')
            result.append(ascii_char)
    ascii_text = ''.join(result)
    return ascii_text
