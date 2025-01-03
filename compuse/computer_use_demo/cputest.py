"""
Cross-platform agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""

import asyncio
import os
import platform
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, List, Optional, TypedDict, cast

from anthropic import Anthropic, AnthropicBedrock, AnthropicVertex, APIResponse
from anthropic.types import ToolResultBlockParam
from anthropic.types.beta import (
    BetaContentBlock,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)

from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult

# Constants
BETA_FLAG = "computer-use-2024-10-22"

# Set up platform-specific paths and directories
if platform.system() == 'Windows':
    OUTPUT_DIR = Path(os.getenv('APPDATA', '.')) / 'computer_tool' / 'outputs'
    DOWNLOAD_CMD = "Invoke-WebRequest -Uri {url} -OutFile {output}"
    APP_LAUNCH_CMD = "Start-Process"
else:
    OUTPUT_DIR = Path.home() / '.computer_tool' / 'outputs'
    DOWNLOAD_CMD = "curl -L {url} -o {output}"
    APP_LAUNCH_CMD = "xdg-open"  # Linux
    if platform.system() == 'Darwin':  # macOS
        APP_LAUNCH_CMD = "open"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TYPING_DELAY_MS = 8
TYPING_GROUP_SIZE = 50

# Scaling Targets
class Resolution(TypedDict):
    width: int
    height: int

MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),       # 4:3
    "WXGA": Resolution(width=1280, height=800),      # 16:10
    "FWXGA": Resolution(width=1366, height=768),     # ~16:9
}

# API Providers
class APIProvider(StrEnum):
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"

PROVIDER_TO_DEFAULT_MODEL_NAME: dict[APIProvider, str] = {
    APIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    APIProvider.BEDROCK: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    APIProvider.VERTEX: "claude-3-5-sonnet-v2@20241022",
}

def get_platform_specific_system_prompt() -> str:
    """Generate a platform-specific system prompt."""
    system = platform.system()
    arch = platform.machine()
    
    if system == "Windows":
        return f"""<SYSTEM_CAPABILITY>
* You are utilizing a Windows machine using {arch} architecture with internet access.
* You can install Windows applications using PowerShell. Use Invoke-WebRequest for downloading files.
* To open applications, use pyautogui to press the Windows key and type the application name followed by enter.
* If GUI app launching fails, you can use PowerShell's Start-Process command as a fallback.
* When using PowerShell with commands that may produce large output, redirect to a temporary file and use Select-String for filtering.
* The current date is {datetime.today()}.
</SYSTEM_CAPABILITY>"""
    elif system == "Darwin":
        return f"""<SYSTEM_CAPABILITY>
* You are utilizing a macOS machine using {arch} architecture with internet access.
* You can install applications using brew or curl for downloading files.
* To open applications, use pyautogui to press command+space and type the application name.
* The terminal can launch GUI apps using the 'open' command.
* When dealing with large command output, use grep or redirect to temporary files.
* The current date is {datetime.today()}.
</SYSTEM_CAPABILITY>"""
    else:  # Linux
        return f"""<SYSTEM_CAPABILITY>
* You are utilizing a Linux machine using {arch} architecture with internet access.
* You can install applications using the system package manager or curl for downloading files.
* To open applications, use pyautogui to press the appropriate shortcut for your desktop environment.
* GUI applications can be launched using xdg-open.
* When dealing with large command output, use grep or redirect to temporary files.
* The current date is {datetime.today()}.
</SYSTEM_CAPABILITY>"""

# Common instructions for all platforms
COMMON_INSTRUCTIONS = """
<IMPORTANT>
* When using a web browser, if a startup wizard appears, IGNORE IT. Click directly on the address bar and enter the URL.
* For PDF documents, rather than navigating through screenshots, download the PDF and convert it to text for direct reading.
* When viewing pages, consider zooming out for better visibility or ensure you scroll to see all content.
* Computer function calls take time to execute and return. Where possible, chain multiple calls together.
</IMPORTANT>"""

# System Prompt combining platform-specific and common instructions
SYSTEM_PROMPT = get_platform_specific_system_prompt() + COMMON_INSTRUCTIONS

# Helper Functions
def chunks(s: str, chunk_size: int) -> List[str]:
    """Split a string into chunks of specified size."""
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]

def _maybe_filter_to_n_most_recent_images(
    messages: List[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int = 10,
):
    """Filters out older images from the messages to keep memory usage in check."""
    if images_to_keep is None:
        return

    tool_result_blocks = cast(
        List[ToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    if images_to_remove <= 0:
        return

    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content
            if images_to_remove <= 0:
                break

def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: List[
        BetaTextBlockParam | BetaImageBlockParam
    ] = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }

def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str) -> str:
    """Prepend system information to tool result if available."""
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text

# Sampling Loop
async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: List[BetaMessageParam],
    output_callback: Callable[[BetaContentBlock], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_response_callback: Callable[[APIResponse[BetaMessage]], None],
    api_key: str,
    only_n_most_recent_images: Optional[int] = None,
    max_tokens: int = 4096,
) -> List[BetaMessageParam]:
    """Sampling loop for the assistant/tool interaction of computer use."""
    tool_collection = ToolCollection(
        ComputerTool(),
        BashTool(),
        EditTool(),
    )
    system = (
        f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    )

    while True:
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(messages, only_n_most_recent_images)

        # Initialize appropriate client based on provider
        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()
        else:
            raise ValueError(f"Unsupported API provider: {provider}")

        # Call the API
        response = client.beta.messages.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            system=system,
            tools=tool_collection.to_params(),
            betas=[BETA_FLAG],
        )

        api_response_callback(cast(APIResponse[BetaMessage], response))

        messages.append(
            {
                "role": "assistant",
                "content": cast(List[BetaContentBlockParam], response.content),
            }
        )

        tool_result_content: List[BetaToolResultBlockParam] = []
        for content_block in cast(List[BetaContentBlock], response.content):
            output_callback(content_block)
            if content_block.type == "tool_use":
                result = await tool_collection.run(
                    name=content_block.name,
                    tool_input=cast(dict[str, Any], content_block.input),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block.id)
                )
                tool_output_callback(result, content_block.id)

        if tool_result_content:
            messages.append({"content": tool_result_content, "role": "user"})
        else:
            return messages

# Main Function
async def run_sampling_loop() -> List[BetaMessageParam]:
    """Main function to run the sampling loop."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")

    messages = await sampling_loop(
        model=PROVIDER_TO_DEFAULT_MODEL_NAME[APIProvider.ANTHROPIC],
        provider=APIProvider.ANTHROPIC,
        system_prompt_suffix="",
        messages=[{
            "role": "user",
            "content": "Save a documentation of Anthropic's cpu_use_tool to my desktop in markdown format."
        }],
        output_callback=lambda x: print(x),
        tool_output_callback=lambda x, y: print(f"Tool Output: {x}, ID: {y}"),
        api_response_callback=lambda x: print(f"API Response: {x}"),
        api_key=api_key,
    )
    return messages

def main():
    """Entry point for the application."""
    async def main_async():
        messages = await run_sampling_loop()
        print("Final Messages:")
        for msg in messages:
            print(msg)

    if asyncio.get_event_loop().is_running():
        asyncio.create_task(main_async())
    else:
        asyncio.run(main_async())

if __name__ == "__main__":
    main()

