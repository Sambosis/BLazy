# code_context_manager.py

import os
import json
import re
import ast
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set, Optional, List, Tuple

@dataclass
class CodeFile:
    name: str
    content: str
    version: int = 1
    last_modified: datetime = field(default_factory=datetime.now)
    dependencies: Set[str] = field(default_factory=set)
    description: Optional[str] = None

    def to_message(self) -> Dict[str, any]:
        """Convert CodeFile to a structured message for an LLM or any other consumer."""
        message_content = f"""
        FILE CONTEXT:
        **{self.name}** (v{self.version})
        *Last Modified*: {self.last_modified.strftime('%Y-%m-%d %H:%M:%S')}
        *Dependencies*: {', '.join(self.dependencies) if self.dependencies else 'None'}
        *Description*: {self.description or 'No description provided.'}

        **Content:**
        ```python
        {self.content}
        ```
        """

        return {
            "role": "user",
            "content": [{
                "type": "text",
                "text": message_content
            }]
        }

def extract_code_blocks(response_text: str) -> List[Tuple[str, str]]:
    """
    Extracts code blocks from the response text.

    Returns a list of tuples containing the language and code.
    For example: [("python", "def foo(): pass"), ...]
    """
    code_blocks = []
    # Regex to match code blocks with language specification
    pattern = re.compile(r"```(\w+)?\n([\s\S]*?)```", re.MULTILINE)
    matches = pattern.findall(response_text)
    for lang, code in matches:
        language = lang.strip() if lang else "plaintext"
        code_blocks.append((language, code.strip()))
    return code_blocks

def is_code_valid(code: str) -> bool:
    """
    Checks if the provided Python code is syntactically correct.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"SyntaxError while parsing code: {e}")
        return False

def replace_file(file_path: str, new_content: str) -> None:
    """
    Replaces the entire content of the specified file with new_content.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Replaced content of {file_path}")

def insert_code_after_function(original_content: str, function_name: str, code_to_add: str) -> str:
    """
    Inserts code after the specified function in a Python file.
    """
    pattern = re.compile(rf"(def {re.escape(function_name)}\(.*?\):\s*[\s\S]*?)(?=def |\Z)", re.MULTILINE)
    match = pattern.search(original_content)
    if match:
        insert_position = match.end()
        return original_content[:insert_position] + '\n\n' + code_to_add + original_content[insert_position:]
    else:
        # If function not found, append at the end
        return original_content + '\n\n' + code_to_add

def extract_single_code_block(code_block: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts a single code block's language and code.
    """
    match = re.match(r"```(\w+)?\n([\s\S]*?)```", code_block, re.MULTILINE)
    if match:
        lang = match.group(1).strip() if match.group(1) else "plaintext"
        code = match.group(2).strip()
        return lang, code
    return None, None

def commit_changes(message: str) -> None:
    """
    Commits changes to the git repository with the provided message.
    """
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"Changes committed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e}")

def run_tests() -> bool:
    """
    Runs the test suite and returns True if all tests pass.
    """
    try:
        subprocess.run(["pytest"], check=True)
        print("All tests passed.")
        return True
    except subprocess.CalledProcessError:
        print("Some tests failed.")
        return False

def revert_last_commit() -> None:
    """
    Reverts the last git commit.
    """
    try:
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], check=True)
        print("Reverted the last commit.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to revert commit: {e}")

class CodeContextManager:
    def __init__(self, persistence_file: Optional[str] = None):
        self.files: Dict[str, CodeFile] = {}
        self.persistence_file = persistence_file
        if self.persistence_file:
            self.load_from_disk()

    def update_file(self, 
                   name: str, 
                   content: str, 
                   dependencies: Optional[Set[str]] = None, 
                   description: Optional[str] = None) -> None:
        """Add or update a file in the context."""
        if name in self.files:
            existing_file = self.files[name]
            existing_file.version += 1
            existing_file.content = content
            existing_file.last_modified = datetime.now()
            if dependencies is not None:
                existing_file.dependencies = dependencies
            if description is not None:
                existing_file.description = description
            print(f"Updated file: {name} to version {existing_file.version}")
        else:
            self.files[name] = CodeFile(
                name=name,
                content=content,
                dependencies=dependencies or set(),
                description=description
            )
            print(f"Added new file: {name}")

        if self.persistence_file:
            self.save_to_disk()

    def get_context_messages(self) -> List[Dict[str, any]]:
        """Get all file contexts as messages."""
        return [file.to_message() for file in self.files.values()]

    def save_to_disk(self) -> None:
        """Persist the current code context to disk."""
        data = {
            name: {
                "name": file.name,
                "content": file.content,
                "version": file.version,
                "last_modified": file.last_modified.isoformat(),
                "dependencies": list(file.dependencies),
                "description": file.description
            } for name, file in self.files.items()
        }
        with open(self.persistence_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Saved code context to {self.persistence_file}")

    def load_from_disk(self) -> None:
        """Load the code context from disk."""
        if not os.path.exists(self.persistence_file):
            print(f"Persistence file {self.persistence_file} does not exist. Starting fresh.")
            return

        with open(self.persistence_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for name, file_data in data.items():
                self.files[name] = CodeFile(
                    name=file_data["name"],
                    content=file_data["content"],
                    version=file_data["version"],
                    last_modified=datetime.fromisoformat(file_data["last_modified"]),
                    dependencies=set(file_data["dependencies"]),
                    description=file_data.get("description")
                )
        print(f"Loaded code context from {self.persistence_file}")

    def remove_file(self, name: str) -> None:
        """Remove a file from the context."""
        if name in self.files:
            del self.files[name]
            print(f"Removed file: {name}")
            if self.persistence_file:
                self.save_to_disk()
        else:
            print(f"Tried to remove non-existent file: {name}")

    def apply_llm_response(self, response_text: str) -> None:
        """
        Parses the LLM response, extracts code blocks, and updates the relevant files.
        Assumes the LLM follows a specific format to indicate target files and update types.

        Example LLM response format:

        ### Update file1.py
        ```python
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        ```

        ### Add to file2.py
        ```python
        def new_function():
            pass
        ```
        """
        # Split the response into sections based on filenames
        sections = re.split(r'###\s+(?:Update|Add)\s+(\S+)', response_text)
        
        # The split will result in a list where filenames are captured in group 1
        # Process in pairs: [text, filename, action, text, filename, action, ...]
        it = iter(sections)
        for section in it:
            if not section.strip():
                continue
            # Get filename
            filename = section.strip()
            # Get action (assume that 'Update' or 'Add' was matched before the filename)
            # Since regex does not capture action, infer it
            action_match = re.search(r'###\s+(Update|Add)\s+', section)
            action = "full_replace" if "Update" in section else "add_code"
            
            # Get the next item which should be the code block
            try:
                code_block = next(it).strip()
                lang, code = extract_single_code_block(code_block)
                if not code:
                    print(f"No code found in section for {filename}. Skipping.")
                    continue
                if not is_code_valid(code):
                    print(f"Invalid code for {filename}. Skipping.")
                    continue

                if action == "full_replace":
                    self.replace_file_content(filename, code)
                    commit_changes(f"Replaced content of {filename}")
                elif action == "add_code":
                    # Optionally, specify function or location
                    # For simplicity, appending to the end
                    self.add_code_to_file(filename, code)
                    commit_changes(f"Added code to {filename}")
                
                # Run tests after each change
                if run_tests():
                    print(f"Changes to {filename} passed tests.")
                else:
                    print(f"Tests failed after changes to {filename}. Reverting.")
                    revert_last_commit()
            except StopIteration:
                break

    def replace_file_content(self, filename: str, new_content: str) -> None:
        """
        Replaces the entire content of the specified file.
        """
        file_path = os.path.join('code_files', filename)
        if os.path.exists(file_path):
            replace_file(file_path, new_content)
            self.update_file(
                name=filename,
                content=new_content,
                dependencies=self.extract_dependencies(new_content),
                description=self.files[filename].description  # Keep existing description
            )
        else:
            print(f"File {filename} does not exist. Creating a new one.")
            replace_file(file_path, new_content)
            self.update_file(
                name=filename,
                content=new_content,
                dependencies=self.extract_dependencies(new_content),
                description="Automatically created file."
            )

    def add_code_to_file(self, filename: str, code_to_add: str, function_name: Optional[str] = None) -> None:
        """
        Adds new code to an existing file. Optionally, specify the function name for better placement.
        """
        file_path = os.path.join('code_files', filename)
        if not os.path.exists(file_path):
            print(f"File {filename} does not exist. Creating a new one.")
            replace_file(file_path, code_to_add)
            self.update_file(
                name=filename,
                content=code_to_add,
                dependencies=self.extract_dependencies(code_to_add),
                description="Automatically created file."
            )
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        if function_name:
            # Insert code after the specified function
            updated_content = insert_code_after_function(original_content, function_name, code_to_add)
        else:
            # Append code at the end
            updated_content = original_content + '\n\n' + code_to_add

        replace_file(file_path, updated_content)

        self.update_file(
            name=filename,
            content=updated_content,
            dependencies=self.extract_dependencies(updated_content),
            description=self.files[filename].description
        )
        print(f"Added code to {filename}")

    def extract_dependencies(self, content: str) -> Set[str]:
        """
        Extracts dependencies from the given Python file content.
        """
        dependencies = set()
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name.split('.')[0] + '.py')
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module.split('.')[0] + '.py')
        except SyntaxError:
            pass
        # Filter dependencies to include only local files
        return {dep for dep in dependencies if dep in self.files}
