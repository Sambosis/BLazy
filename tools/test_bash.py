import os
import re
import subprocess
import sys
import io
import traceback
from typing import Dict, Any
from pathlib import Path
from rich import print as rr
from dotenv import load_dotenv
import openai
from openai import OpenAI
# Load environment variables
load_dotenv()
bash_command_function = {
    "name": "bash_command",
    "description": "Run commands in a bash shell. When invoking this tool, the contents of the 'command' parameter does NOT need to be XML-escaped. You have access to a mirror of common linux and python packages via apt and pip. State is persistent across command calls and discussions with the user. To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'. Please avoid commands that may produce a very large amount of output. Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to be executed."
            }
        },
        "required": ["command"]
    }
}
# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def read_prompt_from_file(bash_command: str) -> str:
    """Read the prompt template from a file and format it with the given bash command."""
    prompt_string = f"""You are a highly skilled assistant specializing in converting Linux Bash commands into equivalent Python scripts or PowerShell scripts. Your task is to generate code that performs the same operation as the given Bash command. Follow these instructions carefully:
    Input: You will receive a single Bash command as input.
    Output Options:
    Option A: A Python script that performs the equivalent action.
    Option B: A PowerShell script that performs the equivalent action.
    Requirements:
    If the command involves file or directory operations (e.g., mkdir, touch, rm, cp), ensure that the script includes error handling (e.g., checking if a file or directory exists before performing the operation).
    If the command involves nested or complex structures (e.g., mkdir -p /path/<dir1,dir2>), expand the structure into individual operations.
    If the command involves environment-specific behavior (e.g., activating a virtual environment), adapt the script to the target platform (Windows for PowerShell, cross-platform for Python).
    Include comments in the generated script to explain each step.
    Output Format:
    Clearly label the output as either "Python Script" or "PowerShell Script."
    Provide the complete script in a code block.
    Examples:
    Input: mkdir -p /repo/dish_tracker/<static/<css,js>,templates,models>
    Python Script:
    import os

    paths = [
        "/repo/dish_tracker/static/css",
        "/repo/dish_tracker/static/js",
        "/repo/dish_tracker/templates",
        "/repo/dish_tracker/models"
    ]

    for path in paths:
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: <path>")


    Input: touch /repo/dish_tracker/app.py /repo/dish_tracker/config.py
    Python Script:
    files = [
        "/repo/dish_tracker/app.py",
        "/repo/dish_tracker/config.py"
    ]
    for file in files:
        with open(file, 'a'):
            os.utime(file, None)
        print(f"Created or updated file: <file>")
    PowerShell Script:
    $files = @(
        "C:\\repo\\dish_tracker\\app.py",
        "C:\\repo\\dish_tracker\\config.py"
    )

    foreach ($file in $files) <
        if (-Not (Test-Path $file)) <
            New-Item -ItemType File -Path $file
        > else <
            (Get-Item $file).LastWriteTime = Get-Date
        >
        Write-Host "Created or updated file: $file"
    >
    Ensure that the execution of the script will not halt further commands from running when necessary.
    For example, if you need to run a flask app do something like this:
import os
import subprocess

try:
    # Change to the specified directory
    os.chdir("C:/repo/algebra")
    print("Changed directory to C:/repo/algebra")

    # Run the Python script in the background with output redirection
    with open('flask.log', 'w') as log_file:
        process = subprocess.Popen(
            ["python", "app.py"],
            stdout=log_file,
            stderr=log_file,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    print(f"Python script app.py is running in the background with PID: process.pid")
    print("Flask logs are being written to flask.log")

except Exception as e:
    print(f"An error occurred: e")
    Important Notes:
    Ensure the generated script is valid and executable.
    Avoid unnecessary complexity; keep the script concise and readable.
    If the Bash command is invalid or unsupported, return an error message explaining why.
    Input: {bash_command}
    Output: """
    rr("Prompt")
    return prompt_string

def generate_script_with_llm(prompt: str) -> str:
    """Send a prompt to the OpenAI API and return its response."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"Error during OpenAI API call: {e}")

def parse_llm_response(response: str):
    """Parse the LLM response to extract the script.
    
    Args:
        response (str): The full response from the LLM containing code blocks
        
    Returns:
        tuple: (script_type, script_code) where script_type is either 
               'Python Script' or 'PowerShell Script'
               
    Raises:
        ValueError: If no valid script found in response
    """
    # First try to determine the script type
    if "Python Script:" in response:
        script_type = "Python Script"
    elif "PowerShell Script:" in response:
        script_type = "PowerShell Script"
    else:
        raise ValueError("No script type identifier found in response")

    # Extract the code block
    match = re.search(
        r"```(?:python|powershell)?\n(.*?)\n```",
        response, 
        re.DOTALL
    )
    
    if not match:
        raise ValueError("No valid code block found in the response")
    
    script_code = match.group(1).strip()
    rr(f"script_type: {script_type}")
    rr(f"script_code: {script_code}")
    
    return script_type, script_code

def execute_script(script_type: str, script_code: str) -> Dict[str, str]:
    """Execute the extracted script and capture output and errors."""
    if script_type == "Python Script":
        rr("Executing Python Script...")
        old_stdout, old_stderr = sys.stdout, sys.stderr
        redirected_output = io.StringIO()
        redirected_error = io.StringIO()
        sys.stdout, sys.stderr = redirected_output, redirected_error
        
        try:
            # Write the script to a temporary file
            with open("temp_script.py", "w") as temp_file:
                temp_file.write(script_code)
            
            # Execute the script using subprocess
            result = subprocess.run(
                ["python", "temp_script.py"],
                capture_output=True,
                text=True
            )
            output = result.stdout
            error = result.stderr
        except Exception as e:
            error = f"Error: {str(e)}\n{traceback.format_exc()}"
            output = ""
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            # Clean up the temporary file
            if os.path.exists("temp_script.py"):
                os.remove("temp_script.py")
        
        return {"output": output, "error": error}

    elif script_type == "PowerShell Script":
        rr("Executing PowerShell Script...")
        with open("script.ps1", "w") as f:
            f.write(script_code)
        try:
            result = subprocess.run(["powershell.exe", "-File", "script.ps1"], capture_output=True, text=True, check=True)
            return {"output": result.stdout, "error": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"output": e.stdout, "error": e.stderr}
    else:
        raise ValueError(f"Unsupported script type: {script_type}")
    
def bash_command(command: str) -> Dict[str, Any]:
    """Execute a bash command by converting it to a Python or PowerShell script."""
    try:
        rr("command: ", command)
        prompt = read_prompt_from_file(command)
        # rr("prompt: ", prompt)
        response = generate_script_with_llm(prompt)
        rr("response: ", response)
        script_type, script_code = parse_llm_response(response)
        rr("script_type: ", script_type)
        rr("script_code: ", script_code)
        result = execute_script(script_type, script_code)
        return {"output": result["output"], "error": result["error"]}
    except Exception as e:
        return {"error": str(e)}

