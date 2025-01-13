
import pandas as pd
import utils.utils
from research_utils.ask_llm import call_gpt4, call_llm

"""
def gpt_list(prompt:str, key:str, use_history=False):
Purpose:
    Get a list of string answers from GPT in a single call. This function queries GPT with the prompt, extracts a list of answers, and returns them as a list of {KEY:ANSWER} pairs.
Args:
    prompt (str): The prompt to be sent to GPT.
    key (str): The key to use in the list of response pairs.
    use_history: True: provide the prior conversational history as context for the prompt. False: prompt is a stand-alone query to GPT
Returns:
    list: A list of {KEY:ANSWER} pairs (dictionaries), one for each answer in the GPT response
Example:
    print(gpt_list("Generate 3 test questions for a children's quiz that test simple two-digit addition. Do not give any answer or explanation, just the question.", 'question'))
    -> [{'question': 'What is 53 + 22?'}, {'question': 'What is the sum of 47 and 36?'}, {'question': 'How much is 59 plus 14?'}] 
"""
def gpt_list(prompt:str, key:str, use_history=False, temperature=0, cache=True, quiet=True):
#   print("DEBUG: gpt_list: prompt =", prompt)
    element_json = f"{{'item_number':INTEGER, '{key}':ITEM}}"
    response = gpt_list_json(prompt, element_json, use_history=use_history, temperature=temperature, cache=cache, quiet=quiet)
#   print("DEBUG: response = ", response)
    return [{key: item[key]} for item in response]

### ----------

"""
def gpt_list_json(prompt:str, json_template:str):
Purpose:
    Get a list of JSON answers from GPT in a single call. This function queries GPT with the prompt, extracts a list of answers as JSON objects, and returns them as a JSON array.
Args:
    prompt (str): The prompt to be sent to GPT.
    json_template (str): The template JSON to return for each answer
Returns:
    JSON array: A list of JSON objects, formatted following the json_template template.
Example:
    print(gpt_list_json("Give me two famous names", "{'first_name',FIRST_NAME, 'surname':SURNAME}"))
    -> [{'first_name': 'Albert', 'surname': 'Einstein'}, {'first_name': 'Marie', 'surname': 'Curie'}]
"""
def gpt_list_json(prompt:str, json_template:str, use_history=False, temperature=0, cache=True, quiet=True):
    full_prompt = prompt + f"\nReturn your answer as a compact JSON object, formatted as a single line with no unnecessary spaces or newlines, in the following structure: {{'answer': [{json_template}, {json_template}, ...]}}"    
    response_str = call_gpt4(full_prompt, response_format="json_object", use_history=use_history, temperature=temperature, cache=cache, quiet=quiet)
    response = utils.utils.clean_extract_json(response_str)
    try:
        item_list = response.get('answer', [])  # Get the list of questions, or an empty list if 'answer' key is not found
        return response.get('answer')
    except KeyError:
        return []  # Handle the case where the 'answer' key is not found

### ----------    

"""
def gpt_json(prompt:str, json_template:str):
Purpose:
    Return a JSON object from a query to GPT
Args:
    prompt (str): The prompt to be sent to GPT.
    json_template (str): The template JSON to return for GPT's answer
Returns:
    JSON object: json_template instantiated with GPT's answer
Example:
    print(gpt_json("What is Obama's first name and age?", "{'first_name':FIRST_NAME, 'age':INTEGER}"))
    -> {'first_name': 'Barack', 'age': 61}
"""
def gpt_json(prompt:str, json_template:str, use_history=False, temperature=0, cache=True, quiet=True):
    full_prompt = prompt + f"\nReturn your answer as a compact JSON object, formatted as a single line with no unnecessary spaces or newlines, in the following structure: {{'answer': {json_template}}}"
    response_str = call_gpt4([full_prompt], response_format="json_object", use_history=use_history, temperature=temperature, cache=cache, quiet=quiet)
    response = utils.utils.clean_extract_json(response_str)    
    return response.get('answer')

### ----------------------------------------------------------------------

"""
def map_dataframe(dataframe:pd.DataFrame, prompt_template:str, output_col:str, model='gpt4'):
Purpose:
    For every row in dataframe, query the model with the instantiated prompt_template, and put answers in the DataFrame column called output_col.
Args:
    dataframe (DataFrame): input data
    prompt_template (str): The template prompt to query model with
    output_col (str): The DataFrame column to place the answers in
    model (str): The model to query. For now, just 'gpt4' is the only valid value
Returns:
    DataFrame: The input dataframe updated with the answers. (Note: the input dataframe is destructively updated)
Example:
    x = pd.DataFrame([{'question':'What is 1 + 1?'}, {'question':'What is 2 + 2?'}])
    map_dataframe(x, "Answer this question: {question}", 'answer', model='olmo')      # x is destructively updated
    print(x)
             question answer
    0  What is 1 + 1?      2
    1  What is 2 + 2?      4

[1] Can't have this function call map_dataframe_json internally as we need to allow non-JSON answers from model='olmo'
"""
def map_dataframe(dataframe:pd.DataFrame, prompt_template:str, output_col:str, model='gpt4', quiet=True):

    responses = []
    for row_dict in dataframe.to_dict('records'):
        prompt = prompt_template.format(**row_dict)
        responses.append(call_llm(prompt, model=model, quiet=quiet))    # [1]        

    dataframe[output_col] = responses
    return dataframe        

### ======================================================================
"""
def map_dataframe_json(dataframe:pd.DataFrame, prompt_template:str, json_template:str):
Purpose:
    For every row in dataframe, query the model with the instantiated prompt_template, and collect the answer as an instantiated json_template.
    Add each answer element (key:value) in that answer to the dataframe in the column named key.
Args:
    dataframe (DataFrame): input data
    prompt_template (str): The template prompt to query model with
    json_template (str): The template JSON to collect GPT's answer in 
Returns:
    DataFrame: The input dataframe updated with the answers. (Note: the input dataframe is destructively updated)
Example:
dataset = pd.DataFrame(
  [{"question":"What is the sum of 34 and 21?","answer":"The sum of 34 and 21 is 55."},
   {"question":"Add 58 and 36 together.","answer":"Add 58 and 36: 94."}]
map_dataframe_json(dataset, "Score the answer to the following question between 0 (completely wrong) and 10 (completely correct), and give a justification:\nQuestion: {question}\nAnswer: {answer}", "{'score10': INTEGER, 'justification': JUSTIFICATION}")
print(dataset.to_csv(sep='\t'))
	question	answer	score10	justification
0	What is the sum of 34 and 21?	The sum of 34 and 21 is 55.	10	The answer provided is completely correct. The sum of 34 and 21 is indeed 55.
1	Add 58 and 36 together.	Add 58 and 36: 94.	10	The answer provided is completely correct. When you add 58 and 36 together, the sum is indeed 94.
"""
def map_dataframe_json(dataframe:pd.DataFrame, prompt_template:str, json_template:str, quiet=True):
    responses = []
    for row_dict in dataframe.to_dict('records'):
        prompt = prompt_template.format(**row_dict)
        response = gpt_json(prompt, json_template, quiet=quiet)
        responses.append(response)
    return add_list_of_dicts_to_df(dataframe, responses)

## sub-utility    
def add_list_of_dicts_to_df(df, list_of_dicts):
  """
  Adds the data from a list of dictionaries to a DataFrame.
  Args:
    df: The input DataFrame.
    list_of_dicts: A list of dictionaries, where keys may or may not 
                   correspond to existing columns in the DataFrame.
  Returns:
    The updated DataFrame.
  """
  if len(df) != len(list_of_dicts):
    raise ValueError("Length of DataFrame and list of entries to add are different! (should be the same).")

  for index, data in enumerate(list_of_dicts):
    for key, value in data.items():
      if key not in df.columns:
        df[key] = pd.NA  # Create the new column with missing values 
      df.at[index, key] = value 

  return df

"""
# Example usage
x = pd.DataFrame([{"id":1,"name":"fred"},{"id":2,"name":"Joe"},{"id":3,"name":"Mike"}])
y = [{'col1': 10, 'col2': 'a'}, {'col1': 20, 'col2': 'b'}, {'col1': 30, 'col2': 'c'}]

updated_x = add_list_of_dicts_to_df(x, y)
print(updated_x)    
   col1 col2
0    10    a
1    20    b
2    30    c
"""
