import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Literal, List, Optional, Dict, Any
from icecream import ic
import sys
from rich import print as rr
edit_file_function =  {
        "name": "edit_file",
        "description": "Custom editing tool for viewing, creating and editing files. State is persistent across command calls and discussions with the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                    "description": "The command to run."
                },
                "path": {
                    "type": "string",
                    "description": "Absolute path to file or directory, e.g. '/repo/file.py' or '/repo'."
                },
                "file_text": {
                    "type": "string",
                    "description": "Required parameter of 'create' command, with the content of the file to be created."
                },
                "view_range": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    },
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Optional parameter of 'view' command when 'path' points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting [start_line, -1] shows all lines from start_line to the end of the file."
                },
                "old_str": {
                    "type": "string",
                    "description": "Required parameter of 'str_replace' command containing the string in 'path' to replace."
                },
                "new_str": {
                    "type": "string",
                    "description": "Optional parameter of 'str_replace' command containing the new string (if not given, no string will be added). Required parameter of 'insert' command containing the string to insert."
                },
                "insert_line": {
                    "type": "integer",
                    "description": "Required parameter of 'insert' command. The 'new_str' will be inserted AFTER the line 'insert_line' of 'path'."
                }
            },
            "required": ["command", "path"]
        }
}
# Reconfigure stdout to use UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
# Reconfigure stdout to use UTF-8 encoding
Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]
SNIPPET_LINES: int = 4

class EditTool:
    description = """
    A cross-platform filesystem editor tool that allows the agent to view, create, and edit files.
    The tool parameters are defined by Anthropic and are not editable.
    """
    _file_history: dict[Path, list[str]]

    def __init__(self):
        self._file_history = defaultdict(list)
        rr(self._file_history)
    def normalize_path(self, path: Optional[str]) -> Path:
        """
        Normalize a file path to ensure it starts with 'C:/repo/'.
        
        Args:
            path: Input path string that needs to be normalized
            Note:
            This method is used to normalize the path provided by the user.
            The normalized path is used to ensure that the path starts with 'C:/repo/'
            and is a valid path.
        Returns:
            Normalized path string starting with 'C:/repo/'
            
        Raises:
            ValueError: If the path is None or empty
        """
        if not path:
            raise ValueError('Path cannot be empty')
        
        # Convert to string in case we receive a Path object
        normalized_path = str(path)
        
        # Convert all backslashes to forward slashes
        normalized_path = normalized_path.replace('\\', '/')
        
        # Remove any leading/trailing whitespace
        normalized_path = normalized_path.strip()
        
        # Remove multiple consecutive forward slashes
        normalized_path = re.sub(r'/+', '/', normalized_path)
        
        # Remove 'C:' or 'c:' if it exists at the start
        normalized_path = re.sub(r'^[cC]:', '', normalized_path)
        
        # Remove '/repo/' if it exists at the start
        normalized_path = re.sub(r'^/repo/', '', normalized_path)
        
        # Remove leading slash if it exists
        normalized_path = re.sub(r'^/', '', normalized_path)
        
        # Combine with base path
        return Path(f'C:/repo/{normalized_path}')

    def validate_path(self, command: str, path: Path):
        """
        Check that the path/command combination is valid in a cross-platform manner.
        param command: The command that the user is trying to run.
        """
        path = self.normalize_path(path)
        try:
            # This handles both Windows and Unix paths correctly
            path = path.resolve()
        except Exception as e:
            raise ValueError(f"Invalid path format: {path}. Error: {str(e)}")

        # Check if it's an absolute path
        if not path.is_absolute():
            suggested_path = Path.cwd() / path
            raise ValueError(
                f"The path {path} is not an absolute path. Maybe you meant {suggested_path}?"
            )

        # Check if path exists
        if not path.exists() and command != "create":
            raise ValueError(
                f"The path {path} does not exist. Please provide a valid path."
            )
        if path.exists() and command == "create":
            raise ValueError(
                f"File already exists at: {path}. Cannot overwrite files using command `create`."
            )

        # Check if the path points to a directory
        if path.is_dir():
            if command != "view":
                raise ValueError(f"The path {path} is a directory and only the `view` command can be used on directories")
    def view(self, path: Path, view_range: Optional[List[int]] = None) -> Dict[str, Any]:
        """Implement the view command using cross-platform methods."""
        path = self.normalize_path(path)
        if path.is_dir():
            if view_range:
                raise ValueError("The `view_range` parameter is not allowed when `path` points to a directory.")

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
                return {"output": stdout}
            except Exception as e:
                return {"error": str(e)}

        # If it's a file, read its content
        try:
            file_content = self.read_file(path)
            init_line = 1
            if view_range:
                if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                    raise ValueError("Invalid `view_range`. It should be a list of two integers.")
                file_lines = file_content.split("\n")
                n_lines_file = len(file_lines)
                init_line, final_line = view_range
                if init_line < 1 or init_line > n_lines_file:
                    raise ValueError(
                        f"Invalid `view_range`: {view_range}. Its first element `{init_line}` should be within the range of lines of the file: {[1, n_lines_file]}"
                    )
                if final_line > n_lines_file:
                    raise ValueError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be smaller than the number of lines in the file: `{n_lines_file}`"
                    )
                if final_line != -1 and final_line < init_line:
                    raise ValueError(
                        f"Invalid `view_range`: {view_range}. Its second element `{final_line}` should be larger or equal than its first `{init_line}`"
                    )

                if final_line == -1:
                    file_content = "\n".join(file_lines[init_line - 1:])
                else:
                    file_content = "\n".join(file_lines[init_line - 1 : final_line])
            
            ic(file_content)
            output = self._make_output(file_content, str(path), init_line=init_line)
            return {"output": output}
        except Exception as e:
            return {"error": str(e)}
    def str_replace(self, path: Path, old_str: str, new_str: Optional[str]) -> Dict[str, Any]:
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
                raise ValueError(f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.")
            elif occurrences > 1:
                file_content_lines = file_content.split("\n")
                lines = [
                    idx + 1
                    for idx, line in enumerate(file_content_lines)
                    if old_str in line
                ]
                raise ValueError(
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

            return {"output": success_msg}

        except Exception as e:
            return {"error": str(e)}
    def create(self, path: Path, file_text: str) -> Dict[str, Any]:
        path = self.normalize_path(path)
        self.write_file(path, file_text)
        self._file_history[path].append(file_text)
        return {"output": f"File created successfully at: {path}"}

    def insert(self, path: Path, insert_line: int, new_str: str) -> Dict[str, Any]:
        """Implement the insert command, which inserts new_str at the specified line in the file content."""
        try:
            path = self.normalize_path(path)
            file_text = self.read_file(path).expandtabs()
            new_str = new_str.expandtabs()
            file_text_lines = file_text.split("\n")
            n_lines_file = len(file_text_lines)

            if insert_line < 0 or insert_line > n_lines_file:
                raise ValueError(
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
            return {"output": success_msg}

        except Exception as e:
            return {"error": str(e)}
    def undo_edit(self, path: Path) -> Dict[str, Any]:
        """Implement the undo_edit command."""
        path = self.normalize_path(path)
        if not self._file_history[path]:
            return {"error": f"No edit history found for {path}."}

        old_text = self._file_history[path].pop()
        self.write_file(path, old_text)

        output = f"Last edit to {path} undone successfully. {self._make_output(old_text, str(path))}"
        return {"output": output}
    def read_file(self, path: Path) -> str:
        rr(path)

        path = self.normalize_path(path)

        try:
            return path.read_text(encoding="utf-8").encode('ascii', errors='replace').decode('ascii')
        except Exception as e:
            ic(f"Error reading file {path}: {e}")
            raise ValueError(f"Ran into {e} while trying to read {path}") 
    def write_file(self, path: Path, file: str):
        path = self.normalize_path(path)
        """Write the content of a file to a given path; raise a ToolError if an error occurs."""
        try:
            path.write_text(file, encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Ran into {e} while trying to write to {path}") 

    def _make_output(
        self,
        file_content: str,
        file_descriptor: str,
        init_line: int = 1,
        expand_tabs: bool = True,
    ) -> str:
        """Generate output for the CLI based on the content of a file."""
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
def edit_file(command: Command, path: str, file_text: Optional[str] = None, view_range: Optional[List[int]] = None, old_str: Optional[str] = None, new_str: Optional[str] = None, insert_line: Optional[int] = None) -> Dict[str, Any]:
    """
    Custom editing tool for viewing, creating and editing files.

    Args:
        command (str): The command to run. Allowed options are: 'view', 'create', 'str_replace', 'insert', 'undo_edit'.
        path (str): Absolute path to file or directory, e.g. '/repo/file.py' or '/repo'.
        file_text (Optional[str]): Required parameter of 'create' command, with the content of the file to be created.
        view_range (Optional[List[int]]): Optional parameter of 'view' command when 'path' points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting [start_line, -1] shows all lines from start_line to the end of the file.
        old_str (Optional[str]): Required parameter of 'str_replace' command containing the string in 'path' to replace.
        new_str (Optional[str]): Optional parameter of 'str_replace' command containing the new string (if not given, no string will be added). Required parameter of 'insert' command containing the string to insert.
        insert_line (Optional[int]): Required parameter of 'insert' command. The 'new_str' will be inserted AFTER the line 'insert_line' of 'path'.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the operation.
    """
    tool = EditTool()
    path_obj = tool.normalize_path(path)

    try:
        if command == "view":
            return tool.view(path_obj, view_range)
        elif command == "create":
            if not file_text:
                raise ValueError("Parameter `file_text` is required for command: create")
            return tool.create(path_obj, file_text)
        elif command == "str_replace":
            if not old_str:
                raise ValueError("Parameter `old_str` is required for command: str_replace")
            return tool.str_replace(path_obj, old_str, new_str)
        elif command == "insert":
            if insert_line is None:
                raise ValueError("Parameter `insert_line` is required for command: insert")
            if not new_str:
                raise ValueError("Parameter `new_str` is required for command: insert")
            return tool.insert(path_obj, insert_line, new_str)
        elif command == "undo_edit":
            return tool.undo_edit(path_obj)
        else:
            raise ValueError(f"Unrecognized command {command}. The allowed commands are: view, create, str_replace, insert, undo_edit")
    except Exception as e:
        return {"error": str(e)}

# OpenAI function definition
edit_file_function = {
    "name": "edit_file",
    "description": "Custom editing tool for viewing, creating and editing files. State is persistent across command calls and discussions with the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                "description": "The command to run."
            },
            "path": {
                "type": "string",
                "description": "Absolute path to file or directory, e.g. '/repo/file.py' or '/repo'."
            },
            "file_text": {
                "type": "string",
                "description": "Required parameter of 'create' command, with the content of the file to be created."
            },
            "view_range": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 2,
                "maxItems": 2,
                "description": "Optional parameter of 'view' command when 'path' points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting [start_line, -1] shows all lines from start_line to the end of the file."
            },
            "old_str": {
                "type": "string",
                "description": "Required parameter of 'str_replace' command containing the string in 'path' to replace."
            },
            "new_str": {
                "type": "string",
                "description": "Optional parameter of 'str_replace' command containing the new string (if not given, no string will be added). Required parameter of 'insert' command containing the string to insert."
            },
            "insert_line": {
                "type": "integer",
                "description": "Required parameter of 'insert' command. The 'new_str' will be inserted AFTER the line 'insert_line' of 'path'."
            }
        },
        "required": ["command", "path"]
    }
}