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
from rich import print as rr
import re
import os
import shlex
from anthropic import Anthropic
import subprocess
import sys
import io
import traceback
from load_constants import PROJECT_DIR
from load_constants import WORKER_DIR, ICECREAM_OUTPUT_FILE, write_to_file
from icecream import ic
ic.configureOutput(includeContext=True, outputFunction=write_to_file)
# adding the following import to fix this error "NameError: name 'datetime' is not defined. Did you forget to import 'datetime'"
from datetime import datetime
PROMPT_FILE = Path(r"C:\mygit\compuse\computer_use_demo\tools\bash.md")

def read_prompt_from_file(file_path: str, bash_command: str) -> str:
    """Read the prompt template from a file and format it with the given bash command."""
    prompt_string = f"""You are an expert in converting Bash commands that use 'uv' (a hypothetical package manager and project tool) into Python scripts. The user will provide one or more 'uv' commands (like 'uv init', 'uv venv', 'uv pip install requests', 'uv run python my_script.py'), and your job is to create a single Python script that replicates those operations step-by-step.

    Key Instructions:
    1. The input is a sequence of 'uv' commands that might include:
    • uv init
    • uv venv
    • uv add <dependency>
    • uv pip <pip_action> ...
    • uv run python ...
    • Or any other 'uv' commands

    2. Generate a Python script that performs an equivalent series of steps:
    • If the command is 'uv init', it might set up a project directory or initialize something in Python code.
    • If the command is 'uv venv', it should create or activate a Python virtual environment in a cross-platform-friendly way using Python.
    • If the command is 'uv pip install <package>', then your Python script should install that package. Show how to do it programmatically (e.g., using subprocess to call pip, or some other approach that doesn’t terminate the script).
    • If the command is 'uv run python <script>.py', your Python script should execute the target Python file or code with arguments as needed (again, show this via Python’s built-in modules, like subprocess, but do not exit the script prematurely).

    3. DO NOT use sys.exit() or any other command that terminates the script execution prematurely.
    4. Include comments that explain each step of the generated Python script.
    5. If the commands involve file or directory operations (like setting up directories or copying files), include error handling (e.g., checking if a directory already exists before creating it).
    6. Your output must be labeled as “Python Script:” followed by a code block containing the full Python code.
    7. If the input Bash command or 'uv' command sequence is invalid or unsupported, return a short error description.
    8. The project directory is {PROJECT_DIR} and that you should use the absolute path at all times to avoid conflicts. 
    Example usage of 'uv' commands and their equivalent Python script:

    Input (Bash commands):
        mkdir myproject
        cd myproject
        uv venv
        .venv\\Scripts\\activate
        uv init
        uv add requests rich python-dotenv

    Python Script:
    ```python
    import subprocess
    from pathlib import Path
    import os

    def run_command(cmd, cwd=None):
        try:
            subprocess.run(cmd, check=True, shell=True, cwd=cwd)
            print(f"Successfully executed: {{cmd}}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing {{cmd}}: {{e}}")

    # Get current working directory and create project path
    current_dir = Path.cwd()
    project_dir = current_dir / "myproject"

    # Create project directory
    try:
        project_dir.mkdir(exist_ok=True)
        print(f"Created project directory: {PROJECT_DIR}")
    except Exception as e:
        print(f"Error creating project directory: {{e}}")

    # Change to project directory
    try:
        os.chdir(project_dir)
        print(f"Changed directory to: {PROJECT_DIR}")
    except Exception as e:
        print(f"Error changing directory: {{e}}")

    # Create virtual environment using uv
    run_command("uv venv")

    # Activate virtual environment
    venv_activate_path = project_dir / ".venv" / "Scripts" / "activate"
    if os.name == 'nt':  # Windows
        activate_cmd = f"call {{venv_activate_path}}"
    else:  # Unix-like
        activate_cmd = f"source {{venv_activate_path}}"

    # Initialize project with uv
    run_command("uv init")

    # Install packages
    packages = ["requests", "rich", "python-dotenv"]
    for package in packages:
        run_command(f"uv add {{package}}")

    print(f"\\nProject setup complete in {PROJECT_DIR}")
    print("To activate the virtual environment, run:")
    print(f"{{activate_cmd}}")

    Important Notes:
    • Always handle paths cross-platform using pathlib, and adapt to Windows by replacing leading 'c' with drive 'C:' if needed.
    • Avoid terminating the script with exit commands.
    • Keep the final script concise and readable.
    • Output must be valid Python code in a code block labeled as Python Script.
    Input: {bash_command}
    Output:
    """
    # rr("Prompt")
    ic(bash_command)
    return prompt_string

async def generate_script_with_llm(prompt: str) -> str:
    """Send a prompt to the LLM and return its response."""
    try:
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        ic(prompt)
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
        ic(response.content[0].text)
        return response.content[0].text
    except Exception as e:
        raise ToolError(f"Error during LLM API call: {e}")

def parse_llm_response(response: str):
    """Parse the LLM response to extract the script."""
    # rr(response)
    match = re.search(
        r"(Python Script|PowerShell Script):\n```(?:python|powershell)?\n(.*?)\n```",
        response, re.DOTALL
    )
    if not match:
        raise ValueError("No valid script found in the response.")
    
    script_type = match.group(1)
    script_code = match.group(2).strip()
    ic(f"script_type: {script_type}")
    ic(f"script_code: {script_code}")
    return script_type, script_code

def execute_script(script_type: str, script_code: str):
    """Execute the extracted script and capture output and errors."""
    output=""

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
        
        ic(f"Output: {output}")
        ic(f"Error: {error}")
        return {"success": success, "output": output, "error": error}

    else:
        raise ValueError(f"Unsupported script type: {script_type}")
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
        output=""
        try:
            prompt = read_prompt_from_file(PROMPT_FILE, command)
            # rr(f"[red]{'*' * 80}[/red]")
            response = await generate_script_with_llm(prompt)
            script_type, script_code = parse_llm_response(response)
            result = execute_script(script_type, script_code)
            ic(result)
            # Normalize output format
            if isinstance(result, dict):
                output = f"output: {result['output']}\nerror: {result['error']}"
            else:
                output = result
                
            return ToolResult(output=output)
        except Exception as e:
            return ToolError(str(e))
    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }   
    


def save_successful_code(script_code: str) -> str:
    """Save successfully executed Python code to a file."""
    # Create directory if it doesn't exist
    save_dir = WORKER_DIR / "llm_gen_code"
    save_dir.mkdir(exist_ok=True)
    ic(script_code)
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
