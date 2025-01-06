import re
from icecream import ic
from datetime import datetime
from typing import cast, List, Optional, Any
from pathlib import Path
from anthropic import APIResponse
from anthropic.types.beta import BetaContentBlock
import hashlib
import base64
import os
import asyncio  
import pyautogui
from rich import print as rr
from icecream import install
from rich.prompt import Prompt
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
import ftfy
import json
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential_jitter
from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult, GetExpertOpinionTool, WebNavigatorTool#,  GoogleSearchTool # windows_navigate
from load_constants import (
    MAX_SUMMARY_MESSAGES,
    MAX_SUMMARY_TOKENS,
    ICECREAM_OUTPUT_FILE,
    JOURNAL_FILE,
    JOURNAL_ARCHIVE_FILE,
    COMPUTER_USE_BETA_FLAG,
    PROMPT_CACHING_BETA_FLAG,
    JOURNAL_MODEL,
    SUMMARY_MODEL,
    JOURNAL_MAX_TOKENS,
    JOURNAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    MAIN_MODEL,
    reload_prompts
)


from typing import Optional, List
from pathlib import Path
import base64
from datetime import datetime
import hashlib
from rich import print as rr
from rich.panel import Panel
from rich.console import Group
from rich.table import Table
from rich.text import Text
import json

from dotenv import load_dotenv
load_dotenv()
install()
# get the current working directory
CWD = Path.cwd()
MAX_SUMMARY_MESSAGES = 40
MAX_SUMMARY_TOKENS = 8000
ICECREAM_OUTPUT_FILE =  CWD / "debug_log.json"
# JOURNAL_FILE = r"C:\mygit\compuse\computer_use_demo\journal\journal.log"
# JOURNAL_ARCHIVE_FILE = "journal/journal.log.archive"
MESSAGES_FILE = CWD / "messages.json"
# --- ARCHIVE OLD LOGS ---
"""Archives a file by appending it to an archive file and clearing the original.

This function takes a file path, an archive suffix, and an optional header text. It reads the contents of the file, appends them to an archive file with the given suffix, and then clears the original file. The header text, if provided, is written to the archive file before the file contents.

Args:
    filepath (str): The path to the file to be archived.
    archive_suffix (str): The suffix to be added to the archive file name.
    header_text (Optional[str]): The header text to be written to the archive file.
"""
def archive_file(filepath: str, archive_suffix: str, header_text: Optional[str] = None):
    """Archives a file by appending it to an archive file and clearing the original."""
    if not os.path.exists(filepath):
        return
    try:
        with open(filepath, 'r', encoding='utf-8') as f_read:
            lines = f_read.readlines()
        with open(filepath + archive_suffix, 'a', encoding='utf-8') as f_archive:
            if header_text:
                f_archive.write('\n' + '='*50 + '\n')
                f_archive.write(f'{header_text} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f_archive.write('='*50 + '\n')
            f_archive.writelines(lines)
        with open(filepath, 'w', encoding='utf-8') as f_clear:
            f_clear.write('')
    except Exception as e:
        ic(f"Error archiving file {filepath}: {e}")

# archive_file(ICECREAM_OUTPUT_FILE, '.archive.json')
# archive_file(JOURNAL_FILE, '.archive', header_text="Archive from")

# --- CUSTOM LOGGING ---

def write_to_file(s: str, file_path: str = ICECREAM_OUTPUT_FILE):
    """Write debug output to a file, formatting JSON content in a pretty way."""
    lines = s.split('\n')
    formatted_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    for line in lines:
        if "tool_input:" in line:
            try:
                # Extract JSON part from the line
                json_part = line.split("tool_input: ")[1]
                 # check if it looks like a json object
                if json_part.strip().startswith('{') and json_part.strip().endswith('}'):
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
    with open(file_path, 'a', encoding="utf-8") as f:
        f.write('\n'.join(formatted_lines))
        f.write('\n' + '-' * 80 + '\n')
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
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for msg in messages:
                f.write(f"\n{msg['role'].upper()}:\n")
                
                # Handle content based on its type
                if isinstance(msg['content'], list):
                    for content_block in msg['content']:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "tool_result":
                                f.write(f"Tool Result [ID: {content_block.get('name', 'unknown')}]:\n")
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
            with open(error_file_path, 'w', encoding='utf-8') as error_file:
                error_file.write(f"Error during execution: {str(e)}\n")
        except:
            # If we can't even write to the error file, return False
            pass
        return False
# --- LOAD SYSTEM PROMPT ---
with open(Path(r"C:\mygit\compuse\computer_use_demo\system_prompt.md"), 'r', encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# # --- OUTPUT MANAGER ---
# class OutputManager:
#     """Manages and formats tool outputs and responses."""
#     def __init__(self, image_dir: Optional[Path] = None ):
#         #CWD = Path.cwd()
#         # Set up image directory
#         if image_dir is None:
#             self.image_dir = Path("default_images")
#         else:
#             self.image_dir = image_dir
#         (CWD / self.image_dir).mkdir(parents=True, exist_ok=True)
#         self.image_counter = 0

#     def save_image(self, base64_data: str) -> Optional[Path]:
#         """Save base64 image data to file and return path."""
#         #CWD = Path.cwd()
#         self.image_counter += 1
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         # Create a short hash of the image data for uniqueness
#         image_hash = hashlib.md5(base64_data.encode()).hexdigest()[:8]
#         image_path = self.image_dir / f"image_{timestamp}_{image_hash}.png"

#         try:
#             image_data = base64.b64decode(base64_data)
#             with open(image_path, 'wb') as f:
#                 f.write(image_data)
#             return image_path
#         except Exception as e:
#             ic(f"Error saving image: {e}")
#             return None

#     def format_tool_output(self, result: ToolResult, tool_name: str) -> None:
#         """Format and print tool output without base64 data."""
#         rr("\n[bold blue]Tool Execution[/bold blue] 🛠️")
#         rr(f"[blue]Tool Name:[/blue] {tool_name}")

#         if isinstance(result, str):
#             rr(f"[red]Error:[/red] {result}")
#         else:
#             if result.output:
#                 # Safely truncate long output
#                 output_text = result.output
#                 if len(output_text) > 500:
#                     output_text = output_text[:200] + "/n.../n" + output_text[-200:]
#                 rr(f"[green]Output:[/green] {output_text}")
            
#             if result.base64_image:
#                 image_path = self.save_image(result.base64_image)
#                 if image_path:
#                     rr(f"[green]📸 Screenshot saved to {image_path}[/green]")
#                 else:
#                     rr("[red]Failed to save screenshot[/red]")

#     def format_api_response(self, response: APIResponse) -> None:
#         """Format and print API response."""
#         rr("\n[bold purple]Assistant Response[/bold purple] 🤖")
#         if hasattr(response.content[0], 'text'):
#             text = response.content[0].text
#             if len(text) > 500:
#                 text = text[:300] + "..." + text[-300:]
#             rr(f"[purple]{text}[/purple]")

#     def format_content_block(self, block: BetaContentBlock) -> None:
#         """Format and print content block."""
#         if getattr(block, 'type', None) == "tool_use":
#             ic(f"\nTool Use: {block.name}")
#             # Only print non-image related inputs
#             safe_input = {k: v for k, v in block.input.items()
#                          if not isinstance(v, str) or len(v) < 1000}
#             ic(f"Input: {safe_input}")
#         elif hasattr(block, 'text'):
#             ic(f"\nText: {block.text}")

#     def format_recent_conversation(self, messages: List[BetaMessageParam], num_recent: int = 2) -> None:
#         """Format and print the most recent conversation exchanges."""
#         rr("\n[bold yellow]Recent Conversation[/bold yellow] 💭")
        
#         # Get the most recent messages
#         recent_messages = messages[-num_recent*2:] if len(messages) > num_recent*2 else messages
        
#         for msg in recent_messages:
#             if msg['role'] == 'user':
#                 rr("\n[bold green]User[/bold green] 👤")
#                 content = msg['content']
#                 if isinstance(content, list):
#                     for content_block in content:
#                         if isinstance(content_block, dict):
#                             if content_block.get("type") == "tool_result":
#                                 rr(f"[green]Tool Result:[/green]")
#                                 for item in content_block.get("content", []):
#                                     if item.get("type") == "text":
#                                         text = item.get("text", "")
#                                         if len(text) > 500:
#                                             text = text[:200] + "/n.../n" + text[-200:]
#                                         rr(f"{text}")
#                                     elif item.get("type") == "image":
#                                         rr("[dim]📸 (Screenshot captured)[/dim]")
#                 else:
#                     if isinstance(content, str):
#                         if len(content) > 500:
#                             content = content[:300] + "..." + content[-300:]
#                         rr(f"{content}")
            
#             elif msg['role'] == 'assistant':
#                 rr("\n[bold blue]Assistant[/bold blue] 🤖")
#                 content = msg['content']
#                 if isinstance(content, list):
#                     for content_block in content:
#                         if isinstance(content_block, dict):
#                             if content_block.get("type") == "text":
#                                 text = content_block.get("text", "")
#                                 if len(text) > 500:
#                                     text = text[:400] + "..." + text[-400:]
#                                 rr(f"[blue]{text}[/blue]")
#                             elif content_block.get("type") == "tool_use":
#                                 rr(f"[cyan]Using tool:[/cyan] {content_block.get('name')}")
#                                 for k, v in content_block.get('input', {}).items():
#                                     rr(f"[cyan]{k}:[/cyan] {v}")
#                                 tool_input = content_block.get('input', "")
#                                 # if isinstance(tool_input, str) and len(tool_input) > 500:
#                                     # tool_input = tool_input[:200] + "/n.../" + tool_input[-200:]
#                                 # rr(f"[cyan]With input:[/cyan] {tool_input}")
#                                 if isinstance(tool_input, str):
#                                     # try to load as json
#                                     try:
#                                         tool_input = json.loads(tool_input)
#                                         rr(f"[cyan]With input:[/cyan]")
#                                         for key, value in tool_input.items():
#                                             if isinstance(value, str) and len(value) > 500:
#                                                 rr(f"[cyan]{key}:[/cyan] {value[:200] + '/n.../n'  + value[-200:]}")
#                                             else:
#                                                 rr(f"[cyan]{key}:[/cyan] {value}")  
#                                     except json.JSONDecodeError:
#                                         if isinstance(tool_input, str):
#                                             tool_input = tool_input[:200] + "/n.../" + tool_input[-200:]
#                                         rr(f"[cyan]With input:[/cyan] {tool_input}")
                                        

#                 elif isinstance(content, str):
            
#                     if len(content) > 500:
#                         content = content[:200] + "/n.../n" + content[-200:]
#                     rr(f"[blue]{content}[/blue]")

#         rr("\n" + "="*50 + "\n")

class OutputManager:
    """Manages and formats tool outputs and responses."""
    def __init__(self, image_dir: Optional[Path] = None ):
        #CWD = Path.cwd()
        # Set up image directory
        if image_dir is None:
            self.image_dir = Path("default_images")
        else:
            self.image_dir = image_dir
        (CWD / self.image_dir).mkdir(parents=True, exist_ok=True)
        self.image_counter = 0
        self.max_output_length = 800  # Define a maximum length for outputs

    def _truncate_text(self, text: str) -> str:
        """Truncate text if it exceeds the maximum length."""
        if len(text) > self.max_output_length:
            return f"{text[:self.max_output_length // 2]}...\n[dim](truncated - see full output in logs)[/dim]\n...{text[-self.max_output_length // 2:]}"
        return text

    def save_image(self, base64_data: str) -> Optional[Path]:
        """Save base64 image data to file and return path."""
        #CWD = Path.cwd()
        self.image_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a short hash of the image data for uniqueness
        image_hash = hashlib.md5(base64_data.encode()).hexdigest()[:8]
        image_path = self.image_dir / f"image_{timestamp}_{image_hash}.png"

        try:
            image_data = base64.b64decode(base64_data)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            return image_path
        except Exception as e:
            rr(f"[bold red]Error saving image:[/bold red] {e}")
            return None

    def format_tool_output(self, result: ToolResult, tool_name: str) -> None:
        """Format and print tool output."""
        tool_panel_elements = []
        tool_panel_elements.append(Text.from_markup(f"[bold blue]Tool Execution[/bold blue] 🛠️", justify="center"))
        tool_panel_elements.append(Text.from_markup(f"[blue]Tool Name:[/blue] {tool_name}"))

        if isinstance(result, str):
            tool_panel_elements.append(Text.from_markup(f"[bold red]Error:[/bold red] {self._truncate_text(result)}"))
        else:
            if result.output:
                tool_panel_elements.append(Text.from_markup(f"[green]Output:[/green]"))
                tool_panel_elements.append(Panel(self._truncate_text(result.output), style="green"))

            if result.base64_image:
                image_path = self.save_image(result.base64_image)
                if image_path:
                    tool_panel_elements.append(Text.from_markup(f"[green]📸 Screenshot saved to {image_path}[/green]"))
                else:
                    tool_panel_elements.append(Text.from_markup("[bold red]Failed to save screenshot[/bold red]"))

            if result.logs:
                tool_panel_elements.append(Text.from_markup("[dim]Logs:[/dim]"))
                tool_panel_elements.append(Panel(self._truncate_text(result.logs), style="dim"))

            if result.exception:
                tool_panel_elements.append(Text.from_markup("[bold red]Exception:[/bold red]"))
                tool_panel_elements.append(Panel(self._truncate_text(result.exception), style="bold red"))

        rr(Panel(Group(*tool_panel_elements), title="Tool Result", border_style="blue"))

    def format_api_response(self, response: APIResponse) -> None:
        """Format and print API response."""
        response_panel_elements = []
        response_panel_elements.append(Text.from_markup("[bold purple]Assistant Response[/bold purple] 🤖", justify="center"))
        if hasattr(response, 'content') and response.content:
            if hasattr(response.content[0], 'text') and response.content[0].text:
                response_panel_elements.append(Panel(self._truncate_text(response.content[0].text), style="purple"))
        else:
            response_panel_elements.append(Text.from_markup("[italic dim]No response content.[/italic dim]"))

        rr(Panel(Group(*response_panel_elements), title="Assistant Response", border_style="purple"))

    def format_content_block(self, block: BetaContentBlock) -> None:
        """Format and print content block."""
        if getattr(block, 'type', None) == "tool_use":
            tool_use_elements = []
            tool_use_elements.append(Text.from_markup(f"[bold cyan]Tool Use:[/bold cyan] {block.name}", justify="center"))
            if block.input:
                input_table = Table(show_header=True, header_style="bold magenta")
                input_table.add_column("Input Key", style="magenta")
                input_table.add_column("Value")
                for k, v in block.input.items():
                    if isinstance(v, str) and len(v) > self.max_output_length:
                        v = f"{v[:self.max_output_length // 2]}...[dim](truncated)[/dim]...{v[-self.max_output_length // 2:]}"
                    input_table.add_row(k, str(v))
                tool_use_elements.append(input_table)
            rr(Panel(Group(*tool_use_elements), title="Tool Invocation", border_style="cyan"))

        elif hasattr(block, 'text') and block.text:
            rr(Panel(self._truncate_text(block.text), title="Text Content", border_style="green"))

    def format_recent_conversation(self, messages: List[BetaMessageParam], num_recent: int = 1) -> None:
        """Format and print the most recent conversation exchanges."""
        rr(Panel(Text.from_markup("[bold yellow]Recent Conversation[/bold yellow] 💭", justify="center"), border_style="yellow"))

        # Get the most recent messages
        recent_messages = messages[-num_recent*2:] if len(messages) > num_recent*2 else messages

        for msg in recent_messages:
            if msg['role'] == 'user':
                user_elements = [Text.from_markup("[bold green]User[/bold green] 👤", justify="left")]
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "tool_result":
                                user_elements.append(Text.from_markup("[green]Tool Result:[/green]"))
                                for item in content_block.get("content", []):
                                    if item.get("type") == "text":
                                        user_elements.append(Panel(self._truncate_text(item.get("text", "")), style="green"))
                                    elif item.get("type") == "image":
                                        user_elements.append(Text.from_markup("[dim]📸 (Screenshot captured)[/dim]"))
                else:
                    if isinstance(content, str):
                        user_elements.append(Panel(self._truncate_text(content), style="green"))
                rr(Panel(Group(*user_elements), border_style="green"))

            elif msg['role'] == 'assistant':
                assistant_elements = [Text.from_markup("[bold blue]Assistant[/bold blue] 🤖", justify="left")]
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "text":
                                assistant_elements.append(Panel(self._truncate_text(content_block.get("text", "")), style="blue"))
                            elif content_block.get("type") == "tool_use":
                                assistant_elements.append(Text.from_markup(f"[cyan]Using tool:[/cyan] {content_block.get('name')}"))
                                if 'input' in content_block and isinstance(content_block['input'], dict):
                                    input_table = Table(show_header=True, header_style="bold magenta")
                                    input_table.add_column("Input Key", style="magenta")
                                    input_table.add_column("Value")
                                    for key, value in content_block['input'].items():
                                        if isinstance(value, str) and len(value) > self.max_output_length:
                                            value = f"{value[:self.max_output_length // 2]}...[dim](truncated)[/dim]...{value[-self.max_output_length // 2:]}"
                                        input_table.add_row(key, str(value))
                                    assistant_elements.append(input_table)

                elif isinstance(content, str):
                    assistant_elements.append(Panel(self._truncate_text(content), style="blue"))
                rr(Panel(Group(*assistant_elements), border_style="blue"))

        rr("-" * 50)

# --- TOOL RESULT CONVERSION ---
def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> dict:
    """Convert tool result to API format."""
    tool_result_content = []
    is_error = False
    ic(result)
    # if result is a ToolFailure, print the error message
    if isinstance(result, str):
        ic(f"Tool Failure: {result}")
        is_error = True
        tool_result_content.append({
            "type": "text",
            "text": result
        })
    else:
        if result.output:
            tool_result_content.append({
                "type": "text",
                "text": result.output
            })
        if result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                }
            })

    
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }

# --- BETA FLAGS ---
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

# --- TOKEN TRACKER ---
class TokenTracker:
    """Tracks total token usage across all iterations."""
    def __init__(self):
        self.total_cache_creation = 0
        self.total_cache_retrieval = 0
        self.total_input = 0
        self.total_output = 0
    
    def update(self, response):
        """Update totals with new response usage."""
        self.total_cache_creation += response.usage.cache_creation_input_tokens
        self.total_cache_retrieval += response.usage.cache_read_input_tokens
        self.total_input += response.usage.input_tokens
        self.total_output += response.usage.output_tokens
    
    def display(self):
        """Display total token usage."""
        rr("\n[bold yellow]Total Token Usage Summary[/bold yellow] 📊")
        rr(f"[yellow]Total Cache Creation Tokens:[/yellow] {self.total_cache_creation:,}")
        rr(f"[yellow]Total Cache Retrieval Tokens:[/yellow] {self.total_cache_retrieval:,}")
        rr(f"[yellow]Total Input Tokens:[/yellow] {self.total_input:,}")
        rr(f"[yellow]Total Output Tokens:[/yellow] {self.total_output:,}")
        rr(f"[bold yellow]Total Tokens Used:[/bold yellow] {self.total_cache_creation + self.total_cache_retrieval + self.total_input + self.total_output:,}")

# --- JOURNALING ---
JOURNAL_MODEL = "claude-3-5-haiku-latest"
SUMMARY_MODEL = "claude-3-5-sonnet-latest"
JOURNAL_MAX_TOKENS = 1500
JOURNAL_SYSTEM_PROMPT_FILE = r"C:\mygit\compuse\computer_use_demo\journal\journal.log"
with open(JOURNAL_SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
    JOURNAL_SYSTEM_PROMPT = f.read()

    """Creates a concise journal entry using Claude Haiku."""
    try:
        user_message = ""
        assistant_response = ""
        for msg in reversed(messages): 

            if msg['role'] == 'user':
                user_message = _extract_text_from_content(msg['content'])
            if msg['role'] == 'assistant' and response.content:
                assistant_response = " ".join([block.text for block in response.content if hasattr(block, 'text')])
        if not user_message or not assistant_response:
            ic("Skipping journal entry - missing content")
            # return
        journal_prompt = f"Summarize this interaction:\nUser: {user_message}\nAssistant: {assistant_response}"
        # rr(f"Journal Prompt:\n {journal_prompt}")
        haiku_response = client.messages.create(
            model=JOURNAL_MODEL,
            max_tokens=JOURNAL_MAX_TOKENS,
            messages=[{"role": "user", "content": journal_prompt}],
            system=JOURNAL_SYSTEM_PROMPT
        )
        summary = haiku_response.content[0].text.strip()
        if not summary:
            ic("Skipping journal entry - no summary generated")
            # return
        # rr(f"Journal Summary:\n {summary}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        journal_entry = f"\nEntry #{entry_number} - {timestamp}\n{summary}\n-------------------\n"
        os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
        journal_entry = ftfy.fix_text(journal_entry)
        with open(JOURNAL_FILE, 'a', encoding='utf-8') as f:
            f.write(journal_entry)
        ic(f"Created journal entry #{entry_number}")
    except Exception as e:
        ic(f"Error creating journal entry: {str(e)}")

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

def get_journal_contents() -> str:
    """Read and return the contents of the journal file."""
    try:
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            file_contents =  f.read()
            return ftfy.fix_text(file_contents)
    except FileNotFoundError:
        return "No journal entries yet."
async def create_journal_entry(entry_number: int, messages: List[BetaMessageParam], response: APIResponse, client: Anthropic):
    #CWD = Path.cwd()
    try:
        # Get current journal contents
        current_journal = get_journal_contents()
        # Extract recent messages
        recent_messages = []
        conversation_text = ""
        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            
            if isinstance(content, list):
                # Handle complex content (tool results, tool use, etc.)
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            conversation_text += f"\n{role}: {block.get('text', '')}"
                        elif block.get('type') == 'tool_use':
                            conversation_text += f"\n{role} (Tool Use): Tool: {block.get('name', '')}\nInput: {json.dumps(block.get('input', ''), indent=2)}"
                        elif block.get('type') == 'tool_result':
                            for item in block.get('content', []):
                                if item.get('type') == 'text':
                                    conversation_text += f"\n{role} (Tool Result): {item.get('text', '')}"
                                elif item.get('type') == 'image':
                                    conversation_text += f"\n{role} (Tool Result): [Image Generated]"
                        else:
                            conversation_text += f"\n{role}: {content}"

        # Create prompt with both current journal and recent messages
        journal_prompt = f"""
        Current Journal Contents:
        {current_journal}

        Recent Messages:
        {conversation_text}

        Please provide an updated comprehensive journal entry that incorporates both the existing progress and new developments.
        """

        # Get updated journal from Haiku
        haiku_response = client.messages.create(
            model=JOURNAL_MODEL,
            max_tokens=JOURNAL_MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": journal_prompt
            }],
            system=JOURNAL_SYSTEM_PROMPT
        )

        updated_journal = haiku_response.content[0].text.strip()
        if not updated_journal:
            ic("Error: No journal update generated")
            return

        # Write the updated journal
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        journal_entry = f"\nEntry #{entry_number} - {timestamp}\n{updated_journal}\n-------------------\n"
        
        # Ensure directory exists and write entry
        os.makedirs(os.path.dirname(CWD / JOURNAL_FILE), exist_ok=True)
        journal_entry = ftfy.fix_text(journal_entry)
        with open(CWD / JOURNAL_FILE, 'w', encoding='utf-8') as f:  # Note: using 'w' instead of 'a'
            f.write(journal_entry)
            
        ic(f"Created updated journal entry #{entry_number}")

    except Exception as e:
        ic(f"Error creating journal entry: {str(e)}")

def truncate_message_content(content: Any, max_length: int = 9250000) -> Any:
    """Truncate message content while preserving structure."""
    if isinstance(content, str):
        return content[:max_length]
    elif isinstance(content, list):
        return [truncate_message_content(item, max_length) for item in content]
    elif isinstance(content, dict):
        return {k: truncate_message_content(v, max_length) if k != 'source' else v
                for k, v in content.items()}
    return content

# --- MAIN SAMPLING LOOP ---
async def sampling_loop(*, model: str, messages: List[BetaMessageParam], api_key: str, max_tokens: int = 8000,) -> List[BetaMessageParam]:
    """Main loop for agentic sampling."""
    ic(messages)
    try:
        tool_collection = ToolCollection(
            BashTool(),
            EditTool(),
            GetExpertOpinionTool(),
            ComputerTool(),
            WebNavigatorTool(),
            # WindowsNavigationTool ()
        )
        system = BetaTextBlockParam(type="text", text=SYSTEM_PROMPT)
        output_manager = OutputManager()
        client = Anthropic(api_key=api_key)
        i = 0
        ic(i)
        running = True
        token_tracker = TokenTracker()
        journal_entry_count = 1
        if os.path.exists(JOURNAL_FILE):
             with open(JOURNAL_FILE, 'r',encoding='utf-8') as f:
                 journal_entry_count = sum(1 for line in f if line.startswith("Entry #")) + 1
        journal_contents = get_journal_contents()
        messages.append({
            "role": "user",
            "content": f"Previous conversation history from journal:\n{journal_contents}"
        })

        while running:
            rr(f"\n[bold yellow]Iteration {i}[/bold yellow] 🔄")
            enable_prompt_caching = True
            betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
            image_truncation_threshold = 1
            only_n_most_recent_images = 2
            i+=1
            if enable_prompt_caching:
                _inject_prompt_caching(messages)
                image_truncation_threshold = 1
                system=[
                            {
                                "type": "text",
                                "text": SYSTEM_PROMPT,
                                "cache_control": {"type": "ephemeral"}
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
                ic(messages)

                truncated_messages = [
                    {"role": msg["role"], "content": truncate_message_content(msg["content"])}
                    for msg in messages
                ]
                # append only the the most recent message to the file MESSAGES_FILE
                with open(MESSAGES_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(truncated_messages[-1]) + "\n")

                response = client.beta.messages.create(
                    max_tokens=MAX_SUMMARY_TOKENS,
                    messages=truncated_messages,
                    model=MAIN_MODEL,
                    system=system,
                    tools=tool_collection.to_params(),
                    betas=betas,
                )

                token_tracker.update(response)
                token_tracker.display()

                ic(f"Response: {response}")
                response_params = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        # output_manager.format_api_response(response)
                        response_params.append({"type": "text", "text": block.text})
                    elif getattr(block, 'type', None) == "tool_use":
                        response_params.append({
                            "type": "tool_use",
                            "name": block.name,
                            "id": block.id,
                            "input": block.input
                        })
                messages.append({"role": "assistant", "content": response_params})
                # append the response to the file MESSAGES_FILE
                with open(MESSAGES_FILE, "a", encoding="utf-8") as f:
                    f.write(f"""
                             role": "assistant", "content": 
                             {response_params}""")
  
                output_manager.format_recent_conversation(messages)

                tool_result_content: List[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    # output_manager.format_content_block(content_block)
                    if content_block["type"] == "tool_use":
                        ic(f"Tool Use: {response_params}")
                        result = await tool_collection.run(
                            name=content_block["name"],
                            tool_input=content_block["input"],
                        )
                        ic.configureOutput(includeContext=True, outputFunction=write_to_file,argToStringFunction=repr)
                        ic(content_block)
                        # output_manager.format
                        # _tool_output(result, content_block["name"])
                        tool_result = _make_api_tool_result(result, content_block["id"])
                        ic(tool_result)
                        tool_result_content.append(tool_result)
                if not tool_result_content:
                    rr("\n[bold yellow]Awaiting User Input[/bold yellow] ⌨️")
                    task = Prompt.ask("What would you like to do next? Enter 'no' to exit")
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                else:
                    messages.append({"role": "user", "content": tool_result_content})
                rr(f"Creating journal entry #{journal_entry_count}")
                rr(f"There are {len(messages)} messages")

                if len(messages) > MAX_SUMMARY_MESSAGES:
                    rr(f"\n[yellow]Messages exceed {MAX_SUMMARY_MESSAGES} - generating summary...[/yellow]")
                    messages = await summarize_messages(messages)
                    rr("[green]Summary generated - conversation compressed[/green]")

                try:
                    await create_journal_entry(
                        entry_number=journal_entry_count,
                        messages=messages,
                    response=response,
                        client=client
                    )
                    journal_entry_count += 1
                except Exception as e:
                    ic(f"Error creating journal entry: {str(e)}")

            except UnicodeEncodeError as ue:
                ic(f"UnicodeEncodeError: {ue}")
                rr(f"Unicode encoding error: {ue}")
                rr(f"ascii: {ue.args[1].encode('ascii', errors='replace').decode('ascii')}")
                break
            except Exception as e:
                ic(f"Error in sampling loop: {str(e).encode('ascii', errors='replace').decode('ascii')}")
                ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
                ic(e.__traceback__.tb_frame.f_locals)
                raise
        token_tracker.display()
        return messages

    except Exception as e:
        ic(e.__traceback__.tb_lineno)
        ic(e.__traceback__.tb_lasti)
        ic(e.__traceback__.tb_frame.f_code.co_filename)
        ic(e.__traceback__.tb_frame)
        ic(f"Error initializing sampling loop: {str(e)}")
        raise


def _inject_prompt_caching(messages: List[BetaMessageParam]):
    """Set cache breakpoints for the 3 most recent turns."""
    breakpoints_remaining = 2
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(content := message["content"], list):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
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

async def summarize_messages(messages: List[BetaMessageParam]) -> List[BetaMessageParam]:
    """Summarize messages using Claude Haiku when they exceed MAX_SUMMARY_MESSAGES."""
    if len(messages) <= MAX_SUMMARY_MESSAGES:
        return messages
    original_prompt = messages[0]["content"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    summary_prompt = """Please provide a detailed technical summary of this conversation. Include:
1. All file names and paths mentioned
2. Directory structures created or modified
3. Specific actions taken and their outcomes
4. Any technical decisions or solutions implemented
5. Current status of the task
6. Any pending or incomplete items
7. Code that was written or modified

Original task prompt for context:
{original_prompt}

Conversation to summarize:
{conversation}"""

    conversation_text = ""
    for msg in messages[1:]:
        role = msg['role'].upper()
        if isinstance(msg['content'], list):
            for block in msg['content']:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        conversation_text += f"\n{role}: {block.get('text', '')}"
                    elif block.get('type') == 'tool_result':
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                conversation_text += f"\n{role} (Tool Result): {item.get('text', '')}"
        else:
            conversation_text += f"\n{role}: {msg['content']}"
    ic(summary_prompt.format(
                original_prompt=original_prompt,
                conversation=conversation_text
            ))
    response = client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=MAX_SUMMARY_TOKENS,
        messages=[{
            "role": "user",
            "content": summary_prompt.format(
                original_prompt=original_prompt,
                conversation=conversation_text
            )
        }]
    )
    summary = response.content[0].text
    ic(summary)

    new_messages = [
        messages[0],
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"[CONVERSATION SUMMARY]\n\n{summary}"
                }
            ]
        }
    ]
    return new_messages

async def run_sampling_loop(task: str) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    ic(messages)
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    ic(messages.append({"role": "user","content": task}))
    messages = await sampling_loop(
        model="claude-3-5-sonnet-latest",
        messages=messages,
        api_key=api_key,
    )
    return messages


async def main_async():

    """Async main function with proper error handling."""
    # Get list of available prompts
    current_working_dir = Path(os.getcwd())
    prompts_dir = current_working_dir / "prompts"
    rr(prompts_dir)
    prompt_files = list(prompts_dir.glob("*.md"))
    
    # Display options
    rr("\n[bold yellow]Available Prompts:[/bold yellow]")
    for i, file in enumerate(prompt_files, 1):
        rr(f"{i}. {file.name}")
    rr(f"{len(prompt_files) + 1}. Create new prompt")
    
    # Get user choice
    choice = Prompt.ask(
        "Select prompt number",
        choices=[str(i) for i in range(1, len(prompt_files) + 2)]
    )
    
    if int(choice) == len(prompt_files) + 1:
        # Create new prompt
        filename = Prompt.ask("Enter new prompt filename (without .md)")
        prompt_text = Prompt.ask("Enter your prompt")
        # Save new prompt
        new_prompt_path = prompts_dir / f"{filename}.md"
        with open(new_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        task = prompt_text
        rr(f"New prompt saved to {new_prompt_path}")
    else:
        # Read existing prompt
        prompt_path = prompt_files[int(choice) - 1]
        with open(prompt_path, 'r', encoding='utf-8') as f:
            task = f.read()
        rr(f"Selected prompt: {prompt_path}")
    try:
        messages = await run_sampling_loop(task)
        rr("\nTask Completed Successfully")
        
        # The token summary will be displayed here from sampling_loop
        
        rr("\nFinal Messages:")
        for msg in messages:
            rr(f"\n{msg['role'].upper()}:")
            # If content is a list of dicts (like tool_result), format accordingly
            if isinstance(msg['content'], list):
                for content_block in msg['content']:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "tool_result":
                            rr(f"Tool Result [ID: {content_block.get('name', 'unknown')}]:")
                            for item in content_block.get("content", []):
                                if item.get("type") == "text":
                                    rr(f"Text: {item.get('text')}")
                                elif item.get("type") == "image":
                                    rr("Image Source: base64 source too big")#{item.get('source', {}).get('data')}")
                        else:
                            for key, value in content_block.items():
                                rr(f"{key}: {value}")
                    else:
                        rr(content_block)
            else:
                rr(msg['content'])

    except Exception as e:
        rr(f"Error during execution: {e}")

def main():
    """Main entry point with proper async handling."""

    asyncio.run(main_async())

if __name__ == "__main__":
    main()

