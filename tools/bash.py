## bash.py
import asyncio
from pathlib import Path
from turtle import st
from typing import ClassVar, Literal
from anthropic.types.beta import BetaToolBash20241022Param
from networkx import jaccard_coefficient
# from torch import error
from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
import platform
# Using subprocess directly for shell commands
from rich import print as rr
import re
import os
import shlex
from anthropic import Anthropic
import subprocess
import sys
import io
import traceback
# adding the following import to fix this error "NameError: name 'datetime' is not defined. Did you forget to import 'datetime'"
from datetime import datetime
PROMPT_FILE = Path(r"C:\mygit\compuse\computer_use_demo\tools\bash.md")

def read_prompt_from_file(file_path: str, bash_command: str) -> str:
    """Read the prompt template from a file and format it with the given bash command."""
    prompt_string = f"""You are a highly skilled assistant specializing in converting Linux Bash commands into equivalent Python scripts or PowerShell scripts. Your task is to generate code that performs the same operation as the given Bash command. Follow these instructions carefully:
    Input: You will receive a single Bash command as input.
    Output Options:
    Option A: A Python script that performs the equivalent action.
    Option B: A PowerShell script that performs the equivalent action.
    Requirements:
    DO NOT USE sys.exit() or any other method that terminates the script execution
    If the command involves file or directory operations (e.g., mkdir, touch, rm, cp), ensure that the script includes error handling (e.g., checking if a file or directory exists before performing the operation).
    If the command involves nested or complex structures (e.g., mkdir -p /path/<dir1,dir2>), expand the structure into individual operations.
    If the command involves environment-specific behavior (e.g., activating a virtual environment), adapt the script to the target platform (Windows for PowerShell, cross-platform for Python).
    Remember, you are working in Window's, so whenever you see a the letter c near the beginning of a Path, it is a typo and use the C drive in it's place.
    You should use the pathlib in your python code to help you create the proper paths.
    Always use full absolute paths including the drive.
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
    Important Notes:
    Ensure the generated script is valid and executable.
    Ensure that the python code handles errors in a way that will allow the execution of the main program to continue.
    Avoid unnecessary complexity; keep the script concise and readable.
    If the Bash command is invalid or unsupported, return an error message explaining why.
    Input: {bash_command}
    Output: """
    rr("Prompt")
    return prompt_string

async def generate_script_with_llm(prompt: str) -> str:
    """Send a prompt to the LLM and return its response."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        # rr(f" {prompt} ")
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-latest",  # Updated to use Claude 3.5 Haiku
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

        )
        rr(f"Raw Content:   {response.content[0].text}")
        return response.content[0].text
    except Exception as e:
        raise ToolError(f"Error during LLM API call: {e}")

def parse_llm_response(response: str):
    """Parse the LLM response to extract the script."""
    match = re.search(
        r"(Python Script|PowerShell Script):\n```(?:python|powershell)?\n(.*?)\n```",
        response, re.DOTALL
    )
    if not match:
        raise ValueError("No valid script found in the response.")
    
    script_type = match.group(1)
    script_code = match.group(2).strip()
    rr(f"script_type: {script_type}")
    rr(f"script_code: {script_code}")
    return script_type, script_code

def execute_script(script_type: str, script_code: str):
    """Execute the extracted script and capture output and errors."""
    if script_type == "Python Script":
        rr("Executing Python script...")
        # Redirect stdout and stderr
        old_stdout, old_stderr = sys.stdout, sys.stderr
        redirected_output = io.StringIO()
        redirected_error = io.StringIO()
        sys.stdout, sys.stderr = redirected_output, redirected_error
        
        try:
            exec(script_code)
            output_out = redirected_output.getvalue()
            error_out = redirected_error.getvalue()
            
            # Save successful code
            if not error_out:
                saved_path = save_successful_code(script_code)
                output_out += f"\nCode saved to: {saved_path}"
                
        except Exception as e:
            output_out = ""
            error_out = f"Error: {str(e)}\n{traceback.format_exc()}"
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr        
        rr(f"Output: {output_out}")
        rr(f"Error: {error_out}")
        return {"success": True if not error_out else False, "output": output_out, "error": error_out}

    elif script_type == "PowerShell Script":
        rr("Executing PowerShell script...")
        script_file = "temp_script.ps1"
        with open(script_file, "w") as f:
            f.write(script_code)
        output=""
        try:
            result = subprocess.run(
                ["powershell.exe", "-File", script_file],
                capture_output=True, text=True, check=True
            )
            output = result.stdout
            error = result.stderr
            success = True
        except subprocess.CalledProcessError as e:
            output = e.stdout
            error = e.stderr
            success = False
        except Exception as e:
            output = ""
            error = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            success = False
        finally:
            if os.path.exists(script_file):
                os.remove(script_file)
        
        rr(f"Output: {output}")
        rr(f"Error: {error}")
        return {"success": success, "output": output, "error": error}

    else:
        raise ValueError(f"Unsupported script type: {script_type}")
# from loop_gfix import get_workspace_dir

class BashTool(BaseAnthropicTool):
    description="""
    A tool that allows the agent to run bash commands. On Windows it uses PowerShell
    The tool parameters are defined by Anthropic and are not editable.
    """

    name: ClassVar[Literal["bash"]] = "bash"
    api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"

    async def __call__(
        self, command: str | None = None, **kwargs
    ):
        if command is not None:
            return await self._run_command(command)
        raise ToolError("no command provided.")

    async def _run_command(self, command: str):
        """Execute a command in the shell."""
        try:
            prompt = read_prompt_from_file(PROMPT_FILE, command)
            rr(f"[red]{'*' * 80}[/red]")
            response = await generate_script_with_llm(prompt)
            script_type, script_code = parse_llm_response(response)
            result = execute_script(script_type, script_code)
            
            # Normalize output format
            if isinstance(result, dict):
                output = f"output: {result['output']}\nerror: {result['error']}"
            else:
                output = result
                
            return ToolResult(output=output)
        except Exception as e:
            return ToolError(output=output, error=str(e))
    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }   
    


def save_successful_code(script_code: str) -> str:
    """Save successfully executed Python code to a file."""
    # Create directory if it doesn't exist
    save_dir = Path("./llm_gen_code")
    save_dir.mkdir(exist_ok=True)
    
    # Extract first line of code for filename (cleaned)
    first_line = script_code.split('\n')[0].strip()
    # Clean the first line to create a valid filename
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', first_line)[:30]
    
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_{timestamp}.py"
    
    # Save the code
    file_path = save_dir / filename
    with open(file_path, 'w') as f:
        f.write(script_code)
    
    return str(file_path)
