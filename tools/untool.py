import json
import os
from typing import List, Dict, Callable, Any

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from dotenv import load_dotenv
load_dotenv()

class ChatManager:
    def __init__(self, model: str, system_prompt: str = "You are a helpful assistant."):
        self.client = OpenAI()
        self.model = model
        self.messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        self.functions: List[Dict[str, Any]] = []
        self.console = Console()

    def add_function(self, name: str, description: str, parameters: Dict[str, Any], func: Callable) -> None:
        self.functions.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })
        self.__dict__[name] = func  # Add the function to the class instance

    def add_message(self, role: str, content: str, tool_call_id:str = None) -> None:
        message = {"role": role, "content": content}

        if tool_call_id:
            message['tool_call_id'] = tool_call_id
        self.messages.append(message)
    def display_conversation(self) -> None:
        table = Table("Role", "Content")
        for message in self.messages:
            role = message["role"]
            content = message.get("content", "")
            
            if "tool_calls" in message:  # Handle tool calls display
                for tool_call in message["tool_calls"]:
                    table.add_row(f"[italic]{role} Tool Call[/]", f"{tool_call['function']['name']}({tool_call['function']['arguments']})")

            elif "tool_call_id" in message: # Handle tool return display
                table.add_row(f"[italic]{role} Tool Return[/]", f"{message.get('content')}")


            elif content.startswith("```") and content.endswith("```"):  # Code block
                lang = content.split("```")[1].strip() or "python"  # defaults to python if no language specified
                code = content.split("```")[2].strip()
                table.add_row(role, Panel(Syntax(code, lang), title=f"{lang} code"))
            elif content.startswith("$$") and content.endswith("$$"): # Math Block

                latex_block = content.strip("$$").strip()
                table.add_row(role, Panel(Markdown(f"```latex\n{latex_block}\n```"), title="LaTeX Block"))
            else:  # Normal Content
                table.add_row(role, Markdown(content))

        self.console.print(table)

    def call_llm(self, tool_choice: str = "auto") -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": self.messages
        }

        if self.functions:
            kwargs["tools"] = self.functions
            kwargs["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**kwargs)
        self.messages.append(response.choices[0].message.to_dict()) # Store the response
        return response.choices[0].message.to_dict()


    def execute_tool_calls(self, message: Dict[str, Any]) -> None:
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                try:
                    function = self.__dict__[function_name]
                    result = function(**arguments)
                    self.add_message(
                        "tool", json.dumps(result), tool_call_id=tool_call['id']
                    )

                except Exception as e:
                    print(f"Error executing function {function_name}: {e}")
                    self.add_message(
                        "tool", f"Error: {e}", tool_call_id=tool_call['id']
                    )


# from chat_manager import ChatManager  # Assuming the class is in chat_manager.py

# Initialize the ChatManager
manager = ChatManager(model="gpt-4o", system_prompt="You are a helpful coding assistant.")

# Define and add a function
def get_code_length(code: str) -> Dict[str, int]:
    """Calculates the length of a code string."""
    return {"length": len(code)}


manager.add_function(
    name="get_code_length",
    description="Calculates the length of a provided code string.",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "The code to calculate the length of."}
        },
        "required": ["code"],
    },
    func=get_code_length,
)

# Example interaction
manager.add_message("user", content="Calculate the length of this code: ```python\nprint('Hello')\n```")

response_message = manager.call_llm()
manager.execute_tool_calls(response_message)

manager.add_message("user", "And what about this one: ```javascript\nconsole.log('World');\n```")
response_message = manager.call_llm()
manager.execute_tool_calls(response_message)

manager.display_conversation()