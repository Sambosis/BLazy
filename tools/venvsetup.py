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
from config import get_constant, set_constant
class ProjectCommand(str, Enum):
    SETUP_PROJECT = "setup_project"
    ADD_DEPENDENCIES = "add_additional_depends"
    RUN_APP = "run_app"

class ProjectSetupTool(BaseAnthropicTool):
    """
    A tool that sets up Python projects with virtual environments and manages script execution.
    """

    name: Literal["project_setup"] = "project_setup"
    api_type: Literal["custom"] = "custom"
    description: str = "A tool for Python project management: setup projects, add dependencies, and run applications."

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
                        "enum": [cmd.value for cmd in ProjectCommand],
                        "description": "Command to execute: setup_project, add_additional_depends, or run_app"
                    },
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Python packages to install"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    },
                    "python_filename": {
                        "type": "string",
                        "description": "the name of the python file to run"
                    }
                },
                "required": ["command", "project_path"]
            }
        }

    def run_command(self, cmd: str, cwd=None, capture_output=False) -> subprocess.CompletedProcess:
        """Helper method to run shell commands safely"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                cwd=cwd,
                capture_output=capture_output,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            ic(f"Error executing command: {cmd}")
            ic(f"Error details: {e}")
            raise

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

    async def setup_project(self, project_path: Path, packages: List[str]) -> dict:
        """Sets up a new Python project"""
        project_path.mkdir(parents=True, exist_ok=True)
        os.chdir(project_path)

        # Setup virtual environment
        ic("Creating virtual environment...")
        self.run_command("uv venv")
        try:
            self.run_command("uv init")
        except:
            pass

        # Install initial packages
        ic("Installing packages...")
        for package in packages:
            self.run_command(f"uv add {package}")

        return {
            "command": "setup_project",
            "status": "success",
            "project_path": str(project_path),
            "packages_installed": packages
        }

    async def add_dependencies(self, project_path: Path, packages: List[str]) -> dict:
        """Adds additional dependencies to an existing project"""
        os.chdir(project_path)
        
        ic("Installing additional packages...")
        for package in packages:
            self.run_command(f"uv add {package}")

        return {
            "command": "add_additional_depends",
            "status": "success",
            "project_path": str(project_path),
            "packages_installed": packages
        }

    async def run_app(self, project_path: Path, filename: str) -> dict:
        """Runs the application using uv run"""
        os.chdir(project_path)
        
        try:
            result = subprocess.run(
                ["uv", "run", filename],
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "command": "run_app",
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

    async def __call__(
        self,
        *,
        command: ProjectCommand,
        project_path: str,
        packages: List[str] = ["flask", "pandas", "flask-wtf", "python-dotenv"],
        python_filename: str = "app.py",
        **kwargs,
    ) -> ToolResult:
        """
        Executes the specified command for project management.
        """
        try:
            # Convert path string to Path object
            # project_path = Path(project_path)
            project_path = Path(get_constant("PROJECT_DIR"))
            # Execute the appropriate command
            if command == ProjectCommand.SETUP_PROJECT:
                result_data = await self.setup_project(project_path, packages)
            elif command == ProjectCommand.ADD_DEPENDENCIES:
                result_data = await self.add_dependencies(project_path, packages)
            elif command == ProjectCommand.RUN_APP:
                result_data = await self.run_app(project_path, python_filename)
            else:
                return ToolResult(error=f"Unknown command: {command}")

            # Convert result_data to formatted string
            formatted_output = self.format_output(result_data)
            return ToolResult(output=formatted_output)

        except Exception as e:
            ic(e)
            error_msg = f"Failed to execute {command}: {str(e)}"
            rr(f"Error: {error_msg}")
            return ToolResult(error=error_msg)