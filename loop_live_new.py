import asyncio
import base64
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, cast

import ftfy
import pyautogui
from anthropic import Anthropic, APIResponse
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlock,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
from dotenv import load_dotenv
from icecream import ic, install
from rich import print as rr
from rich.prompt import Prompt

from tools import (
    BashTool,
    ComputerTool,
    EditTool,
    GetExpertOpinionTool,
    ToolCollection,
    ToolResult,
    ToolError,
    WebNavigatorTool,
    ProjectSetupTool
)

# Assume AgentDisplay is defined in the same file or imported
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich import box
from rich.table import Table
from queue import Queue
from utils.agent_display import AgentDisplay
from utils.output_manager import OutputManager
load_dotenv()
install()

# get the current working directory
CWD = Path.cwd()
MAX_SUMMARY_MESSAGES = 9
MAX_SUMMARY_TOKENS = 8000
ICECREAM_OUTPUT_FILE = CWD / "debug_log.json"

MESSAGES_FILE = CWD / "messages2.json"
# --- BETA FLAGS ---
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
HOME = Path.home()
PROMPT_NAME = None

def get_workspace_dir():
    return HOME / f"{PROMPT_NAME}/workspace"

def get_logs_dir():
    return HOME / f"{PROMPT_NAME}/logs"

def update_paths():
    logs_dir = get_logs_dir()
    return {
        'ICECREAM_OUTPUT_FILE': logs_dir / "debug_log.json",
        'JOURNAL_FILE': logs_dir / "journal/journal.log",
        'JOURNAL_ARCHIVE_FILE': logs_dir / "journal/journal.log.archive",
        'SUMMARY_FILE': logs_dir / "summaries/summary.md",
        'SYSTEM_PROMPT_FILE': logs_dir / "prompts/system_prompt.md",
        'JOURNAL_SYSTEM_PROMPT_FILE': logs_dir / "prompts/journal_prompt.md"
    }

# --- ARCHIVE OLD LOGS ---
"""Archives a file by appending it to an archive file and clearing the original.

This function takes a file path, an archive suffix, and an optional header text. It reads the contents of the file, appends them to an archive file with the given suffix, and then clears the original file. The header text, if provided, is written to the archive file before the file contents.

Args:
    filepath (str): The path to the file to be archived.
    archive_suffix (str): The suffix to be added to the archive file name.
    header_text (Optional[str]): The header text to be written to the archive file.
"""

def archive_file(filepath: Path, archive_suffix: str, header_text: Optional[str] = None):
    """Archives a file by appending it to an archive file and clearing the original."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f_read:
            lines = f_read.readlines()
        with open(filepath + archive_suffix, "a", encoding="utf-8") as f_archive:
            if header_text:
                f_archive.write("\n" + "=" * 50 + "\n")
                f_archive.write(
                    f"{header_text} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f_archive.write("=" * 50 + "\n")
            f_archive.writelines(lines)
        with open(filepath, "w", encoding="utf-8") as f_clear:
            f_clear.write("")
    except Exception as e:
        ic(f"Error archiving file {filepath}: {e}")

# --- CUSTOM LOGGING ---

def write_to_file(s: str, file_path: str = ICECREAM_OUTPUT_FILE):
    """Write debug output to a file, formatting JSON content in a pretty way."""
    lines = s.split("\n")
    formatted_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    for line in lines:
        if "tool_input:" in line:
            try:
                # Extract JSON part from the line
                json_part = line.split("tool_input: ")[1]
                # check if it looks like a json object
                if json_part.strip().startswith("{") and json_part.strip().endswith("}"):
                    # Parse and pretty-print the JSON
                    json_obj = json.loads(json_part)
                    pretty_json = json.dumps(json_obj, indent=4)
                    formatted_lines.append("tool_input: " + pretty_json)
                else:
                    formatted_lines.append(line)
            except (IndexError, json.JSONDecodeError):
                # If parsing fails, just append the original line
                formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write("\n".join(formatted_lines))
        f.write("\n" + "-" * 80 + "\n")

ic.configureOutput(includeContext=True, outputFunction=write_to_file)

def write_messages_to_file(messages, output_file_path):
    """
    Write a list of messages to a specified file.

    Args:
        messages (list): List of message dictionaries containing 'role' and 'content'
        output_file_path (str): Path to the output file

    Returns:
        bool: True if successful, False if an error occurred
    """
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(f"\n{msg['role'].upper()}:\n")

                # Handle content based on its type
                if isinstance(msg["content"], list):
                    for content_block in msg["content"]:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "tool_result":
                                f.write(
                                    f"Tool Result [ID: {content_block.get('name', 'unknown')}]:\n"
                                )
                                for item in content_block.get("content", []):
                                    if item.get("type") == "text":
                                        f.write(f"Text: {item.get('text')}\n")
                                    elif item.get("type") == "image":
                                        f.write("Image Source: base64 source too big\n")
                            else:
                                for key, value in content_block.items():
                                    f.write(f"{key}: {value}\n")
                        else:
                            f.write(f"{content_block}\n")
                else:
                    f.write(f"{msg['content']}\n")

                # Add a separator between messages for better readability
                f.write("-" * 80 + "\n")

        return True

    except Exception as e:
        # Write error to a separate error log file
        error_file_path = output_file_path + ".error.log"
        try:
            with open(error_file_path, "w", encoding="utf-8") as error_file:
                error_file.write(f"Error during execution: {str(e)}\n")
        except:
            # If we can't even write to the error file, return False
            pass
        return False

def format_messages_to_string(messages):
    """
    Format a list of messages into a formatted string.

    Args:
        messages (list): List of message dictionaries containing 'role' and 'content'

    Returns:
        str: Formatted string containing all messages
    """
    try:
        # Use list to build string pieces efficiently
        output_pieces = []

        for msg in messages:
            output_pieces.append(f"\n{msg['role'].upper()}:")

            # Handle content based on its type
            if isinstance(msg["content"], list):
                for content_block in msg["content"]:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "tool_result":
                            output_pieces.append(
                                f"\nTool Result [ID: {content_block.get('name', 'unknown')}]:"
                            )
                            for item in content_block.get("content", []):
                                if item.get("type") == "text":
                                    output_pieces.append(f"\nText: {item.get('text')}")
                                elif item.get("type") == "image":
                                    output_pieces.append(
                                        "\nImage Source: base64 source too big"
                                    )
                        else:
                            for key, value in content_block.items():
                                output_pieces.append(f"\n{key}: {value}")
                    else:
                        output_pieces.append(f"\n{content_block}")
            else:
                output_pieces.append(f"\n{msg['content']}")

            # Add a separator between messages for better readability
            output_pieces.append("\n" + "-" * 80)

        # Join all pieces with empty string since we've already added newlines
        return "".join(output_pieces)

    except Exception as e:
        return f"Error during formatting: {str(e)}"

def format_messages_to_html(messages):
    """
    Format a list of messages into an HTML-formatted string.

    Args:
        messages (list): List of message dictionaries containing 'role' and 'content'

    Returns:
        str: HTML-formatted string containing all messages
    """
    try:
        # List to accumulate HTML pieces
        output_pieces = []

        for msg in messages:
            role = msg["role"].lower()

            # Determine the message class based on role
            if role == "user":
                message_class = "user-message"
                header_html = '<strong class="green">User:</strong><br>'
            elif role == "assistant":
                message_class = "assistant-message"
                header_html = '<strong class="blue">Assistant:</strong><br>'
            else:
                message_class = "unknown-role"
                header_html = f"<strong>{role.upper()}:</strong><br>"

            # Start message div
            output_pieces.append(f'<div class="{message_class}">')
            output_pieces.append(header_html)

            # Handle content
            content = msg.get("content", "")
            if isinstance(content, list):
                for content_block in content:
                    if isinstance(content_block, dict):
                        block_type = content_block.get("type")

                        if block_type == "tool_result":
                            tool_id = content_block.get("name", "unknown")
                            output_pieces.append(
                                f'<div class="tool-use"><strong>Tool Result [ID: {tool_id}]:</strong></div>'
                            )

                            for item in content_block.get("content", []):
                                item_type = item.get("type")
                                if item_type == "text":
                                    text = item.get("text", "")
                                    output_pieces.append(
                                        f'<div class="tool-output green">Text: {text}</div>'
                                    )
                                elif item_type == "image":
                                    # If you have base64 image data, you can embed it directly
                                    # For now, as per your original code:
                                    output_pieces.append(
                                        '<div class="tool-output"><em>Image Source: base64 source too big</em></div>'
                                    )
                        elif block_type == "tool_use":
                            tool_name = content_block.get("name", "unknown")
                            output_pieces.append(
                                f'<div class="tool-use"><strong>Using tool: {tool_name}</strong></div>'
                            )

                            inputs = content_block.get("input", {})
                            if isinstance(inputs, dict):
                                output_pieces.append('<div class="tool-input">')
                                for key, value in inputs.items():
                                    # Truncate long inputs if necessary
                                    display_value = (
                                        (value[:100] + "...")
                                        if isinstance(value, str) and len(value) > 100
                                        else value
                                    )
                                    output_pieces.append(f"<div>{key}: {display_value}</div>")
                                output_pieces.append("</div>")
                        else:
                            # For other types of content blocks
                            for key, value in content_block.items():
                                output_pieces.append(
                                    f'<div class="{key}">{key}: {value}</div>'
                                )
                    else:
                        # If content_block is not a dict
                        output_pieces.append(f"<div>{content_block}</div>")
            else:
                # If content is a simple string
                output_pieces.append(f"<div>{content}</div>")

            # Separator for readability
            output_pieces.append("<hr>")
            # Close message div
            output_pieces.append("</div>")

        # Join all HTML pieces into a single string
        return "".join(output_pieces)

    except Exception as e:
        # Return the error as an HTML-formatted string
        return f"<div class='error red'>Error during formatting: {str(e)}</div>"

def rr(strin):
    pass

# --- LOAD SYSTEM PROMPT ---
with open(
    CWD / "system_prompt.md", "r", encoding="utf-8"
) as f:
    SYSTEM_PROMPT = f.read()


def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> dict:
    """Convert tool result to API format."""
    tool_result_content = []
    is_error = False
    ic(result)
    # if result is a ToolFailure, print the error message
    if isinstance(result, str):
        ic(f"Tool Failure: {result}")
        is_error = True
        tool_result_content.append({"type": "text", "text": result})
    else:
        if result.output:
            tool_result_content.append({"type": "text", "text": result.output})
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

# --- TOKEN TRACKER ---
import html

class TokenTracker:
    """Tracks total and recent token usage across all iterations."""

    def __init__(self):
        self.total_cache_creation = 0
        self.total_cache_retrieval = 0
        self.total_input = 0
        self.total_output = 0
        self.recent_cache_creation = 0
        self.recent_cache_retrieval = 0
        self.recent_input = 0
        self.recent_output = 0

    def update(self, response):
        """Update totals with new response usage."""
        self.recent_cache_creation = response.usage.cache_creation_input_tokens
        self.recent_cache_retrieval = response.usage.cache_read_input_tokens
        self.recent_input = response.usage.input_tokens
        self.recent_output = response.usage.output_tokens

        self.total_cache_creation += self.recent_cache_creation
        self.total_cache_retrieval += self.recent_cache_retrieval
        self.total_input += self.recent_input
        self.total_output += self.recent_output

    def display(self):
        """Display recent and total token usage as HTML."""
        # Construct HTML for Recent Token Usage
        recent_html = f"""
        <div class="token-section">
            <h3 class="yellow">Recent Token Usage 📊</h3>
            <p><strong class="yellow">Recent Cache Creation Tokens:</strong> {self.recent_cache_creation:,}</p>
            <p><strong class="yellow">Recent Cache Retrieval Tokens:</strong> {self.recent_cache_retrieval:,}</p>
            <p><strong class="yellow">Recent Input Tokens:</strong> {self.recent_input:,}</p>
            <p><strong class="yellow">Recent Output Tokens:</strong> {self.recent_output:,}</p>
            <p><strong class="yellow">Recent Tokens Used:</strong> {self.recent_cache_creation + self.recent_cache_retrieval + self.recent_input + self.recent_output:,}</p>
        </div>
        """

        # Construct HTML for Total Token Usage
        total_html = f"""
        <div class="token-section">
            <h3 class="yellow">Total Token Usage 📈</h3>
            <p><strong class="yellow">Total Cache Creation Tokens:</strong> {self.total_cache_creation:,}</p>
            <p><strong class="yellow">Total Cache Retrieval Tokens:</strong> {self.total_cache_retrieval:,}</p>
            <p><strong class="yellow">Total Input Tokens:</strong> {self.total_input:,}</p>
            <p><strong class="yellow">Total Output Tokens:</strong> {self.total_output:,}</p>
            <p><strong class="yellow">Total Tokens Used:</strong> {self.total_cache_creation + self.total_cache_retrieval + self.total_input + self.total_output:,}</p>
        </div>
        """

        # Combine both sections
        combined_html = recent_html + total_html

        # Send the combined HTML to the output buffer
        write_to_buffer(combined_html)

# --- JOURNALING ---
JOURNAL_MODEL = "claude-3-5-haiku-latest"
SUMMARY_MODEL = "claude-3-5-sonnet-latest"
JOURNAL_MAX_TOKENS = 1500

def _extract_text_from_content(content: Any) -> str:
    """Extracts text from potentially nested content structures."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif item.get("type") == "tool_result":
                    for sub_item in item.get("content", []):
                        if sub_item.get("type") == "text":
                            text_parts.append(sub_item.get("text", ""))
        return " ".join(text_parts)
    return ""

def truncate_message_content(content: Any, max_length: int = 9250000) -> Any:
    """Truncate message content while preserving structure."""
    if isinstance(content, str):
        return content[:max_length]
    elif isinstance(content, list):
        return [truncate_message_content(item, max_length) for item in content]
    elif isinstance(content, dict):
        return {
            k: truncate_message_content(v, max_length) if k != "source" else v
            for k, v in content.items()
        }
    return content

# --- MAIN SAMPLING LOOP ---
async def sampling_loop(
    *,
    model: str,
    messages: List[BetaMessageParam],
    api_key: str,
    max_tokens: int = 8000,
    output_manager: OutputManager,  # Add this parameter
    display: AgentDisplay,
) -> List[BetaMessageParam]:
    """Main loop for agentic sampling."""
    try:
        tool_collection = ToolCollection(
            BashTool(),
            EditTool(),
            GetExpertOpinionTool(),
            ComputerTool(),
            WebNavigatorTool(),
        )
        system = BetaTextBlockParam(type="text", text=SYSTEM_PROMPT)
        client = Anthropic(api_key=api_key)
        i = 0
        display.add_message("tool", tool_collection.get_tool_names_as_string())

        running = True
        token_tracker = TokenTracker()
        # display.update_display()
        journal_entry_count = 1
        if os.path.exists(JOURNAL_FILE):
            with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
                journal_entry_count = sum(1 for line in f if line.startswith("Entry #")) + 1

        enable_prompt_caching = True
        previous_message_count = 0

        while running:
            # output_manager.message_queue.put(
            #     f"<div class='iteration-info'>Iteration {i}</div>"
            # )
            display.add_message("system", f"<div class='iteration-info'>Iteration {i}</div>")
            betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
            image_truncation_threshold = 1
            only_n_most_recent_images = 2
            i += 1

            if enable_prompt_caching:
                _inject_prompt_caching(messages)
                image_truncation_threshold = 1
                system = [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                ]

            if only_n_most_recent_images:
                _maybe_filter_to_n_most_recent_images(
                    messages,
                    only_n_most_recent_images,
                    min_removal_threshold=image_truncation_threshold,
                )

            try:
                tool_collection.to_params()
                for msg in messages:
                    if msg["content"] == "":
                        msg["content"] = "continue"

                response = client.beta.messages.create(
                    max_tokens=MAX_SUMMARY_TOKENS,
                    messages=messages,
                    model=MAIN_MODEL,
                    system=system,
                    tools=tool_collection.to_params(),
                    betas=betas,
                )

                token_tracker.update(response)
                response_params = []
                for block in response.content:
                    if hasattr(block, "text"):
                        response_params.append({"type": "text", "text": block.text})
                        output_manager.format_api_response(
                            response
                        )  # Use the output manager
                    elif getattr(block, "type", None) == "tool_use":
                        response_params.append(
                            {
                                "type": "tool_use",
                                "name": block.name,
                                "id": block.id,
                                "input": block.input,
                            }
                        )
                messages.append({"role": "assistant", "content": response_params})
                write_messages_to_file(messages, MESSAGES_FILE)
                new_messages = messages[-2:]
                # conversation_html = format_messages_to_html(messages)
                # output_manager.message_queue.put(conversation_html)  # Update the message queue
                previous_message_count = len(messages)

                tool_result_content: List[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    if content_block["type"] == "tool_use":
                        result = await tool_collection.run(
                            name=content_block["name"],
                            tool_input=content_block["input"],
                        )
                        output_manager.format_tool_output(
                            result, content_block["name"]
                        )  # Use the output manager
                        tool_result = _make_api_tool_result(
                            result, content_block["id"]
                        )
                        tool_result_content.append(tool_result)
                if not tool_result_content and len(messages) > 4:
                    # task = input("What would you like to do next? Enter 'no' to exit: ")
                    task = Prompt.ask(
                        "What would you like to do next? Enter 'no' to exit"
                    )
                    display.add_message("user", task)
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                    # output_manager.message_queue.put(
                    #     f"<div class='user-message'>User: {task}</div>"
                    # )  # Update the message queue
                else:
                    messages.append({"role": "user", "content": tool_result_content})

            except UnicodeEncodeError as ue:
                print(f"UnicodeEncodeError: {ue}")
                # output_manager.message_queue.put(
                #     f"<div class='error'>Unicode encoding error: {ue}</div>"
                # )
                display.add_message("system", f"<div class='error'>Unicode encoding error: {ue}</div>")
                break
            except Exception as e:
                print(f"Error in sampling loop: {str(e)}")
                # output_manager.message_queue.put(
                #     f"<div class='error'>Error: {str(e)}</div>"
                # )
                display.add_message("system", f"<div class='error'>Error: {str(e)}</div>")
                raise
        return messages

    except Exception as e:
        print(f"Error initializing sampling loop: {str(e)}")
        # output_manager.message_queue.put(
        #     f"<div class='error'>Initialization Error: {str(e)}</div>"
        # )
        display.add_message("system", f"<div class='error'>Initialization Error: {str(e)}</div>")
        raise

def _inject_prompt_caching(messages: List[BetaMessageParam]):
    """Set cache breakpoints for the 3 most recent turns."""
    breakpoints_remaining = 2
    for msg in messages:
        ic(msg)
    ic(len(messages))
    for message in reversed(messages):
        ic(message)
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            if breakpoints_remaining:
                ic(breakpoints_remaining)
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
                # if no more breakpoints, remove cache control
                # from the last message
                if breakpoints_remaining == 0:
                    content[-1].pop("cache_control", None)
                    break

def _maybe_filter_to_n_most_recent_images(
    messages: List[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
):
    """Remove older images from tool results in place."""
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        List[BetaToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    images_to_remove = 0
    images_found = 0
    for tool_result in reversed(tool_result_blocks):
        if isinstance(tool_result.get("content"), list):
            for content in reversed(tool_result.get("content", [])):
                if isinstance(content, dict) and content.get("type") == "image":
                    images_found += 1

    images_to_remove = max(0, images_found - images_to_keep)

    removed = 0
    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if removed < images_to_remove:
                        removed += 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content

async def run_sampling_loop(
    task: str, output_manager: OutputManager, display: AgentDisplay
) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    if not api_key:
        raise ValueError(
            "API key not found. Please set the ANTHROPIC_API_KEY environment variable."
        )
    messages.append({"role": "user", "content": task})
    # output_manager.message_queue.put(
    #     f"<div class='user-message'>User: {task}</div>"
    # )  # Add initial message
    display.add_message("user", task)
    messages = await sampling_loop(
        model="claude-3-5-sonnet-latest",
        messages=messages,
        api_key=api_key,
        output_manager=output_manager,
        display=display
    )
    return messages

async def main_async():
    """Async main function with proper error handling."""
    # Initialize AgentDisplay and OutputManager
    display = AgentDisplay()
    output_manager = OutputManager(display)

    # Get list of available prompts
    current_working_dir = Path(os.getcwd())
    prompts_dir = current_working_dir / "prompts"
    prompt_files = list(prompts_dir.glob("*.md"))

    # Display options
    print("\n[bold yellow]Available Prompts:[/bold yellow]")
    for i, file in enumerate(prompt_files, 1):
        print(f"{i}. {file.name}")
    print(f"{len(prompt_files) + 1}. Create new prompt")

    # Get user choice
    choice = input("Select prompt number: ")

    if int(choice) == len(prompt_files) + 1:
        # Create new prompt
        filename = input("Enter new prompt filename (without .md): ")
        prompt_text = input("Enter your prompt: ")
        # Save new prompt
        new_prompt_path = prompts_dir
        new_prompt_path = prompts_dir / f"{filename}.md"
        with open(new_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        task = prompt_text
        print(f"New prompt saved to {new_prompt_path}")
    else:
        # Read existing prompt
        prompt_path = prompt_files[int(choice) - 1]
        with open(prompt_path, 'r', encoding='utf-8') as f:
            task = f.read()
        print(f"Selected prompt: {prompt_path}")

    # Use Live display context
    with Live(display.create_layout(), refresh_per_second=4) as live:
        # Start the display update task
        update_task = asyncio.create_task(display.update_display(live))

        try:
            # Run the sampling loop
            messages = await run_sampling_loop(task, output_manager, display)
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            # Ensure the update task is cancelled
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass

def main():
    """Main entry point with proper async handling."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
