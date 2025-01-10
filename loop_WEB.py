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
import jsonify
import pyautogui
# from rich import print as rr
from icecream import install
from rich.prompt import Prompt
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
)
global output_buffer

import time
import ftfy
import json
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential_jitter
from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult, GetExpertOpinionTool, WebNavigatorTool, ProjectSetupTool#,  GoogleSearchTool # windows_navigate
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
# from rich import print as rr
from rich.panel import Panel
from rich.console import Group
from rich.table import Table
from rich.text import Text
import json
from flask import Flask, Response, request, render_template, jsonify
import threading
from dotenv import load_dotenv
load_dotenv()
install()
# get the current working directory
CWD = Path.cwd()
MAX_SUMMARY_MESSAGES = 9
MAX_SUMMARY_TOKENS = 8000
ICECREAM_OUTPUT_FILE =  CWD / "debug_log.json"

    
MESSAGES_FILE = CWD / "messages2.json"
# --- BETA FLAGS ---
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

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
            if isinstance(msg['content'], list):
                for content_block in msg['content']:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "tool_result":
                            output_pieces.append(
                                f"\nTool Result [ID: {content_block.get('name', 'unknown')}]:"
                            )
                            for item in content_block.get("content", []):
                                if item.get("type") == "text":
                                    output_pieces.append(f"\nText: {item.get('text')}")
                                elif item.get("type") == "image":
                                    output_pieces.append("\nImage Source: base64 source too big")
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
            role = msg['role'].lower()
            
            # Determine the message class based on role
            if role == 'user':
                message_class = 'user-message'
                header_html = '<strong class="green">User:</strong><br>'
            elif role == 'assistant':
                message_class = 'assistant-message'
                header_html = '<strong class="blue">Assistant:</strong><br>'
            else:
                message_class = 'unknown-role'
                header_html = f'<strong>{role.upper()}:</strong><br>'
            
            # Start message div
            output_pieces.append(f'<div class="{message_class}">')
            output_pieces.append(header_html)
            
            # Handle content
            content = msg.get('content', '')
            if isinstance(content, list):
                for content_block in content:
                    if isinstance(content_block, dict):
                        block_type = content_block.get("type")
                        
                        if block_type == "tool_result":
                            tool_id = content_block.get('name', 'unknown')
                            output_pieces.append(f'<div class="tool-use"><strong>Tool Result [ID: {tool_id}]:</strong></div>')
                            
                            for item in content_block.get("content", []):
                                item_type = item.get("type")
                                if item_type == "text":
                                    text = item.get("text", "")
                                    output_pieces.append(f'<div class="tool-output green">Text: {text}</div>')
                                elif item_type == "image":
                                    # If you have base64 image data, you can embed it directly
                                    # For now, as per your original code:
                                    output_pieces.append('<div class="tool-output"><em>Image Source: base64 source too big</em></div>')
                        elif block_type == "tool_use":
                            tool_name = content_block.get('name', 'unknown')
                            output_pieces.append(f'<div class="tool-use"><strong>Using tool: {tool_name}</strong></div>')
                            
                            inputs = content_block.get('input', {})
                            if isinstance(inputs, dict):
                                output_pieces.append('<div class="tool-input">')
                                for key, value in inputs.items():
                                    # Truncate long inputs if necessary
                                    display_value = (value[:88100] + '...') if isinstance(value, str) and len(value) > 99100 else value
                                    output_pieces.append(f'<div>{key}: {display_value}</div>')
                                output_pieces.append('</div>')
                        else:
                            # For other types of content blocks
                            for key, value in content_block.items():
                                output_pieces.append(f'<div class="{key}">{key}: {value}</div>')
                    else:
                        # If content_block is not a dict
                        output_pieces.append(f'<div>{content_block}</div>')
            else:
                # If content is a simple string
                output_pieces.append(f'<div>{content}</div>')
            
            # Separator for readability
            output_pieces.append('<hr>')
            # Close message div
            output_pieces.append('</div>')
        
        # Join all HTML pieces into a single string
        return ''.join(output_pieces)
    
    except Exception as e:
        # Return the error as an HTML-formatted string
        return f"<div class='error red'>Error during formatting: {str(e)}</div>"

# --- LOAD SYSTEM PROMPT ---
with open(Path(r"C:\mygit\compuse\computer_use_demo\system_prompt.md"), 'r', encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

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

    def format_recent_conversation(self, messages: List[BetaMessageParam], num_recent: int = 1) -> str:
        """Format and print the most recent conversation exchanges."""
        # Dictionary to map Rich markup to HTML
        markup_to_html = {
            '[bold yellow]': '<strong style="color: yellow;">',
            '[/bold yellow]': '</strong>',
            '[bold green]': '<strong style="color: green;">',
            '[/bold green]': '</strong>',
            '[bold blue]': '<strong style="color: blue;">',
            '[/bold blue]': '</strong>',
            '[green]': '<span style="color: green;">',
            '[/green]': '</span>',
            '[cyan]': '<span style="color: cyan;">',
            '[/cyan]': '</span>',
            '[dim]': '<span style="opacity: 0.7;">',
            '[/dim]': '</span>',
            '[red]': '<span style="color: red;">',
            '[/red]': '</span>'
        }

        output_parts = []
        
        # Add conversation header
        header = "Recent Conversation 💭"
        output_parts.append(f'<div class="conversation-header"><strong style="color: yellow;">{header}</strong></div>')

        # Get the most recent messages
        recent_messages = messages[-num_recent*2:] if len(messages) > num_recent*2 else messages

        for msg in recent_messages:
            if msg['role'] == 'user':
                # Format user message
                user_header = '<strong style="color: green;">User</strong> 👤'
                output_parts.append(f'<div class="user-message">{user_header}')
                
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "tool_result":
                                output_parts.append('<span style="color: green;">Tool Result:</span>')
                                for item in content_block.get("content", []):
                                    if item.get("type") == "text":
                                        output_parts.append(f'<div class="tool-output">{self._truncate_text(item.get("text", ""))}</div>')
                                    elif item.get("type") == "image":
                                        output_parts.append('<span style="opacity: 0.7;">📸 (Screenshot captured)</span>')
                else:
                    if isinstance(content, str):
                        output_parts.append(f'<div class="user-content">{self._truncate_text(content)}</div>')
                output_parts.append('</div>')

            elif msg['role'] == 'assistant':
                # Format assistant message
                assistant_header = '<strong style="color: blue;">Assistant</strong> 🤖'
                output_parts.append(f'<div class="assistant-message">{assistant_header}')
                
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "text":
                                output_parts.append(f'<div class="assistant-text">{self._truncate_text(content_block.get("text", ""))}</div>')
                            elif content_block.get("type") == "tool_use":
                                tool_header = f'<span style="color: cyan;">Using tool:</span> {content_block.get("name")}'
                                output_parts.append(f'<div class="tool-use">{tool_header}')
                                
                                if 'input' in content_block and isinstance(content_block['input'], dict):
                                    output_parts.append('<div class="tool-input">')
                                    for key, value in content_block['input'].items():
                                        if isinstance(value, str) and len(value) > self.max_output_length:
                                            value = self._truncate_text(value)
                                        output_parts.append(f'<div>{key}: {value}</div>')
                                    output_parts.append('</div>')
                elif isinstance(content, str):
                    output_parts.append(f'<div class="assistant-content">{self._truncate_text(content)}</div>')
                output_parts.append('</div>')

        # Join all parts with newlines and return
        return '\n'.join(output_parts)

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
        try:
            # Construct HTML for Recent Token Usage
            recent_html = f'''
            <div class="token-section">
                <h3 class="yellow">Recent Token Usage 📊</h3>
                <p><strong class="yellow">Recent Cache Creation Tokens:</strong> {self.recent_cache_creation:,}</p>
                <p><strong class="yellow">Recent Cache Retrieval Tokens:</strong> {self.recent_cache_retrieval:,}</p>
                <p><strong class="yellow">Recent Input Tokens:</strong> {self.recent_input:,}</p>
                <p><strong class="yellow">Recent Output Tokens:</strong> {self.recent_output:,}</p>
                <p><strong class="yellow">Recent Tokens Used:</strong> {self.recent_cache_creation + self.recent_cache_retrieval + self.recent_input + self.recent_output:,}</p>
            </div>
            '''

            # Construct HTML for Total Token Usage
            total_html = f'''
            <div class="token-section">
                <h3 class="yellow">Total Token Usage 📈</h3>
                <p><strong class="yellow">Total Cache Creation Tokens:</strong> {self.total_cache_creation:,}</p>
                <p><strong class="yellow">Total Cache Retrieval Tokens:</strong> {self.total_cache_retrieval:,}</p>
                <p><strong class="yellow">Total Input Tokens:</strong> {self.total_input:,}</p>
                <p><strong class="yellow">Total Output Tokens:</strong> {self.total_output:,}</p>
                <p><strong class="yellow">Total Tokens Used:</strong> {self.total_cache_creation + self.total_cache_retrieval + self.total_input + self.total_output:,}</p>
            </div>
            '''

            # Combine both sections
            combined_html = recent_html + total_html

            # Remove internal line breaks to prevent SSE issues
            combined_html = combined_html.replace('\n', ' ').replace('\r', ' ')

            # Send the combined HTML to the output buffer
            write_to_buffer(combined_html)

        except Exception as e:
            error_message = html.escape(f"Error during token tracker display: {str(e)}")
            write_to_buffer(f"<div class='error red'>{error_message}</div>")
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

def format_message_to_html(msg: BetaMessageParam) -> str:
    """
    Format a single message into an HTML-formatted string.

    Args:
        msg (BetaMessageParam): A message dictionary containing 'role' and 'content'

    Returns:
        str: HTML-formatted string for the message
    """
    try:
        role = msg['role'].lower()

        # Determine the message class and header based on role
        if role == 'user':
            message_class = 'user-message'
            header_html = '<strong class="green">User:</strong><br>'
        elif role == 'assistant':
            message_class = 'assistant-message'
            header_html = '<strong class="blue">Assistant:</strong><br>'
        else:
            message_class = 'unknown-role'
            header_html = f'<strong>{html.escape(role.upper())}:</strong><br>'

        # Start the message div
        html_parts = [f'<div class="{message_class}">', header_html]

        content = msg.get('content', '')
        if isinstance(content, list):
            for content_block in content:
                if isinstance(content_block, dict):
                    block_type = content_block.get("type")

                    if block_type == "tool_result":
                        tool_id = html.escape(content_block.get('name', 'unknown'))
                        html_parts.append(f'<div class="tool-use"><strong>Tool Result [ID: {tool_id}]:</strong></div>')

                        for item in content_block.get("content", []):
                            item_type = item.get("type")
                            if item_type == "text":
                                text = html.escape(item.get("text", "")).replace('\n', ' ')
                                html_parts.append(f'<div class="tool-output green">Text: {text}</div>')
                            elif item_type == "image":
                                # Placeholder for image rendering
                                html_parts.append('<div class="tool-output"><em>Image Source: base64 source too big</em></div>')

                    elif block_type == "tool_use":
                        tool_name = html.escape(content_block.get('name', 'unknown'))
                        html_parts.append(f'<div class="tool-use"><strong>Using tool: {tool_name}</strong></div>')

                        inputs = content_block.get('input', {})
                        if isinstance(inputs, dict):
                            html_parts.append('<div class="tool-input">')
                            for key, value in inputs.items():
                                # Truncate long inputs if necessary
                                if isinstance(value, str) and len(value) > 100:
                                    value = html.escape(value[:100] + '...')
                                else:
                                    value = html.escape(str(value))
                                html_parts.append(f'<div>{key}: {value}</div>')
                            html_parts.append('</div>')

                    else:
                        for key, value in content_block.items():
                            key_escaped = html.escape(str(key))
                            value_escaped = html.escape(str(value)).replace('\n', ' ')
                            html_parts.append(f'<div class="{key_escaped}">{key_escaped}: {value_escaped}</div>')
                else:
                    # If content_block is not a dict
                    content_escaped = html.escape(str(content_block)).replace('\n', ' ')
                    html_parts.append(f'<div>{content_escaped}</div>')
        else:
            if isinstance(content, str):
                content_escaped = html.escape(content).replace('\n', ' ')
                html_parts.append(f'<div>{content_escaped}</div>')

        # Add a separator
        html_parts.append('<hr>')  # Separates messages visually
        html_parts.append('</div>')  # Closes the message div

        # Combine all parts into a single HTML string
        html_content = ''.join(html_parts)
        return html_content

    except Exception as e:
        # Return the error as an HTML-formatted string
        error_message = html.escape(f"Error during formatting: {str(e)}")
        return f"<div class='error red'>{error_message}</div>"
        
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
            ProjectSetupTool()
        )
        system = [BetaTextBlockParam(type="text", text=SYSTEM_PROMPT)]
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

        ic(messages)    
        enable_prompt_caching = True

        previous_message_count = 0  # Initialize the counter

        while running:
            print(i)
            write_to_buffer(f"<div class='iteration'><strong class='yellow'>Iteration {i}</strong> 🔄</div>")
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
                # token_tracker.display()  # Display token usage

                ic(f"Response: {response}")
                response_params = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_params.append({"type": "text", "text": block.text})
                    elif getattr(block, 'type', None) == "tool_use":
                        response_params.append({
                            "type": "tool_use",
                            "name": block.name,
                            "id": block.id,
                            "input": block.input
                        })
                messages.append({"role": "assistant", "content": response_params})

                write_messages_to_file(messages, MESSAGES_FILE)

                # Get new messages since the last iteration
                new_messages = messages[previous_message_count:]
                
                # Format and send each new message individually
                for new_msg in new_messages:
                    conversation_html = format_message_to_html(new_msg)
                    write_to_buffer(conversation_html)

                # Update previous message count
                previous_message_count = len(messages)

                print(conversation_html)
                tool_result_content: List[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    if content_block["type"] == "tool_use":
                        ic(f"Tool Use: {response_params}")
                        result = await tool_collection.run(
                            name=content_block["name"],
                            tool_input=content_block["input"],
                        )
                        ic.configureOutput(includeContext=True, outputFunction=write_to_file, argToStringFunction=repr)
                        ic(content_block)
                        tool_result = _make_api_tool_result(result, content_block["id"])
                        ic(tool_result)
                        tool_result_content.append(tool_result)
                
                if not tool_result_content and len(messages) > 4:
                    write_to_buffer("<div class='awaiting-input'><strong class='yellow'>Awaiting User Input</strong> ⌨️</div>")
                    task = Prompt.ask("What would you like to do next? Enter 'no' to exit")
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                else:
                    messages.append({"role": "user", "content": tool_result_content})

            except UnicodeEncodeError as ue:
                ic(f"UnicodeEncodeError: {ue}")
                write_to_buffer(f"<div class='error red'>Unicode encoding error: {ue}</div>")
                write_to_buffer(f"<div class='error red'>ascii: {ue.args[1].encode('ascii', errors='replace').decode('ascii')}</div>")
                break
            except Exception as e:
                ic(f"Error in sampling loop: {str(e).encode('ascii', errors='replace').decode('ascii')}")
                ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
                ic(e.__traceback__.tb_frame.f_locals)
                raise
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
    for msg in messages:
        ic(msg)
    ic(len(messages))
    for message in reversed(messages):
        ic(message)
        if message["role"] == "user" and isinstance(content := message["content"], list):
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



async def run_sampling_loop(task: str) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    # ic.configureOutput(outputFunction=write_to_buffer)  # Add this line to redirect icecream output
    # rr.print = write_to_buffer  # Existing line to redirect rich.print output
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    messages.append({"role": "user","content": task})
    messages = await sampling_loop(
            model="claude-3-5-sonnet-latest",
        messages=messages,
        api_key=api_key,
    )
    return messages


async def main_async():

    """Async main function with proper error handling."""
    # Get list of available prompts
    rr = write_to_buffer
    current_working_dir = Path(os.getcwd())
    prompts_dir = current_working_dir / "prompts"
    # rr(prompts_dir)
    prompt_files = list(prompts_dir.glob("*.md"))
    
    # Display options
    # rr("\n[bold yellow]Available Prompts:[/bold yellow]")
    # for i, file in enumerate(prompt_files, 1):
    #     rr(f"{i}. {file.name}")
    # rr(f"{len(prompt_files) + 1}. Create new prompt")
    
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
        # rr(f"New prompt saved to {new_prompt_path}")
    else:
        # Read existing prompt
        prompt_path = prompt_files[int(choice) - 1]
        with open(prompt_path, 'r', encoding='utf-8') as f:
            task = f.read()
        # rr(f"Selected prompt: {prompt_path}")
    try:
        messages = await run_sampling_loop(task)


    except Exception as e:
        print(f"Error during execution: {e}")
# 
def main():
    """Main entry point with proper async handling."""

    asyncio.run(main_async())

app = Flask(__name__, template_folder='./templates')

# Global variables for output management
output_buffer = []
output_lock = threading.Lock()

def write_to_buffer(html_content: str):
    """Write HTML content to buffer for streaming to the frontend."""
    with output_lock:
        # Append the HTML content directly to the buffer
        output_buffer.append(html_content)

def flush_buffer():
    """Get and clear the buffer."""
    with output_lock:
        if not output_buffer:
            return None
        messages = output_buffer.copy()
        output_buffer.clear()
        return messages

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            messages = flush_buffer()
            if messages:
                for msg in messages:
                    if msg.strip():  # Only send non-empty messages
                        yield f"data: {msg}\n\n"
            time.sleep(0.1)  # Adjust delay as needed
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        task = request.form.get('task')
        if task:
            # Run the sampling loop in a separate thread
            threading.Thread(target=lambda: asyncio.run(run_sampling_loop(task))).start()
    return render_template('index.html')

@app.route('/task', methods=['POST'])
def handle_task():
    task = request.json.get('task')
    if task:
        thread = threading.Thread(
            target=lambda: asyncio.run(run_sampling_loop(task))
        )
        thread.start()
        return jsonify({"status": "success", "message": "Task started"})
    return jsonify({"status": "error", "message": "No task provided"}), 400

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)