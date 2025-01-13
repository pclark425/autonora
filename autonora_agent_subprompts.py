
#======================================================================
#	PLAN SUBPROMPT
#======================================================================

PLAN_SUBPROMPT = """
Okay! We are ready to get started on a new research task!

Your top-level research task is: {task}

YOUR NEXT INSTRUCTION: generate a plan to perform this research. Return your plan as a JSON object with the following structure:
{{"plan": [{{"step_number":1, "step":DESCRIPTION}}, {{"step_number":2, "step":DESCRIPTION}}, ....]}}
"""

#======================================================================
#	REPLAN SUBPROMPT
#======================================================================

REPLAN_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

According to your last reflection, it looks like the current plan isn't working.

YOUR NEXT INSTRUCTION: Generate a revised plan to perform the research task.
You don't need to repeat steps that were already performed successfully, i.e., the new plan should start from the current state of your research, rather than start from scratch.
You can reuse variables and data structures from the earlier execution, if that is helpful.
I will then discard the old plan, and continue with your revised plan.

Return your revised plan as a JSON object with the following structure:
{{"plan": [{{"step_number":1, "step":DESCRIPTION}}, {{"step_number":2, "step":DESCRIPTION}}, ....]}}
"""

#======================================================================
#	FIRST ACTION SUBPROMPT
#======================================================================

FIRST_ACTION_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

Here is the current plan we are following:
{formatted_plan}

We will start with the first step, step {step_number}: {step_description}

YOUR NEXT INSTRUCTION: Generate Python code that implements this step. I'll then execute it and show you the results.
Return your answer as a JSON object of the form:
      {{"thought":THOUGHT, "action":PYTHON_CODE}}
"""

#======================================================================
#	NEXT ACTION SUBPROMPT
#======================================================================

NEXT_ACTION_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

Here is the current plan we are following:
{formatted_plan}

We have successfully completed step number {prev_step_number}.
We will now move to step {step_number}: {step_description}

YOUR NEXT INSTRUCTION: Generate Python code that implements this step. I'll then execute it and show you the results.
Return your answer as a JSON object of the form:
      {{"thought":THOUGHT, "action":PYTHON_CODE}}
"""

#======================================================================
#	CONTINUE ACTION SUBPROMPT
#======================================================================

CONTINUE_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

Here is the current plan we are following:
{formatted_plan}

We are currently on step {step_number}: {step_description}

According to your last reflection, the step is only partially completed. 

YOUR NEXT INSTRUCTION: Generate Python code that completes this step. I'll then execute it and show you the results.
Return your answer as a JSON object of the form:
      {{"thought":THOUGHT, "action":PYTHON_CODE}}
"""

#======================================================================
#	DEBUG SUBPROMPT
#======================================================================

DEBUG_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

Here is the current plan we are following:
{formatted_plan}

We are currently on step {step_number}: {step_description}

According to your last reflection, there was a problem implementing/executing this step.

YOUR NEXT INSTRUCTION: Try again, and generate new Python code that implements this step. Pay particular
attention to avoid the problem that occurred last time. I'll then execute it and show you the results.
Return your answer as a JSON object of the form:
      {{"thought":THOUGHT, "action":PYTHON_CODE}}
"""

#======================================================================
#	REFLECTION SUBPROMPT
#======================================================================

REFLECTION_SUBPROMPT = """
As a reminder, your top-level research task is: {task}

Here is the current plan we are following:
{formatted_plan}

We are currently on step {step_number}: {step_description}

YOUR NEXT INSTRUCTION: Perform a REFLECTION step to assess if top-level task is complete, the current plan step is complete, and what to do next.

Assess:
 - thought: Summarize the progress made so far in the research, and what to do next
 - task_complete: Have you achieved the top-level research task?
 - current_step_complete: Have you successfully completed the current step in the plan?
 - next_step_type:
     - If task_complete is true, then 'exit' 
     - If current_step_complete is true, then 'next_step'
     - If the current step was only partially completed, then 'continue'
     - If there was a Python error, and it seems fixable, then 'debug'
     - If you seem to be stuck, looping, or going around in circles, then 'retry'
     
Return the results as a JSON structure of the form:
   {{"thought": STRING, "task_complete": BOOLEAN, "current_step_complete": BOLEAN, "next_step_type": one of 'exit', 'next_step', 'continue', 'debug', or 'retry'}}
"""


