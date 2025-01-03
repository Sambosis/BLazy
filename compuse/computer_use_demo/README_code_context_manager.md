# Code Context Manager Documentation

## Overview
The Code Context Manager is a Python utility designed to manage and update code files within a project, leveraging Large Language Models (LLMs) to suggest and apply changes. It provides robust functionality for storing file content, versioning, dependency tracking, and persistent storage.

## Installation
```bash
pip install pytest  # Required for test functionality
```

## Basic Usage

### 1. Initialization
```python
from code_context_manager import CodeContextManager

# Initialize with persistence file
manager = CodeContextManager("code_context.json")

# Or without persistence (memory only)
manager = CodeContextManager()
```

### 2. Managing Files

#### Add or Update Files
```python
# Add a new file
manager.update_file(
    name="my_module.py",
    content="def my_function():\n    print('Hello')",
    dependencies={"utils.py"},
    description="A simple module"
)

# Update existing file
manager.update_file(
    name="my_module.py",
    content="def my_function():\n    print('Hello, World!')"
)
```

#### Remove Files
```python
manager.remove_file("my_module.py")
```

## 3. Working with LLMs

#### Get Context for LLM
```python
messages = manager.get_context_messages()
```
### Use messages in your LLM API calls

### Apply LLM Suggestions
#### Example LLM response
```python
llm_response = """
```python
def my_function(name):
    print(f'Hello, {name}!')
```
## Update my_module.py

### Add to utils.py
```python
def helper_function():
    print("This is a helper")
```

```python
manager.apply_llm_response(llm_response)
```

## Features

### 1. Automatic Versioning
- Files are automatically versioned when updated
- Version history is maintained in the persistence file

### 2. Dependency Tracking
- Automatically extracts Python import statements
- Maintains dependency relationships between files
- Supports both direct imports and from-imports

### 3. Git Integration
- Automatic commits for file changes
- Automatic rollback if tests fail
- Commit messages include file and action information

### 4. Test Integration
- Automatic test running after changes
- Rollback support if tests fail
- Uses pytest for test execution

### 5. Persistence
- JSON-based file storage
- Automatic saving on updates
- Load previous state on initialization

## File Format Specifications

### LLM Response Format
### Update filename.py
```python
# Your code here
```

### Add to filename.py
```python
# Your code here
```

### Persistence File Format
```json
{
    "filename.py": {
        "name": "filename.py",
        "content": "# file content",
        "version": 1,
        "last_modified": "2024-03-14T12:00:00",
        "dependencies": ["dependency1.py", "dependency2.py"],
        "description": "File description"
    }
}
```

## Advanced Usage

### Custom Test Integration
```python
def custom_test_runner():
    # Your custom test logic
    return True  # or False based on test results

manager = CodeContextManager("code_context.json")
manager.test_runner = custom_test_runner
```

### Working with Dependencies
```python
# Manually extract dependencies
code = """
import os
from my_module import my_function
"""
dependencies = manager.extract_dependencies(code)
print(dependencies)  # {'my_module.py'}
```

### File Operations with Function Targeting
```python
# Add code after specific function
manager.add_code_to_file(
    filename="module.py",
    code_to_add="def new_function():\n    pass",
    function_name="existing_function"
)
```

## Best Practices

### Version Control
- Always use with a Git repository
- Keep meaningful commit messages
- Regular backups of persistence file

### Code Organization
- Use descriptive file names
- Maintain clear dependencies
- Include meaningful file descriptions

### Testing
- Write comprehensive tests
- Use pytest for compatibility
- Test changes before committing

### LLM Integration
- Provide clear context to LLMs
- Validate LLM responses
- Review changes before applying

## Error Handling
The manager includes robust error handling for:
- Invalid Python syntax
- Missing files
- Git operations
- Test failures
- Persistence operations

## Example Workflow
```python
# Initialize manager
manager = CodeContextManager("code_context.json")

# Add initial files
manager.update_file(
    "main.py",
    "def main():\n    print('Hello')",
    description="Main entry point"
)

# Get context for LLM
context = manager.get_context_messages()

# Send to LLM and get response
llm_response = get_llm_suggestions(context)

# Apply changes
manager.apply_llm_response(llm_response)

# Check results
print(manager.files["main.py"].version)  # Current version
print(manager.files["main.py"].last_modified)  # Last update time
```

## Limitations
- Only supports Python files currently
- Requires Git repository for version control
- Depends on pytest for testing
- Single-threaded operations

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

For more information or support, please open an issue in the repository.