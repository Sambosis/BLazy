## edit.py
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Literal, get_args, Dict
from anthropic.types.beta import BetaToolTextEditor20241022Param
from flask import g
from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import maybe_truncate
from typing import List, Optional
from icecream import ic
import sys

from rich import print as rr
import datetime
import json
from load_constants import  write_to_file, ICECREAM_OUTPUT_FILE
from config import get_constant, set_constant, REPO_DIR, PROJECT_DIR, LOGS_DIR  # Updated import

# Reconfigure stdout to use UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
# include the context for the icecream debugger
# ic.configureOutput(includeContext=True)
ic.configureOutput(includeContext=True, outputFunction=write_to_file)

# Reconfigure stdout to use UTF-8 encoding
Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]
SNIPPET_LINES: int = 4
logs_dir = Path(get_constant('LOGS_DIR'))
logs_dir = Path.cwd() / logs_dir
LOG_FILE = logs_dir / "file_creation_log.json"
PROJECT_DIR = Path(get_constant('PROJECT_DIR'))
PROJECT_DIR = Path.cwd() / PROJECT_DIR


# set_constant('LOG_FILE', str(LOG_FILE))  # Ensure LOG_FILE is a string path
class EditTool(BaseAnthropicTool):
    description="""
    A cross-platform filesystem editor tool that allows the agent to view, create, and edit files.
    The tool parameters are defined by Anthropic and are not editable.
    """

    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    _file_history: dict[Path, list[str]]

    def __init__(self):
        self._file_history = defaultdict(list)
        if not LOG_FILE.exists():
            LOG_FILE.write_text('[]', encoding='utf-8')
        super().__init__()

    def to_params(self) -> BetaToolTextEditor20241022Param:
        return {
            "name": self.name,
            "type": self.api_type,
        }

    def format_output(self, data: Dict) -> str:
        """Format the output data similar to ProjectSetupTool style"""
        output_lines = []
        
        # Add command type
        output_lines.append(f"Command: {data['command']}")
        
        # Add status
        output_lines.append(f"Status: {data['status']}")
        
        # Add file path if present
        if 'file_path' in data:
            output_lines.append(f"File Path: {data['file_path']}")
            
        # Add operation details if present
        if 'operation_details' in data:
            output_lines.append(f"Operation: {data['operation_details']}")
            
        # Join all lines with newlines
        return "\n".join(output_lines)

    async def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ) -> ToolResult:
        try:
            # Normalize the path first
            _path = self.normalize_path(path)
            
            if command == "create":
                if not file_text:
                    raise ToolError("Parameter `file_text` is required for command: create")
                self.write_file(_path, file_text)
                self._file_history[_path].append(file_text)
                self.log_file_operation(_path, "create")
                
                output_data = {
                    "command": "create",
                    "status": "success",
                    "file_path": str(_path),
                    "operation_details": "File created successfully"
                }
                return ToolResult(output=self.format_output(output_data))
                
            # Handle other commands similarly...
            # ...existing code...

        except Exception as e:
            return ToolResult(output=None, error=str(e), base64_image=None)

    def normalize_path(self, path: Optional[str]) -> Path:
        """Normalize file paths to be within the project directory"""
        if not path:
            raise ValueError("Path cannot be None or empty")
            
        project_dir = Path(get_constant("PROJECT_DIR"))
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            
        try:
            # Convert to Path object
            p = Path(path)
            
            # If it's an absolute path
            if p.is_absolute():
                # Ensure it's within project directory
                try:
                    p = p.relative_to(p.anchor)
                except ValueError:
                    p = Path(os.path.basename(str(p)))
                    
            # Resolve the path relative to project directory
            resolved_path = (project_dir / p).resolve()
            
            # Ensure the path is within project directory
            if not str(resolved_path).startswith(str(project_dir)):
                resolved_path = project_dir / p.name
                
            return resolved_path
            
        except Exception as e:
            raise ValueError(f"Invalid path: {e}")

    async def view(self, path: Path, view_range: Optional[List[int]] = None) -> ToolResult:
        """Implement the view command using cross-platform methods."""
        ic(path)
        if path.is_dir():
            if view_range:
                raise ToolError(
                    "The `view_range` parameter is not allowed when `path` points to a directory."
                )

            try:
                # Cross-platform directory listing using pathlib
                files = []
                for level in range(3):  # 0-2 levels deep
                    if level == 0:
                        pattern = "*"
                    else:
                        pattern = os.path.join(*["*"] * (level + 1))

                    for item in path.glob(pattern):
                        # Skip hidden files and directories
                        if not any(part.startswith('.') for part in item.parts):
                            files.append(str(item.resolve()))  # Ensure absolute paths

                stdout = "\n".join(sorted(files))
                stdout = f"Here's the files and directories up to 2 levels deep in {path}, excluding hidden items:\n{stdout}\n"
                return ToolResult(output=stdout, error=None, base64_image=None)
            except Exception as e:
                return ToolResult(output="", error=str(e), base64_image=None)

        # If it's a file, read its content
        file_content = self.read_file(path)
        init_line = 1
        if view_range:
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                raise ToolError("Invalid `view_range`. It should be a list of two integers.")
            file_lines = file_content.split("\n")
            n_lines_file = len(file_lines)
            init_line, final_line = view_range
            if init_line < 1 or init_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                )
            if final_line > n_lines_file:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                )
            if final_line != -1 and final_line < init_line:
                raise ToolError(
                    f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"
                )

            if final_line == -1:
                file_content = "\n".join(file_lines[init_line - 1:])
            else:
                file_content = "\n".join(file_lines[init_line - 1 : final_line])
        return ToolResult(output=self._make_output(file_content, str(path), init_line=init_line), error=None, base64_image=None)
    def str_replace(self, path: Path, old_str: str, new_str: Optional[str]) -> ToolResult:
        """Implement the str_replace command, which replaces old_str with new_str in the file content."""
        try:
            # Read the file content
            ic(path)
            path = self.normalize_path(path)
            file_content = self.read_file(path).expandtabs()
            old_str = old_str.expandtabs()
            new_str = new_str.expandtabs() if new_str is not None else ""

            # Check if old_str is unique in the file
            occurrences = file_content.count(old_str)
            if occurrences == 0:
                raise ToolError(f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.")
            elif occurrences > 1:
                file_content_lines = file_content.split("\n")
                lines = [
                    idx + 1
                    for idx, line in enumerate(file_content_lines)
                    if old_str in line
                ]
                raise ToolError(
                    f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique"
                )

            # Replace old_str with new_str
            new_file_content = file_content.replace(old_str, new_str)

            # Write the new content to the file
            self.write_file(path, new_file_content)

            # Save the content to history
            self._file_history[path].append(file_content)

            # Create a snippet of the edited section
            replacement_line = file_content.split(old_str)[0].count("\n")
            start_line = max(0, replacement_line - SNIPPET_LINES)
            end_line = replacement_line + SNIPPET_LINES + new_str.count("\n")
            snippet = "\n".join(new_file_content.split("\n")[start_line : end_line + 1])

            # Prepare the success message
            success_msg = f"The file {path} has been edited. "
            success_msg += self._make_output(snippet, f"a snippet of {path}", start_line + 1)
            success_msg += "Review the changes and make sure they are as expected. Edit the file again if necessary."

            return ToolResult(output=success_msg, error=None, base64_image=None)

        except Exception as e:
            return ToolResult(output=None, error=str(e), base64_image=None)
    def insert(self, path: Path, insert_line: int, new_str: str) -> ToolResult:
        """Implement the insert command, which inserts new_str at the specified line in the file content."""
        path = self.normalize_path(path)
        file_text = self.read_file(path).expandtabs()
        new_str = new_str.expandtabs()
        file_text_lines = file_text.split("\n")
        n_lines_file = len(file_text_lines)

        if insert_line < 0 or insert_line > n_lines_file:
            raise ToolError(
                f"Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, n_lines_file]}"
            )

        new_str_lines = new_str.split("\n")
        new_file_text_lines = (
            file_text_lines[:insert_line]
            + new_str_lines
            + file_text_lines[insert_line:]
        )
        snippet_lines = (
            file_text_lines[max(0, insert_line - SNIPPET_LINES) : insert_line]
            + new_str_lines
            + file_text_lines[insert_line : insert_line + SNIPPET_LINES]
        )

        new_file_text = "\n".join(new_file_text_lines)
        snippet = "\n".join(snippet_lines)

        self.write_file(path, new_file_text)
        self._file_history[path].append(file_text)

        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(
            snippet,
            "a snippet of the edited file",
            max(1, insert_line - SNIPPET_LINES + 1),
        )
        success_msg += "Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
        return ToolResult(output=success_msg)
    # def ensure_valid_repo_path(filename: str) -> str:
    #     ### Need to Try this out ###
    #     base_path = PROJECT_DIR
        
    #     # Normalize path separators for cross-platform compatibility
    #     filename = filename.replace("\\", "/")
        
    #     # Check if the filename already starts with the base path
    #     if not filename.startswith(base_path):
    #         # Prepend the base path if it's not present
    #         filename = os.path.join(base_path, filename.lstrip("/"))

        return os.path.normpath(filename)
    def undo_edit(self, path: Path) -> ToolResult:
        """Implement the undo_edit command."""
        path = self.normalize_path(path)
        if not self._file_history[path]:
            raise ToolError(f"No edit history found for {path}.")

        old_text = self._file_history[path].pop()
        self.write_file(path, old_text)

        return ToolResult(
            output=f"Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}"
        )

    def read_file(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").encode('ascii', errors='replace').decode('ascii')
        except Exception as e:
            ic(f"Error reading file {path}: {e}")
            raise ToolError(f"Ran into {e} while trying to read {path}") from None
    def write_file(self, path: Path, file: str):
        """Write file content ensuring correct project directory"""
        try:
            # Normalize path to be within project directory
            full_path = self.normalize_path(str(path))
            
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            full_path.write_text(file, encoding="utf-8")
        except Exception as e:
            raise ToolError(f"Error writing to {path}: {str(e)}")

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ) -> str:
        """Generate output for the CLI based on the content of a file."""
        file_content = maybe_truncate(file_content)
        if expand_tabs:
            file_content = file_content.expandtabs()
        file_content = "\n".join(
            [
                f"{i + init_line:6}\t{line}"
                for i, line in enumerate(file_content.split("\n"))
            ]
        )
        return (
            f"Here's the result of running ` -n` on {file_descriptor}:\n"
            + file_content
            + "\n"
        )

    def log_file_operation(self, path: Path, operation: str) -> None:
        """Log operations on a file with timestamp."""
        try:
            # Read existing logs
            if LOG_FILE.exists():
                logs = json.loads(LOG_FILE.read_text(encoding='utf-8'))
            else:
                logs = {}
            
            path_str = str(path)
            # Convert to dict if it's still a list (for backward compatibility)
            if isinstance(logs, list):
                logs = {}

            # Create new entry if file not logged before
            if path_str not in logs:
                logs[path_str] = {
                    "created_at": datetime.datetime.now().isoformat(),
                    "operations": []
                }
            
            # Add new operation
            logs[path_str]["operations"].append({
                "timestamp": datetime.datetime.now().isoformat(),
                "operation": operation
            })
            
            # Write updated logs
            LOG_FILE.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"Warning: Failed to log file operation: {e}")
