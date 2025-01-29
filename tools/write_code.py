from enum import Enum
from typing import Literal, Optional, List
from pathlib import Path
from .base import ToolResult, BaseAnthropicTool
import os
import subprocess
from icecream import ic
from rich import print as rr
import json
from pydantic import BaseModel
import tempfile
from config import get_constant, set_constant, PROJECT_DIR, LOGS_DIR
from openai import OpenAI
from utils.file_logger import log_file_operation, get_all_current_code
import time
class CodeCommand(str, Enum):
    WRITE_CODE_TO_FILE = "write_code_to_file"
    WRITE_AND_EXEC = "write_and_exec"
import re
class WriteCodeTool(BaseAnthropicTool):
    """
    A tool that sets up Python projects with virtual environments and manages script execution.
    """

    name: Literal["write_code"] = "write_code"
    api_type: Literal["custom"] = "custom"
    description: str = "A tool that takes a description of python code and provides the actual python code. It can either execute the code or write it to a file depending on the command."

    def __init__(self, display=None):
        super().__init__(display)

    def to_params(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.api_type,
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": [cmd.value for cmd in CodeCommand],
                        "description": "Command of what to do with the code: write_code_to_file or write_and_exec"
                    },
                    "code_description": {
                        "type": "string",
                        "description": "A detailed description of the code to be written. In must specify any additional imports, classes, functions, etc. that should be included in the code. It also will need to know what files it may need to interact with, their paths and the direectory structure. It should also give a brief description of the project as a whole, while being clear about the scope of the code that it needs to write."
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    },
                    "python_filename": {
                        "type": "string",
                        "description": "The filename of the python file to write the code to.  This is onluly needed if the command is write_code_to_file, but if write_code_to_file is the command, this is required."
                    }
                },
                "required": ["command", "code_description", "project_path"]
            }
        }

    async def __call__(
        self,
        *,
        command: CodeCommand,
        code_description: str,
        project_path: str = PROJECT_DIR,
        python_filename: str = "you_need_to_name_me.py",
        **kwargs,
        ) -> ToolResult:
        """
        Executes the specified command for project management.
        """
        try:
            if self.display:
                self.display.add_message("tool", f"WriteCodeTool Instructions: {code_description}")

            # Convert path string to Path object
            project_path = Path(get_constant("PROJECT_DIR"))
            # Execute the appropriate command
            if command == CodeCommand.WRITE_CODE_TO_FILE:
                result_data = await self.write_code_to_file(code_description, project_path, python_filename)
            elif command == CodeCommand.WRITE_AND_EXEC:
                result_data = await self.write_and_exec(code_description, project_path)

            else:
                return ToolResult(error=f"Unknown command: {command}")

            # Convert result_data to formatted string
            formatted_output = self.format_output(result_data)

            if self.display:
                self.display.add_message("tool", f"WriteCodeTool completed: {formatted_output}")
            return ToolResult(output=formatted_output)

        except Exception as e:
            if self.display:
                self.display.add_message("tool", f"WriteCodeTool error: {str(e)}")
            error_msg = f"Failed to execute {command}: {str(e)}"
            
            return ToolResult(error=error_msg)

    async def _call_llm_to_generate_code(self, code_description: str) -> str:
        """Call LLM to generate code based on the code description.
        This method uses OpenRouter API to generate code based on a provided description.
        It includes the current codebase context in the prompt and formats the response
        as Python code.
        Args:
            code_description (str): A detailed description of the code to be generated
        Returns:
            str: Generated Python code string, extracted from markdown code block if present
        Raises:
            Potential OpenAI API exceptions are not explicitly handled
        Notes:
            - Requires OPENROUTER_API_KEY environment variable
            - Logs messages to code_messages.json
            - Uses google/gemini-2.0-flash-exp:free model
            - Includes a 5 second delay before API call
        """
        """Call LLM to generate code based on the code description"""
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        current_code_base = get_all_current_code()
        client = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=OPENROUTER_API_KEY)
        messages=[
                {
                "role": "system",
                "content": [
                    {
                    "type": "text",
                    "text": "Your are an expert with software engineer and proud coder.  You are make carefully designed programs that work on the first try and take the whole scope of the program into consideration when creating a piece of code."
                    },
                    ],
                "role": "user",
                "content": 
                [
                    {
                    "type": "text",
                    "text": f"""At the bottom is a detailed description of code that you need to write.  Your response should include everything needed in order to run the file including imports that will be needed. All of the code that you provide needs to be enclosed inside of xml style tags like this:
                    <PYTHON>
                    your code here
                    </PYTHON>
                    You will use the <TYPE OF CODE HERE> </TYPE OF CODE HERE>tags even if you are creating code in a different language such as openscad.
                    
                    Here is all of the code that has been created for the project so far:
                    {current_code_base}
                    
                    Here is the description of the code:
                    {code_description}"""
                    },
                ]
                }
            ]
        # append messages to a file called ages.log
        LOGS_DIR = Path(get_constant("LOGS_DIR"))


        self.display.add_message("user", f"Sending messages to OpenAI: {current_code_base}")
        # give a delay
        completion = client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free",
        messages=messages
        )
        code_string = completion.choices[0].message.content
                # Extract just the Python code from markdown code block if present
        code_string = self.extract_code(code_string)
        CODE_FILE = LOGS_DIR / "code_messages.py"
        with open(CODE_FILE, "a") as f:
            # write code_string to the file
            f.write(f"\n{code_string}\n")
            
        return code_string

    def extract_code(self, code_string: str) -> str:
        """Extract code from string containing XML tags and/or markdown code blocks."""
        
        # Define regex patterns for any language
        xml_pattern = re.compile(r"<(\w+)>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
        markdown_pattern = re.compile(r"```(\w+)\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
        
        # First, attempt to extract code within XML tags
        xml_match = xml_pattern.search(code_string)
        if xml_match:
            extracted = xml_match.group(2).strip()
            # Within the extracted XML content, check for markdown code fences
            markdown_match = markdown_pattern.search(extracted)
            if markdown_match:
                return markdown_match.group(2).strip()
            return extracted
        
        # If no XML tags, attempt to extract markdown code fences
        markdown_match = markdown_pattern.search(code_string)
        if markdown_match:
            return markdown_match.group(2).strip()
        
        # If neither tags nor code fences are found, return the original string
        return code_string
    def format_output(self, data: dict) -> str:
        """Format the output data as a readable string"""
        output_lines = []
        
        # Add command type
        output_lines.append(f"Command: {data['command']}")
        
        # Add status
        output_lines.append(f"Status: {data['status']}")
        
        # Add project path
        output_lines.append(f"Project Path: {data['project_path']}")
        
        # Add packages if present
        if 'packages_installed' in data:
            output_lines.append("Packages Installed:")
            for package in data['packages_installed']:
                output_lines.append(f"  - {package}")
        
        # Add run output if present
        if 'run_output' in data and data['run_output']:
            output_lines.append("\nApplication Output:")
            output_lines.append(data['run_output'])
        
        if 'errors' in data and data['errors']:
            output_lines.append("\nErrors:")
            output_lines.append(data['errors'])
        
        # Join all lines with newlines
        return "\n".join(output_lines)


    async def write_code_to_file(self, code_description: str, project_path: Path, filename) -> dict:
        """Write code to a permanent file"""
        # Ensure the project directory exists
        project_path.mkdir(parents=True, exist_ok=True)
        
        # It's better to avoid changing the current working directory
        # os.chdir(project_path)

        code_string = await self._call_llm_to_generate_code(code_description)
        file_path = project_path / filename
        with open(file_path, 'w') as file:
            file.write(code_string)
                
        # Log the file creation
        log_file_operation(file_path, "create")
                
        return {
            "command": "write_code_to_file",
            "status": "success",
            "project_path": str(project_path),
            "filename": filename
        }
        

    async def write_and_exec(self, code_description: str,  project_path: Path) -> dict:
        """Write code to a temp file and execute it"""
        os.chdir(project_path)    

        code_string = await self._call_llm_to_generate_code(code_description)
        

        
        # Create temp file with .py extension
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code_string)
            temp_path = temp_file.name
        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "command": "write_and_exec",
                "status": "success",
                "project_path": str(project_path),
                "run_output": result.stdout,
                "errors": result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "command": "run_app",
                "status": "error",
                "project_path": str(project_path),
                "errors": f"Failed to run app: {str(e)}\nOutput: {e.stdout}\nError: {e.stderr}"
            }
