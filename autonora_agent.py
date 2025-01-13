
"""
USAGE:
%load_ext autoreload
%autoreload 2
%run autonora_agent
autonora()

Some example tasks:

1. Characterize how well the language model OLMo can perform 2-digit addition.
2. Is OLMo or Llama better at 2-digit addition? Use a dataset of just 5 examples to evaluate.
3. How good is OLMo at 2-digit addition? Use a dataset of just 5 examples to evaluate.
4. I'd like you to do some research on Theory of Mind. Yuling Gu recently observed that while LLMs can correctly answer direct questions about other people's beliefs, e.g., 
    'Joe took an exam in the school gym, while Alan took an exam in the library. Alan cheated. Does Joe know Alan cheated?' 
    Correct answer: No; LLM answer: No
they struggle with indirect questions about actions related to those beliefs, e.g., 
    'Joe took an exam in the school gym, while Alan took an exam in the library. Alan cheated. When Joe leaves, might Joe report that Alan cheated?' 
    Correct answer: No, as Joe is unaware of the cheating; LLM answer: Yes
Please do some research to see if this phenomenon holds for the language model OLMo or not.
5. What is 242 * 241?
"""

import json
import pandas as pd
import time
import datetime
import os

import my_globals
import utils.utils
import utils.pyparser

### import prompts
from autonora_agent_subprompts import *
# from controller import *

### import research functions into the global namespace
from research_utils.categorize_questions import place_items_in_categories, is_in_category
from research_utils.score_categories import score_categories, add_signal
from research_utils.mapping import *
from research_utils.ask_llm import call_gpt4
from write_report.write_report import write_report, dialog

# for redirecting output
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

# Constants for default values
# DEFAULT_TASK = "" - defined earlier
# DEFAULT_OUTPUT_FILESTEM = "ToM" - defined earlier

"""
Now in autonora_agent_subprompts.py
PLAN_SUBPROMPT = "Generate a plan for the task: {task}"
REPLAN_SUBPROMPT = "Replan for the task: {task}"
FIRST_ACTION_SUBPROMPT = "Describe the first action for the task: {task}"
NEXT_ACTION_SUBPROMPT = "Describe the next action for the task: {task}"
CONTINUE_SUBPROMPT = "Continue the action for the task: {task}"
DEBUG_SUBPROMPT = "Debug the step for the task: {task}"
REFLECTION_SUBPROMPT = "Reflect on the task: {task}"
"""

# Read in the system prompt
SYSTEM_PROMPT_FILE = "autonora_agent_prompt.txt"
with open(SYSTEM_PROMPT_FILE, 'r') as f:
    SYSTEM_PROMPT = f.read()

# Globals
retry_counter = 0

# State class
class State:
    def __init__(self, task, mode, plan=None, step_number=None, iteration=1, observations="", auto=False, namespace=None, interactive=True):
        self.task = task or None
        self.mode = mode
        self.plan = plan or []
        self.step_number = step_number
        self.iteration = iteration
        self.observations = observations
        self.auto = auto
        self.namespace = namespace or {}
        self.interactive = interactive

    def update(self, **kwargs):
        """Update multiple state attributes at once."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return (f"State(task={self.task}, mode={self.mode}, step_number={self.step_number}, "
                f"iteration={self.iteration}, auto={self.auto}, plan={self.plan}, "
                f"observations='{self.observations[:30]}...')")

# Core functions
# Two modes:
# 1. task=None, mode="done", interactive=True - repeatedly ask for the next task
# 2. task=task, mode="plan", interactive=False - do the given task then stop
def autonora(task=None, interactive=True):
    state = reset_autonora_state(task=task, interactive=interactive)
    autonora_step(state)

def reset_autonora_state(task=None, interactive=True, iteration=0):    
    """Top-level function to initialize and start the process."""
    my_globals.dialog_so_far = [SYSTEM_PROMPT]
    my_globals.reset_counters()
    my_globals.last_report_filestem = None
    global retry_counter
    retry_counter = 0
    namespace = initialize_namespace()
    mode = "plan" if task else "done"
    state = State(task, mode=mode, plan=None, step_number=None, auto=True, namespace=namespace, iteration=iteration, interactive=interactive)
    return state

def restart():
    autonora_step(my_globals.state)

# Execute a Python command in the AutoNORA execution environment
def py(cmd):
    if isinstance(cmd,str):
        exec(cmd, my_globals.state.namespace)
    else:
        print("ERROR! Please provide a string as an argumen to py()!")

### ======================================================================
###		MAIN LOOP	
### ======================================================================

def autonora_step(state):
    """Core loop for processing steps of a task."""
    my_globals.state = state			# Store a global copy of state, in case we interrupt and resatart
    state.iteration = state.iteration + 1	# update counter

    # auto=False means pause after each step for user input. Default is currently auto=True, so this currently not used.
    if not state.auto:
        cmd = handle_user_input(state)
        if cmd == 'q':
            return

    # safety check to prevent runaway AutoNORA
    if state.iteration > my_globals.MAX_ITERATIONS:
        observation = f"Yikes!!! Exceeded MAX_ITERATIONS ({my_globals.MAX_ITERATIONS}) steps! Giving up!"
        print(observation)
        state.observations += observation
        state.mode = "done"

    # (re)set state.task to be a new top-level research task, and flip state.mode="plan"        
    if state.mode == "done" and state.interactive:
        new_task = utils.utils.multiline_input("----------------------------------------\n\nWhat is the next research task you'd like me to do (or 'q' to quit)? End with a blank line\n> ")         
        if new_task == 'q':
            my_globals.dialog_so_far.append(state.observations)
            return
        else:
            state = reset_autonora_state(task=new_task, iteration=1)
            observation = "----------------------------------------\n     START A NEW RESEARCH TASK\n----------------------------------------\n\n" 
            observation += f"New top-level task: {new_task}\n\n"
            print(observation)
            state.observations += observation

    # if mode is (still) "done", exit.            
    if state.mode == "done":
        my_globals.dialog_so_far.append(state.observations)
        return

    # Create prompt for the next step:            
    header, mode_prompt = generate_header_and_prompt(state)
    prompt = state.observations + header + mode_prompt		# observations are from previous iteration    
    print(header, end="")
        
    # Process based on the mode
    if state.mode in ["plan", "replan"]:
        state.plan, state.observations = create_plan(prompt)
        state.update(mode="act", step_number=1)
        autonora_step(state)

    elif state.mode in ["act", "continue", "debug", "retry"]:
        action, think_observations = generate_action(prompt)
        act_observations = execute_action(action, state.namespace)
        state.update(mode="reflect", observations = think_observations + act_observations)
        autonora_step(state)

    elif state.mode == "reflect":
        observations = reflect(prompt, state)		# state.mode updated in reflect() based on the reflection result
        state.update(observations=observations)
        autonora_step(state)

    else:
        raise ValueError(f"Unrecognized mode '{state.mode}'")

### ======================================================================    

def initialize_namespace():
    """Initialize a clean execution namespace."""
    namespace = globals().copy()
    namespace["__builtins__"] = __builtins__
    return namespace

# --------------------

def handle_user_input(state):
    """Handle user input for controlling task progression."""
    cmd = None
    while cmd != '' and cmd != 'q' and cmd != 'a':  # Loop until cmd is an empty string
        cmd = input("Press <return> to continue, 'q' to quit, 'a' for auto mode, or enter a Python function> ")
        if cmd == "a":
            state.auto = True
        elif cmd.strip() and cmd != 'q':
            try:
                exec(cmd, state.namespace)
            except Exception as e:
                print(f"Error executing command: {e}")
    return cmd                

# ----------

def generate_header_and_prompt(state):
    """Generate headers and prompts for planning modes."""
    header = "-" * 40 + "\n"

    # compute some extra strings to use in the prompt
    formatted_plan = ""
    for step in state.plan:
        formatted_plan += f"{step['step_number']}. {step['step']}\n"
    step_description = next((step["step"] for step in state.plan if step["step_number"] == state.step_number), "(no current step)")
    prev_step_number = (state.step_number - 1) if state.step_number is not None else "?"
    dictionary = {**vars(state),'formatted_plan':formatted_plan, 'step_description':step_description, 'prev_step_number':prev_step_number}

    if state.mode == "plan":
        header += f"{state.iteration}. Generate Initial Plan\n"
        prompt = PLAN_SUBPROMPT.format(**dictionary)
    elif state.mode == "replan":
        header += f"{state.iteration}. Replan Task\n"
        prompt = REPLAN_SUBPROMPT.format(**dictionary)
    elif state.mode == "act":
        header += f"{state.iteration}. Perform Step {state.step_number}: {step_description}\n"
        if state.step_number == 1:
            prompt = FIRST_ACTION_SUBPROMPT.format(**dictionary)
        else:
            prompt = NEXT_ACTION_SUBPROMPT.format(**dictionary)            
    elif state.mode == "continue":
        header += f"{state.iteration}. Continue Step {state.step_number}\n"
        prompt = CONTINUE_SUBPROMPT.format(**dictionary)
    elif state.mode in ["debug", "retry"]:
        header += f"{state.iteration}. An error occurred doing step {state.step_number}. Let's try and debug the problem and retry (retry number {retry_counter}).\n"
        prompt = DEBUG_SUBPROMPT.format(**dictionary)
    elif state.mode == "reflect":
        header += f"{state.iteration}. Reflect on Step {state.step_number}\n"
        prompt = REFLECTION_SUBPROMPT.format(**dictionary)
    header += "-" * 40 + "\n"
    return header, prompt

"""
======================================================================
		MAIN EXECUTION OPERATIONS
======================================================================
INPUT: a prompt
BEHAVIOR:
 1. gets response_str from GPT
 2. [prompt,response_str] are added to the dialog_so_far
 3. generates and returns observations, namely a pretty print/execution of the response_str. This will be part of the NEXT prompt
======================================================================
"""
# Returns plan
def create_plan(prompt):
    """Execute planning logic and return the generated plan."""
    print("Planning...")
    my_globals.dialog_so_far.append(prompt)
    response_str = call_gpt4(my_globals.dialog_so_far, response_format="json_object")
    my_globals.dialog_so_far.append(response_str)
    json_response = utils.utils.clean_extract_json(response_str)
    plan = json_response['plan']	# plan = [{'step_number': 1, 'step': "Generate a dataset"}, {'step_number': 2, 'step': "..."}...]
    formatted_plan = "Current plan that you generated:\n"
    for step in plan:
        formatted_plan += f"{step['step_number']}. {step['step']}\n"
    print(formatted_plan)
    observations = ""
    return plan, observations

# --------------------

def generate_action(prompt):
    """Generate Python code"""
    print("Thinking...")
    my_globals.dialog_so_far.append(prompt)
    response_str = call_gpt4(my_globals.dialog_so_far, response_format="json_object")
    my_globals.dialog_so_far.append(response_str)
    json_response = utils.utils.clean_extract_json(response_str)
    thought, action = json_response.get("thought"), json_response.get("action")
    observations = f"\nYou said:\n\nThought: {thought}\nAction (code):\n{action}\n\n----------------------------------------\n\n"
    print(observations)
    return action, observations

# --------------------

# Update observations    
def execute_action(action, namespace):
    observations = "I'll now execute the actions (code) you suggested...\n\n"
    print(observations)
    commands = utils.pyparser.parse_code(action)
    for command in commands:
        try:
            f = io.StringIO()
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            tee_stdout = Tee(original_stdout, f)  # Capture both stdout and stderr
            tee_stderr = Tee(original_stderr, f)
            with redirect_stdout(tee_stdout), redirect_stderr(tee_stderr):
                print(f"In [{my_globals.py_counter}]:", command)
                my_globals.py_counter += 1
                exec(command, namespace) 			# Execute in the shared namespace
                print()
        except Exception as e:
            # Write the error message to the same buffer
            with redirect_stdout(tee_stdout), redirect_stderr(tee_stderr):
                print(f"Error: {e}")                
        finally:
            observation = f.getvalue()
            observations += observation
    return observations

# --------------------

def reflect(prompt, state):
    """Handle reflection logic and decide next steps."""
    global retry_counter
    print("Reflecting...")

    my_globals.dialog_so_far.append(prompt)
    response_str = call_gpt4(my_globals.dialog_so_far, response_format="json_object")
    my_globals.dialog_so_far.append(response_str)    
    json_response = utils.utils.clean_extract_json(response_str)
    thought = json_response.get("thought")
    task_complete = json_response.get("task_complete", False)
    current_step_complete = json_response.get("current_step_complete", False)
    next_step_type = json_response.get("next_step_type", "exit")
    observations = f"\nYou said:\n\nThought: {thought}\nOverall task complete? {task_complete}\nCurrent step complete? {current_step_complete}\nNext step type: {next_step_type}\n\n----------------------------------------\n\n"
    print(observations)

    if next_step_type == "exit":
        runtime_seconds = time.time() - my_globals.start_time if my_globals.start_time else None
        runtime = round(runtime_seconds / 60) if runtime_seconds else "?"            
        conclusion = "Research is done!!! Horray!\n"
        conclusion += f"{my_globals.gpt_calls} GPT calls, {my_globals.olmo_calls} OLMo calls, {my_globals.together_calls} Together calls.\n"
        conclusion += f"Runtime: {runtime} minutes.\n"
        print(conclusion)
        # store dialog trace on "exit"
        observations += conclusion
        date_for_filename = datetime.datetime.now().strftime("%m-%d-%Y_%H.%M")                
        trace_filestem = (my_globals.last_report_filestem + "-trace") if my_globals.last_report_filestem else (date_for_filename + "-trace")
        dialog(output_filestem = trace_filestem)
        my_globals.last_report_filestem = None
        state.update(mode="done")
        
    elif next_step_type == "next_step":
        observation = f"Step {state.step_number} complete. Moving onto the next step in the plan...\n"
        observations += observation
        print(observation, sep="")
        retry_counter = 0
        state.update(mode="act", step_number=state.step_number + 1)

    elif next_step_type == "continue":
        observation = f"Step {state.step_number} not yet complete. Let's continue to work on it...\n"
        observations += observation
        print(observation, sep="")
        retry_counter = 0
        state.update(mode="continue")
        
    elif next_step_type == "debug" or next_step_type == "retry":
        if retry_counter >= 3:
            observation = f"Too many retries! I seem to be stuck on step {state.step_number}. Let's abandon this effort and replan.\n"
            print(observation, end="")
            observations += observation
            state.update(mode="replan")
        else:
            retry_counter += 1
            observation = f"An error occurred doing step {state.step_number}. Let's try and debug the problem and retry (retry number {retry_counter}).\n\n"
#           observation = f"An error occured doing step {state.step_number}. Let's try debugging it and try again...\n"
            observations += observation
            print(observation, end="")
            state.update(mode=next_step_type)
    else:
            print(f"ERROR! Unrecognized next_step_type '{next_step_type}'! Yikes!!")
            raise ValueError("next_step_type should be one of 'exit|next_step|continue|debug|retry'")

    return observations

# ======================================================================

class Tee:
    """A helper class to write to multiple streams simultaneously."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
            stream.flush()  # Ensure output is written immediately

    def flush(self):
        for stream in self.streams:
            stream.flush()

