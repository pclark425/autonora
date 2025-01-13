
import time
import numpy as np

MY_OAI_KEY = print("Add your OAI key to my_globals.py to proceed!")
MY_TOGETHER_KEY = print("Add your Together key to my_globals.py to proceed (if you want to use Mistral or Llama)!")
MY_INFERD_TOKEN = print("Add your InferD token to my_globals.py to proceed (if you want to use OLMo)!")

# counters
gpt_calls = 0
olmo_calls = 0
together_calls = 0
start_time = 0

MAX_ITERATIONS = 200     # prevent runaway system!

''' OLD
# constants, for autonora_probing
TOPIC = "How well can OLMo answer two-digit addition problems?"
EXAMPLE_QUESTION = "What is 23 + 43?"
BATCH_SIZE = 5
N_QUESTIONS = 20
AUTONORA_VERSION = "2.0"
KB_SERVER_URL = "https://dummy/"
'''

OUTPUT_DIR = "output/"

dialog_so_far = []   # ordered list. Odd elements are Nora's question, Even elements are GPT's response.
py_counter = 1
state = {}
last_report_filestem = None

# keys and models
OAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

OLMO_ENDPOINT = 'https://ai2-reviz--olmoe-1b-7b-0924-instruct.modal.run/completion'  # updated 10/16/24
OLMO_VERSION_ID = 'mov_01j1x1awwfqx23gmw0wkmb73ea'

TOGETHER_ENDPOINT = "https://api.together.xyz/v1/chat/completions"
LLAMA_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"	# more recent
MISTRAL_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"

def reset_counters ():
    global olmo_calls, gpt_calls, together_calls, py_counter, start_time
    olmo_calls = 0
    gpt_calls = 0
    together_calls = 0
    py_counter = 1
    start_time = time.time()
