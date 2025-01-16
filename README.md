# BLazy

BLazy is a Python-based project designed to automate various tasks and streamline workflows. It leverages several tools and libraries to provide a comprehensive solution for project management, web navigation, code analysis, and more.

## Features

- **Project Setup**: Automate the creation of project directories, virtual environments, and installation of dependencies.
- **Web Navigation**: Use Playwright to interact with web pages, including reading information, navigating websites, filling forms, extracting data, and downloading files.
- **Code Analysis**: Analyze Python code to extract information about functions, classes, dependencies, and more.
- **Tool Integration**: Integrate with various tools like Bash, Edit, and WebNavigator to perform specific tasks.
- **Session Management**: Maintain session history for contextual awareness and better user experience.
- **LLM Capability**: Utilize large language models (LLMs) to enhance the functionality of tools and automate complex tasks.

## Usage Instructions

### Setting Up a Project

To set up a new project, use the `ProjectSetupTool`:

```python
from tools.venvsetup import ProjectSetupTool

project_tool = ProjectSetupTool()
result = project_tool(
    command="setup_project",
    project_path="path/to/your/project",
    packages=["flask", "pandas", "flask-wtf", "python-dotenv"]
)
print(result.output)
```

### Web Navigation

To navigate a website and extract information, use the `WebNavigatorTool`:

```python
from tools.playwright import WebNavigatorTool

web_tool = WebNavigatorTool()
result = web_tool(
    url="https://example.com",
    action="read",
    params={"content_type": "structured"}
)
print(result.output)
```

### Code Analysis

To analyze a Python codebase, use the `CodeAnalyzer`:

```python
from tools.code_tools import CodeAnalyzer
from pathlib import Path

analyzer = CodeAnalyzer.create(code_root=Path("path/to/your/code"))
analyzer.analyze_repo()
df = analyzer.to_dataframe()
print(df['functions'])
print(df['classes'])
print(df['dependencies'])
```

### Using LLMs

BLazy leverages large language models (LLMs) to enhance the functionality of its tools. For example, you can use the `LLMTool` to generate code snippets, analyze text, or perform other complex tasks:

```python
from tools.llm_tool import LLMTool

llm_tool = LLMTool()
result = llm_tool(
    prompt="Generate a Python function to calculate the factorial of a number."
)
print(result.output)
```

## Contributing

We welcome contributions to the BLazy project! Here are some ways you can contribute:

1. **Report Bugs**: If you find a bug, please report it by opening an issue on GitHub.
2. **Submit Pull Requests**: If you have a fix or a new feature, submit a pull request. Please ensure your code follows the project's coding standards and includes tests.
3. **Improve Documentation**: Help us improve the documentation by suggesting changes or adding new sections.

### Development Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/Sambosis/BLazy.git
   cd BLazy
   ```

2. Create a virtual environment and activate it:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Run the tests to ensure everything is set up correctly:
   ```sh
   pytest
   ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or inquiries, please contact us at [email@example.com](mailto:email@example.com).
