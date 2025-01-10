from typing import Literal, Optional, List
from pathlib import Path
from .base import ToolResult, BaseAnthropicTool
import os
import subprocess
from icecream import ic
from rich import print as rr
import json

class ProjectSetupTool(BaseAnthropicTool):
    """
    A tool that sets up Python projects with virtual environments and manages script execution.
    """

    name: Literal["project_setup"] = "project_setup"
    api_type: Literal["custom"] = "custom"
    description: str = "A tool that sets up Python projects with virtual environments, installs packages, and runs Python scripts."

    def to_params(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.api_type,
            "input_schema": {
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Python packages to install"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    },
                    "script_path": {
                        "type": "string",
                        "description": "Optional path to a Python script to run after setup"
                    }
                },
                "required": ["packages", "project_path"]
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
        
        # Add status
        output_lines.append(f"Status: {data['status']}")
        
        # Add project path
        output_lines.append(f"Project Path: {data['project_path']}")
        
        # Add packages
        output_lines.append("Packages Installed:")
        for package in data['packages_installed']:
            output_lines.append(f"  - {package}")
        
        # Add script output if present
        if 'script_output' in data and data['script_output']:
            output_lines.append("\nScript Output:")
            output_lines.append(data['script_output'])
        
        if 'script_errors' in data and data['script_errors']:
            output_lines.append("\nScript Errors:")
            output_lines.append(data['script_errors'])
        
        if 'script_error' in data:
            output_lines.append(f"\nScript Error: {data['script_error']}")
        
        # Join all lines with newlines
        return "\n".join(output_lines)

    async def __call__(
        self,
        *,
        packages: List[str] = ["flask", "pandas", "flask-wtf", "python-dotenv"],
        project_path: str = str(Path.cwd()),
        script_path: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Sets up a Python project and optionally runs a script.
        """
        try:
            # Convert path strings to Path objects
            project_path = Path(project_path)
            
            ic(f"Setting up project in {project_path}")
            
            # Create and setup project
            project_path.mkdir(parents=True, exist_ok=True)
            os.chdir(project_path)

            # Setup virtual environment
            ic("Creating virtual environment...")
            self.run_command("uv venv")
            try:
                self.run_command("uv init")
            except:
                pass

            # Install packages
            ic("Installing packages...")
            for package in packages:
                self.run_command(f"uv add {package}")

            result_data = {
                "status": "success",
                "project_path": str(project_path),
                "packages_installed": packages
            }

            # Run script if provided
            if script_path:
                script_path = Path(script_path)
                ic(f"Running script: {script_path}")
                try:
                    script_result = subprocess.run(
                        ["uv", "run", str(script_path)],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    result_data["script_output"] = script_result.stdout
                    result_data["script_errors"] = script_result.stderr
                except Exception as e:
                    result_data["script_error"] = str(e)

            # Convert result_data to formatted string
            formatted_output = self.format_output(result_data)
            return ToolResult(output=formatted_output)

        except Exception as e:
            ic(e)
            error_msg = f"Failed to setup project: {str(e)}"
            rr(f"Project setup error: {error_msg}")
            return ToolResult(error=error_msg)