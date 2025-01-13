"""
Reflect
Do a reflection
-------
{...}
-------
Thought:I've done step 3. Move to step 4 (write report)
Now generate an action
----------
{action:"write_report('olmo')"}
----------
Action: ...
Executing...
In [123]: write_report('olmo')
Generating report using GPT:
> Create a title for the report.
afadadsf
> Write a paragraph
...
"""

import my_globals
import os
import time
import datetime
from string import Template		# for write_report()

import utils.utils		# for replace_special_chars_with_ascii

from research_utils.ask_llm import call_gpt4

### --------------------

REPORT_INTRO = """I'm now going to ask you to write a report about the research conducted, section by section.
Before starting, think about what the main conclusions are that you want the report to make, and plan the report contents accordingly so the report is coherent.
The experiments should describe pertinent results supporting the conclusions.
The analysis should describe analytical reflections about the results, for example describing interesting categories of problem/task that provide interesting insights.
As a preview, the report will contain the following sections:
 - title
 - abstract
 - introduction
 - approach
 - results
 - analysis
 - conclusion
I'll now ask you for each section in turn. Just provide the information for the section that I ask for, and nothing else. Do not provide other sections until prompted.
Let's begin!"""

REPORT_PARTS = \
 {"title": "First, create a title for the report.", \
  "abstract": "Write an abstract for the report. State the goal, then the approach, then the findings, then a statement about the significance of the work.", \
  "introduction": "Write an introduction. Describe the motivation for the work, then give an overview of what was done, and finally the main findings.", \
  "approach": "Describe the approach used in detail.", \
  "results": "Describe the experimental results that were obtained.", \
  "analysis": "Write an analysis of the results. Provide illustrative examples in the analysis to make your points clear.", \
  "conclusion": "Summarize conclusions of the research, in particular the main findings."}

### ======================================================================
### 			WRITE A REPORT
### Pass the entire conversation history to GPT to write up the work
### ======================================================================

REPORT_DIR = "output/"
REPORT_HTML_TEMPLATE_FILE = "write_report/report_template.html"
REPORT_TXT_TEMPLATE_FILE = "write_report/report_template.txt"

with open(REPORT_HTML_TEMPLATE_FILE, 'r') as f:
    REPORT_HTML_TEMPLATE = f.read()
with open(REPORT_TXT_TEMPLATE_FILE, 'r') as f:
    REPORT_TXT_TEMPLATE = f.read()    

## Writes report to "output/report_20-12-13_13.43.txt"
def write_report(filename="report"):
    global REPORT_INTRO, REPORT_PARTS
    html_report_template = Template(REPORT_HTML_TEMPLATE)
    txt_report_template = Template(REPORT_TXT_TEMPLATE)    
    report_dialog = my_globals.dialog_so_far.copy()	# the last item in dialog_so_far will be a GPT response
    report_parameters = {}				# empty dict
    print("\nGenerating report using GPT:\n")    
    for section, prompt in REPORT_PARTS.items():
        prompt = (REPORT_INTRO + prompt) if section == "intro" else prompt
        prompt += f"\nReturn exactly and only the {section}, so it can be directly included in the report. Do not return any additional justification or explanation.\n"
        prompt += "If you do any formatting, use HTML markup rather than Markdown (md) markup. e.g., for a numbered list, use <ol><li>...<li>...</ol>."
        report_dialog += [prompt]
        print("------------ Query -----------------------")
        print(prompt)
        print("---------- GPT Reponse  ------------------")
        response0 = call_gpt4(report_dialog)
        response = utils.utils.replace_special_chars_with_ascii(response0)		# get rid of non-ASCII characters that mess up the display
        report_dialog += [response]
        print(response[:70], "...", sep="")
        report_parameters[section] = response

    # Add footnotes
    runtime_seconds = time.time() - my_globals.start_time if my_globals.start_time else None
    runtime = round(runtime_seconds / 60) if runtime_seconds else "?"                
    notes = f"{my_globals.gpt_calls} GPT calls, {my_globals.olmo_calls} OLMo calls, {my_globals.together_calls} Together calls.\n"
    notes += f"Runtime: {runtime} minutes.\n"
    date = datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
    date_for_filename = datetime.datetime.now().strftime("%m-%d-%Y_%H.%M")        
    report_parameters['notes'] = notes
    report_parameters['date'] = date
    report_parameters['underline'] = "=" * len(report_parameters['title'])		# for .txt output
    report_filestem = filename + "_" + date_for_filename

    html_report = html_report_template.substitute(report_parameters)
    html_report_file = my_globals.OUTPUT_DIR + report_filestem + ".html"
    with open(html_report_file, "w") as file:
        file.write(html_report)

    report_parameters = {k: utils.utils.remove_html_markup(v) for k, v in report_parameters.items()}     # strip HTML markup   	
    txt_report = txt_report_template.substitute(report_parameters)
    txt_report_file = my_globals.OUTPUT_DIR + report_filestem + ".txt"
    with open(txt_report_file, "w") as file:
        file.write(txt_report)

    my_globals.last_report_filestem = report_filestem		# for saving the dialog later
#   dialog(output_filestem=report_filestem + "-trace")		# also output the GPT conversation

#   print(utils.utils.remove_html_markup(html_report))
    print(txt_report)
    print("======================================================================")        

    return

### ======================================================================
###		print out the dialog so far
### ======================================================================

### dialog(["You are a smart assistant.","What is 1+1?","2","What is 2+3?"])
### dialog(output_filestem="report-trace")
def dialog(dialog=None, show_system_prompt=False, output_dir=my_globals.OUTPUT_DIR, output_filestem=None):
    if dialog is None:
        dialog = my_globals.dialog_so_far  # Dynamically assign the current value

    output_to_file = output_filestem is not None
    output_file_path = None

    if output_to_file:
        if not output_dir:
            raise ValueError("output_dir must be provided if output_filestem is specified.")
        # Create output directory if it does not exist
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, f"{output_filestem}.txt")

    # Open the file for writing if output_to_file is True
    with open(output_file_path, 'w') if output_to_file else open(os.devnull, 'w') as file:
        output = file if output_to_file else None

        def write_output(text):
            if output_to_file:
                output.write(text + "\n")
            else:
                print(text)

        write_output("======================================================================")
        write_output("\t\t\tSYSTEM PROMPT")
        write_output("======================================================================")
        write_output("")

        if show_system_prompt:
            write_output(dialog[0])
        else:
            write_output("...<system prompt>...")

        write_output("")
        # Loop over every 2 items starting at index 1
        for i in range(1, len(dialog), 2):
            write_output("======================================================================")
            write_output("\t\t\tAUTONORA")
            write_output("======================================================================")
            write_output(dialog[i])

            if i + 1 < len(dialog):  # Check if the next item exists
                write_output("======================================================================")
                write_output("\t\t\t   GPT")
                write_output("======================================================================")
                write_output(dialog[i + 1])

