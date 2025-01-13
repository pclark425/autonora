
"""
Clear cache:
research_utils.ask_llm.cached_call_gpt4.cache_clear()

TEST CASES:
call_llm("What is 1 + 1?", "olmo")

call_gpt4("What is 1 + 1? Return your answer as a JSON structure {'answer':NUMBER}.", response_format="json_object")
Out[24]: '{\n  "answer": 2\n}'     - note you then have to subsequently parse this with json.loads(answer)

call_gpt4("What is 1 + 1?")
Out[21]: '1 + 1 equals 2.'
"""

import requests
import json
import my_globals
from functools import lru_cache

gpt4_history = []

def call_llm(question, model, quiet=True):
    if model == "olmo":
        return call_olmo(question, quiet=quiet)
    elif model == "gpt4":
        return call_gpt4(question, quiet=quiet)   
    elif model == "llama":
        return call_together(question, "llama", quiet=quiet)
    elif model == "mistral":
        return call_together(question, "mistral", quiet=quiet)
    else:
        return f"Unrecognized model: {model}"

def raw_call_olmo(prompt, temperature=0, inferd_token=my_globals.MY_INFERD_TOKEN, quiet=True):
    # quiet currently unused
    url = my_globals.OLMO_ENDPOINT
    model_version_id = my_globals.OLMO_VERSION_ID
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {inferd_token}'
    }
    data = {
        'model_version_id': model_version_id,
        'input': {
            'messages': [{
                'role': 'user',
                'content': prompt
            }],
            'opts': {
                'temperature': temperature,
                'max_tokens': 1000,
                'logprobs': 2
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_lines = response.text.strip().split('\n')
    result_tokens = []
    for line in response_lines:
        line_json = json.loads(line)
        token = line_json.get('result', {}).get('output', {}).get('text', '')
        result_tokens.append(token)
    return ''.join(result_tokens)

def call_olmo(prompt, temperature=0, cache=True, inferd_token=my_globals.MY_INFERD_TOKEN, quiet=True):
    my_globals.olmo_calls += 1        
    if cache:
        return cached_call_olmo(prompt, temperature=temperature, inferd_token=inferd_token, quiet=quiet)
    else:
        return raw_call_olmo(prompt, temperature=temperature, inferd_token=inferd_token, quiet=quiet)

# Apply the lru_cache decorator
@lru_cache() 
def cached_call_olmo(prompt, temperature=0, inferd_token=my_globals.MY_INFERD_TOKEN, quiet=True):
    return raw_call_olmo(prompt, temperature=temperature, inferd_token=inferd_token, quiet=quiet)

# Example:
# "The capital of England is London"

# ----------------------------------------


def call_together(prompt, model, together_key=my_globals.MY_TOGETHER_KEY, quiet=True):
    my_globals.together_calls += 1            
    # quiet currently unused
    url = my_globals.TOGETHER_ENDPOINT
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {together_key}"
    }
    if model == "llama":
        model_details = my_globals.LLAMA_MODEL
    elif model == "mistral":
        model_details =  my_globals.MISTRAL_MODEL
    else:
        print("Unrecognized model! ", model)
    data = {
#       "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
#       "model": "meta-llama/Llama-2-7b-chat-hf",
        "model": model_details,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "max_tokens": 1024,
        "stop": ["</s>"]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)

    if response.status_code == 200:
        answer = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
#               print("Decoded line:", decoded_line)  # Debugging output
                if decoded_line.strip() == 'data: [DONE]':
#                   print("End of data stream.")
                    break  # Exit the loop as the end of the data stream is reached
                try:
                    if decoded_line.startswith('data:') and len(decoded_line) > 6:
                        json_data = json.loads(decoded_line[5:])  # Remove 'data:' prefix and parse JSON
                        text = json_data.get('choices', [{}])[0].get('text', '')
                        answer += text
                except json.JSONDecodeError as e:
                    print("JSON decode error:", e)
                    continue  # Skip this line if it cannot be decoded
        return answer.strip()
    else:
        return f"Failed to get response from {model}"

# Example usage:
# result = call_together("Please answer as concisely as possible. What is the capital of England?", "llama")
# print(result)

# ======================================================================

# Define the function to query GPT-4.
# resonse_format = "json_object" or "text"

### PEC: Need to unwind prompts into a set of messages
### NOTE: returns a string, even if response_format = "json_object". You then need to apply json.loads(result) to parse it.
def raw_call_gpt4(prompts0, response_format="text", temperature=0, openai_api_key=my_globals.MY_OAI_KEY, quiet=True):

    if response_format not in ["text", "json_object"]:
        raise ValueError("Invalid response_format. Must be 'text' or 'json_object'.")

    prompts = (
        prompts0 if isinstance(prompts0, list) else
        [prompts0] if isinstance(prompts0, str) else
        list(prompts0) if isinstance(prompts0, tuple) else
        (print(f"DEBUG: ERROR! Unrecognized prompt format {prompts0}") or None)
    )    
    
    url = my_globals.OAI_ENDPOINT
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    messages = convert_to_messages(prompts)
    data = {
        'model': 'gpt-4-1106-preview',
        'response_format': {'type':response_format},
        'messages': messages,
        'temperature': temperature,
        'max_tokens': 4000,
        'top_p': 0.5,
        'frequency_penalty': 0.5,
        'presence_penalty': 0.5
    }
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        try:
            if not quiet:
                print("DEBUG: prompts =", prompts)
#           print("DEBUG: REALLY calling gpt4...")
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            if not quiet:
                print("DEBUG: Response = ", response_json)
            
            # Check if there's an error in the response
            if 'error' in response_json:
                raise ValueError(response_json['error']['message'])
            
            # Extract the content based on the response format
            if response_format == "json_object":
                content = response_json['choices'][0]['message']['content']
            else:
                content = response_json['choices'][0]['message']['content']
            
            return content
        
        except Exception as e:
            print(f"ERROR from GPT4: {e}. Trying again...")
            attempts += 1
    
    # If all attempts fail
    print(f"ERROR from GPT4: {e}. Giving up (returning NIL)")
    return {} if response_format == "json_object" else ""

# ----------

### gpt4_history is reset after the next call with use_history=False
def call_gpt4(prompts, response_format="text", temperature=0, cache=True, use_history=False, openai_api_key=my_globals.MY_OAI_KEY, quiet=True):
    global gpt4_history

#   print("DEBUG: call_gpt4: prompts =", prompts)
    if use_history:
        if isinstance(prompts,list):
            raise HistoryInHistoryError("Don't use call_gpt4 with both a list of prompts and use_history=True!")
        else:
            prompts1 = gpt4_history + [prompts]
    else:
        gpt4_history = []
        prompts1 = prompts
    if cache:
        prompts2 = tuple(prompts1) if isinstance(prompts1,list) else prompts1	# convert list to tuples as can't cache a list. Otherwise, prompts1 is a string
        response = cached_call_gpt4(prompts2, response_format=response_format, temperature=temperature, openai_api_key=openai_api_key, quiet=quiet)	# Lists not directly hashable
    else:
        response = raw_call_gpt4(prompts1, response_format=response_format, temperature=0.5, openai_api_key=openai_api_key, quiet=quiet)
    if use_history:
        gpt4_history += [prompts,response]
    my_globals.gpt_calls += 1        
    return response        

#old    
#def call_gpt4(prompts, response_format="text", temperature=0, cache=True, openai_api_key=my_globals.MY_OAI_KEY, quiet=True):
#    if cache:
#        prompts2 = tuple(prompts) if isinstance(prompts,list) else prompts
#        return cached_call_gpt4(prompts2, response_format=response_format, temperature=temperature, openai_api_key=openai_api_key, quiet=quiet)	# Lists not directly hashable
#    else:
#        return raw_call_gpt4(prompts, response_format=response_format, temperature=0.5, openai_api_key=openai_api_key, quiet=quiet)

# Apply the lru_cache decorator
# To clear the cache:
#     research_utils.ask_llm.cached_call_gpt4.cache_clear()
@lru_cache() 
def cached_call_gpt4(prompts, response_format="text", temperature=0, openai_api_key=my_globals.MY_OAI_KEY, quiet=True):
    return raw_call_gpt4(prompts, response_format=response_format, temperature=temperature, openai_api_key=openai_api_key, quiet=quiet)

### ======================================================================

"""
Convert a list of strings showing a 2-way conversation, e.g., 
convert_to_messages(["You are a helpful assistant.","Hi","How can I help?","What is your name?"]) -> 
[{'role': 'system', 'content': 'You are a helpful assistant.'},
 {'role': 'user', 'content': 'Hi'},
 {'role': 'system', 'content': 'How can I help?'},
 {'role': 'user', 'content': 'What is your name?'}]
"""
def convert_to_messages(input_data):
    """
    Converts a list of strings representing a 2-way conversation to a JSON structure.
    Args:
        input_data: A list of strings or a single string representing the conversation.
    Returns:
        A list of dictionaries, each representing a message with 'role' and 'content' keys.
    """
    SYSTEM_PROMPT = "You are a helpful, rigorous science assistant."

    if isinstance(input_data, str):
        input_data = [input_data]

    if len(input_data) % 2 != 0:
        input_data = [SYSTEM_PROMPT] + input_data

    json_data = []
    for i in range(0, len(input_data), 2):
        json_data.append({'role': 'system', 'content': input_data[i]})
        json_data.append({'role': 'user', 'content': input_data[i+1]})
    return json_data

