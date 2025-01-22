import asyncio
from pathlib import Path
from typing import ClassVar, Literal
from anthropic.types.beta import BetaToolBash20241022Param
import re
import os
import subprocess
import sys
import io
import traceback
from datetime import datetime
from anthropic import Anthropic

from .base import BaseAnthropicTool, ToolError, ToolResult
from utils.agent_display import AgentDisplay  # Add this line
from load_constants import WORKER_DIR, write_to_file
from icecream import ic
from config import BASH_PROMPT_FILE, get_constant

ic.configureOutput(includeContext=True, outputFunction=write_to_file)



def read_prompt_from_file(file_path: str, bash_command: str) -> str:
    """Read the prompt template from a file and format it with the given bash command."""
    project_dir = Path(get_constant("PROJECT_DIR"))
    with open(file_path, "r") as file:
        prompt_string = file.read()
    prompt_string += f"Your project directory is {project_dir}. You need to make sure that all files you create and work you do is done in that directory. \n"
    prompt_string += f"Your bash command is: {bash_command}\n"
    temp= input(f" The prompt is: {prompt_string}")
    return prompt_string

async def generate_script_with_llm(prompt: str) -> str:
    """Send a prompt to the LLM and return its response."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        ic(prompt)
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
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
    match = re.search(
        r"(Python Script|PowerShell Script):\n```(?:python|powershell)?\n(.*?)\n```",
        response,
        re.DOTALL,
    )
    if not match:
        raise ValueError("No valid script found in the response.")
    script_type = match.group(1)
    script_code = match.group(2).strip()
    ic(f"script_type: {script_type}")
    ic(f"script_code: {script_code}")
    return script_type, script_code


def execute_script(script_type: str, script_code: str, display: AgentDisplay = None):
    """Execute the extracted script and capture output and errors."""
    output = ""

    if script_type == "Python Script":
        if display:
            display.add_message("user", "Executing Python script...")

        # Write the Python script to a temporary file
        script_file = "temp_script.py"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_code)

        try:
            # Use subprocess to run the Python script
            result = subprocess.run(
                ["python", script_file],
                capture_output=True,
                text=True,
                check=False  # Don't automatically raise CalledProcessError
            )
            output_out = result.stdout
            error_out = result.stderr

            # Decide success based on return code
            success = (result.returncode == 0)

            # Send output to the display
            if display:
                if output_out:
                    display.add_message("user", f"Output:\n{output_out}")
                if error_out:
                    display.add_message("user", f"Error Message:\n{error_out}")

        except Exception as e:
            # Catch any unexpected Python-level errors from subprocess itself
            output_out = ""
            error_out = f"Error: {str(e)}\n{traceback.format_exc()}"
            success = False
            if display:
                display.add_message("user", f"Execution Error:\n{error_out}")
        finally:
            # Clean up the temporary file
            if os.path.exists(script_file):
                os.remove(script_file)

        return {
            "success": success,
            "output": output_out,
            "error": error_out
        }

    elif script_type == "PowerShell Script":
        if display:
            display.add_message("user", "Executing PowerShell script...")

        script_file = "temp_script.ps1"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_code)

        try:
            result = subprocess.run(
                ["powershell.exe", "-File", script_file],
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout
            error = result.stderr
            success = (result.returncode == 0)

            if display and output:
                display.add_message("user", f"PowerShell Output:\n{output}")
            if display and error:
                display.add_message("user", f"PowerShell Errors:\n{error}")

        except Exception as e:
            output = ""
            error = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            success = False
            if display:
                display.add_message("user", f"Unexpected Error:\n{error}")
        finally:
            if os.path.exists(script_file):
                os.remove(script_file)

        return {
            "success": success,
            "output": output,
            "error": error
        }

    else:
        error_msg = f"Unsupported script type: {script_type}"
        if display:
            display.add_message("user", f"Error: {error_msg}")
        raise ValueError(error_msg)


class BashTool(BaseAnthropicTool):
    def __init__(self, display: AgentDisplay = None):
        self.display = display
        super().__init__()
        
    description = """
        A tool that allows the agent to run bash commands. On Windows it uses PowerShell
        The tool parameters are defined by Anthropic and are not editable.
        """

    name: ClassVar[Literal["bash"]] = "bash"
    api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"

    async def __call__(self, command: str | None = None, **kwargs):
        if command is not None:
            return await self._run_command(command)
        raise ToolError("no command provided.")

    async def _run_command(self, command: str):
        """Execute a command in the shell."""
        BASH_PROMPT_FILE= get_constant("BASH_PROMPT_FILE")
        output = ""
        try:
            if self.display:
                self.display.add_message("user", f"Processing command: {command}")

            prompt = read_prompt_from_file(BASH_PROMPT_FILE, command)
            response = await generate_script_with_llm(prompt)
            script_type, script_code = parse_llm_response(response)

            # Pass the display to execute_script
            result = execute_script(script_type, script_code, self.display)

            if isinstance(result, dict):
                output = f"output: {result['output']}\nerror: {result['error']}"
            else:
                output = result
            return ToolResult(output=output)
        except Exception as e:
            if self.display:
                self.display.add_message("user", f"Error: {str(e)}")
            return ToolError(str(e))

    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }


def save_successful_code(script_code: str) -> str:
    """Save successfully executed Python code to a file."""
    # Create directory if it doesn't exist
    llm_gen_code_dir = Path(get_constant("LLM_GEN_CODE_DIR"))
    save_dir = llm_gen_code_dir
    save_dir.mkdir(exist_ok=True)
    ic(script_code)
    # Extract first line of code for filename (cleaned)
    first_line = script_code.split("\n")[0].strip()
    # Clean the first line to create a valid filename
    clean_name = re.sub(r"[^a-zA-Z0-9]", "_", first_line)[:30]

    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_{timestamp}.py"

    # Save the code
    file_path = save_dir / filename
    with open(file_path, "w") as f:
        f.write(script_code)

    return str(file_path)
