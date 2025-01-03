from .base import BaseAnthropicTool

class ExampleTool(BaseAnthropicTool):
    @property
    def name(self) -> str:
        return "example_tool"

    @property
    def description(self) -> str:
        return "An example tool that does something."

    def __init__(self):
        super().__init__(input_schema={
            "type": "object",
            "properties": {
                "example_param": {
                    "type": "string",
                    "description": "An example parameter for the tool."
                }
            },
            "required": ["example_param"]
        })

    def __call__(self, **kwargs) -> str:
        # Implement the tool's functionality here
        return f"Example tool executed with {kwargs.get('example_param')}" 