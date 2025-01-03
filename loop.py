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
from dotenv import load_dotenv
load_dotenv()
install()
# get the current working directory
CWD = Path("C:/mygit/compuse/")
# append ICECREAM_OUTPUT_FILE to the end of ICECREAM_OUTPUT_FILE.archive and clear the file
if (CWD / ICECREAM_OUTPUT_FILE).exists():
    with open(CWD / ICECREAM_OUTPUT_FILE, 'r', encoding="utf-8") as f:
        lines = f.readlines()
    archive_file = CWD / (ICECREAM_OUTPUT_FILE.with_suffix('.archive.json'))   
    with open(archive_file, 'a', encoding="utf-8") as f:
        for line in lines:
            f.write(line)
    with open(CWD / ICECREAM_OUTPUT_FILE, 'w', encoding="utf-8") as f:
        f.write('')

# Archive journal log if it exists
if (CWD / JOURNAL_FILE).exists():
    # Create journal directory if it doesn't exist
    try:
        with open(CWD / JOURNAL_FILE, 'r', encoding='utf-8') as f:
            journal_lines = f.readlines()
        with open(CWD / JOURNAL_ARCHIVE_FILE, 'a', encoding='utf-8') as f:
            f.write('\n' + '='*50 + '\n')
            f.write(f'Archive from {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('='*50 + '\n')
            for line in journal_lines:
                f.write(line)
        # Clear the current journal file
        with open(CWD / JOURNAL_FILE, 'w', encoding='utf-8') as f:
            f.write('')
    except Exception as e:
        ic(f"Error archiving journal: {str(e)}")
else:
    (CWD / JOURNAL_FILE).mkdir(parents=True, exist_ok=True)

def write_to_file(s, file_path=ICECREAM_OUTPUT_FILE):
    """
    Write debug output to a file, formatting JSON content in a pretty way.
    """
    #CWD = Path.cwd()
    try:
        lines = s.split('\n')
        formatted_lines = []
        
        for line in lines:
            if "tool_input:" in line:
                try:
                    # Extract JSON part from the line
                    json_part = line.split("tool_input: ")[1]
                    # Parse and pretty-print the JSON
                    json_obj = json.loads(json_part)
                    pretty_json = json.dumps(json_obj, indent=4)
                    formatted_lines.append("tool_input: " + pretty_json)
                except (IndexError, json.JSONDecodeError):
                    # If parsing fails, just append the original line
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        # Write to file with explicit UTF-8 encoding and error handling
        with open(CWD / file_path, 'a', encoding="utf-8", errors='replace') as f:
            f.write('\n'.join(formatted_lines))
            f.write('\n' + '-' * 80 + '\n')  # Add separator between entries
    except UnicodeEncodeError as ue:
        # Fallback handling for Unicode encode errors
        with open(CWD / file_path, 'a', encoding="utf-8", errors='replace') as f:
            f.write(f"Warning: Some characters could not be encoded: {str(ue)}\n")
            f.write('\n'.join(line.encode('ascii', errors='replace').decode('ascii') for line in formatted_lines))
            f.write('\n' + '-' * 80 + '\n')
    except Exception as e:
        ic(f"Error writing to file: {str(e)}")
ic.configureOutput(includeContext=True, outputFunction=write_to_file)

class OutputManager:
    """Manages and formats tool outputs and responses."""
    def __init__(self, image_dir: Optional[Path] = None ):
        #CWD = Path.cwd()
        # Set up image directory
        self.image_dir = image_dir
        (CWD / self.image_dir).mkdir(parents=True, exist_ok=True)
        self.image_counter = 0

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
            ic(f"Error saving image: {e}")
            return None

    def format_tool_output(self, result: ToolResult, tool_name: str) -> None:
        """Format and print tool output without base64 data."""
        rr("\n[bold blue]Tool Execution[/bold blue] 🛠️")
        rr(f"[blue]Tool Name:[/blue] {tool_name}")

        if isinstance(result, str):
            rr(f"[red]Error:[/red] {result}")
        else:
            if result.output:
                # Safely truncate long output
                output_text = result.output
                if len(output_text) > 500:
                    output_text = output_text[:200] + "/n.../n" + output_text[-200:]
                rr(f"[green]Output:[/green] {output_text}")
            
            if result.base64_image:
                image_path = self.save_image(result.base64_image)
                if image_path:
                    rr(f"[green]📸 Screenshot saved to {image_path}[/green]")
                else:
                    rr("[red]Failed to save screenshot[/red]")

    def format_api_response(self, response: APIResponse) -> None:
        """Format and print API response."""
        rr("\n[bold purple]Assistant Response[/bold purple] 🤖")
        if hasattr(response.content[0], 'text'):
            text = response.content[0].text
            if len(text) > 500:
                text = text[:300] + "..." + text[-300:]
            rr(f"[purple]{text}[/purple]")

    def format_content_block(self, block: BetaContentBlock) -> None:
        """Format and print content block."""
        if getattr(block, 'type', None) == "tool_use":
            ic(f"\nTool Use: {block.name}")
            # Only print non-image related inputs
            safe_input = {k: v for k, v in block.input.items()
                         if not isinstance(v, str) or len(v) < 1000}
            ic(f"Input: {safe_input}")
        elif hasattr(block, 'text'):
            ic(f"\nText: {block.text}")

    def format_recent_conversation(self, messages: List[BetaMessageParam], num_recent: int = 2) -> None:
        """Format and print the most recent conversation exchanges."""
        rr("\n[bold yellow]Recent Conversation[/bold yellow] 💭")
        
        # Get the most recent messages
        recent_messages = messages[-num_recent*2:] if len(messages) > num_recent*2 else messages
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                rr("\n[bold green]User[/bold green] 👤")
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "tool_result":
                                rr(f"[green]Tool Result:[/green]")
                                for item in content_block.get("content", []):
                                    if item.get("type") == "text":
                                        text = item.get("text", "")
                                        if len(text) > 500:
                                            text = text[:200] + "/n.../n" + text[-200:]
                                        rr(f"{text}")
                                    elif item.get("type") == "image":
                                        rr("[dim]📸 (Screenshot captured)[/dim]")
                else:
                    if isinstance(content, str):
                        if len(content) > 500:
                            content = content[:300] + "..." + content[-300:]
                        rr(f"{content}")
            
            elif msg['role'] == 'assistant':
                rr("\n[bold blue]Assistant[/bold blue] 🤖")
                content = msg['content']
                if isinstance(content, list):
                    for content_block in content:
                        if isinstance(content_block, dict):
                            if content_block.get("type") == "text":
                                text = content_block.get("text", "")
                                if len(text) > 500:
                                    text = text[:400] + "..." + text[-400:]
                                rr(f"[blue]{text}[/blue]")
                            elif content_block.get("type") == "tool_use":
                                rr(f"[cyan]Using tool:[/cyan] {content_block.get('name')}")
                                for k, v in content_block.get('input', {}).items():
                                    rr(f"[cyan]{k}:[/cyan] {v}")
                                tool_input = content_block.get('input', "")
                                # if isinstance(tool_input, str) and len(tool_input) > 500:
                                    # tool_input = tool_input[:200] + "/n.../" + tool_input[-200:]
                                # rr(f"[cyan]With input:[/cyan] {tool_input}")
                                if isinstance(tool_input, str):
                                    # try to load as json
                                    try:
                                        tool_input = json.loads(tool_input)
                                        rr(f"[cyan]With input:[/cyan]")
                                        for key, value in tool_input.items():
                                            if isinstance(value, str) and len(value) > 500:
                                                rr(f"[cyan]{key}:[/cyan] {value[:200] + '/n.../n'  + value[-200:]}")
                                            else:
                                                rr(f"[cyan]{key}:[/cyan] {value}")  
                                    except json.JSONDecodeError:
                                        if isinstance(tool_input, str):
                                            tool_input = tool_input[:200] + "/n.../" + tool_input[-200:]
                                        rr(f"[cyan]With input:[/cyan] {tool_input}")
                                        

                elif isinstance(content, str):
            
                    if len(content) > 500:
                        content = content[:200] + "/n.../n" + content[-200:]
                    rr(f"[blue]{content}[/blue]")

        rr("\n" + "="*50 + "\n")

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

class TokenTracker:
    """Tracks total token usage across all iterations."""
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
        """Display total token usage."""
        rr("\n[bold yellow]Recent Token Usage[/bold yellow] 📊")
        rr(f"[yellow]Recent Cache Creation Tokens:[/yellow] {self.recent_cache_creation:,}")
        rr(f"[yellow]Recent Cache Retrieval Tokens:[/yellow] {self.recent_cache_retrieval:,}")
        rr(f"[yellow]Recent Input Tokens:[/yellow] {self.recent_input:,}")
        rr(f"[yellow]Recent Output Tokens:[/yellow] {self.recent_output:,}")
        rr(f"[bold yellow]Recent Tokens Used:[/bold yellow] {self.recent_cache_creation + self.recent_cache_retrieval + self.recent_input + self.recent_output:,}")
        rr("\n[bold yellow]Total Token Usage[/bold yellow] 📈")
        rr(f"[yellow]Total Cache Creation Tokens:[/yellow] {self.total_cache_creation:,}")
        rr(f"[yellow]Total Cache Retrieval Tokens:[/yellow] {self.total_cache_retrieval:,}")
        rr(f"[yellow]Total Input Tokens:[/yellow] {self.total_input:,}")
        rr(f"[yellow]Total Output Tokens:[/yellow] {self.total_output:,}")
        rr(f"[bold yellow]Total Tokens Used:[/bold yellow] {self.total_cache_creation + self.total_cache_retrieval + self.total_input + self.total_output:,}")

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

# Add after JOURNAL_SYSTEM_PROMPT definition
def get_journal_contents() -> str:
    """Read and return the contents of the journal file."""
    #CWD = Path.cwd()
    try:
        with open(CWD / JOURNAL_FILE, 'r', encoding='utf-8') as f:
            file_contents =  f.read()

        return file_contents
    except FileNotFoundError:
        return "No journal entries yet."

# Add after imports
def truncate_message_content(content: Any, max_length: int = 450000) -> Any:
    """Truncate message content while preserving structure."""
    if isinstance(content, str):
        return content[:max_length]
    elif isinstance(content, list):
        return [truncate_message_content(item, max_length) for item in content]
    elif isinstance(content, dict):
        return {k: truncate_message_content(v, max_length) if k != 'source' else v 
                for k, v in content.items()}
    return content

# In the sampling_loop function, before calling client.beta.messages.create:
# @retry(stop=stop_after_attempt(3), wait=wait_fixed(30))
async def call_llm_with_retry(client, messages, max_tokens, model, system, tools, betas):

    try:
        return_value = client.beta.messages.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            system=system,
            tools=tools,
            betas=betas,
    )
        ic(return_value)
        return return_value
    except Exception as e:
        ic(f"Error calling LLM: {str(e)}")
        raise
async def sampling_loop(*, model: str, messages: List[BetaMessageParam], api_key: str, max_tokens: int = 6000,) -> List[BetaMessageParam]:
    #CWD = Path.cwd()
    ic(messages)
    try:
        # Initialize tools with proper error handling
        tool_collection = ToolCollection(
            BashTool(),
            EditTool(),
            GetExpertOpinionTool(),
            ComputerTool(),
            WebNavigatorTool(),
            # GoogleSearchTool(),
            # windows_navigate()
        )
        ic(tool_collection)            
        
        system = BetaTextBlockParam(
            type="text",
            text=SYSTEM_PROMPT,  
        )
        
        output_manager = OutputManager(image_dir=CWD / 'logs/computer_tool_images')
        client = Anthropic(api_key=api_key)
        i = 0
        running = True
        token_tracker = TokenTracker()
        
        # Add journal entry counter
        journal_entry_count = 1
        if (CWD / JOURNAL_FILE).exists():
            with open(CWD / JOURNAL_FILE, 'r',encoding='utf-8') as f:
                journal_entry_count = sum(1 for line in f if line.startswith("Entry #")) + 1
        else:
            journal_entry_count = 1

        # Add journal contents to messages
        messages.append({
            "role": "user",
            "content": f"Previous conversation history from journal:\n{get_journal_contents()}"
        })

        while running:
            # reload_prompts()
            rr(f"\n[bold yellow]Iteration {i}[/bold yellow] 🔄")
            enable_prompt_caching = True
            betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
            image_truncation_threshold = 1
            only_n_most_recent_images = 2
            i+=1
            if i > 20:
                running = False
            if enable_prompt_caching:
                _inject_prompt_caching(messages)
                # Is it ever worth it to bust the cache with prompt caching?
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
                # Truncate messages before sending to API
                truncated_messages = [
                    {
                        "role": msg["role"],
                        "content": truncate_message_content(msg["content"])

                    } 
                    for msg in messages
                ]
                with open(CWD / "messages.json", "w") as f:
                    for msg in truncated_messages:  
                        for_looking_at_messages_as_json = json.dumps(msg, indent=4)
                        f.write(for_looking_at_messages_as_json)
                        f.write("\n\n")
 
                # Update token tracker
                token_tracker.update(response)
                token_tracker.display() 

                # Convert response content to params format
                response_params = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        output_manager.format_api_response(response)
                        response_params.append({
                            "type": "text",
                            "text": block.text
                        })
                    elif getattr(block, 'type', None) == "tool_use":
                        response_params.append({
                            "type": "tool_use",
                            "name": block.name,
                            "id": block.id,
                            "input": block.input
                        })
                # Append assistant message with full response content
                messages.append({
                    "role": "assistant",
                    "content": response_params
                })
                # Format the recent conversation after each response
                output_manager.format_recent_conversation(messages)
                
                # Process tool uses and collect results
                tool_result_content: list[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    output_manager.format_content_block(content_block)
                    if content_block["type"] == "tool_use":
                        ic(f"Tool Use: {response_params}")
                        result = await tool_collection.run(
                            name=content_block["name"],
                            tool_input=content_block["input"],
                        )
                        ic.configureOutput(includeContext=True, outputFunction=write_to_file,argToStringFunction=repr)
                        ic(content_block)
                        output_manager.format_tool_output(result, content_block["name"])
                        tool_result = _make_api_tool_result(result, content_block["id"])
                        ic(tool_result)
                        tool_result_content.append(tool_result)
                # If no tool results, we're done



                
                if not tool_result_content or i % 5 == 0:
                    rr("\n[bold yellow]Awaiting User Input[/bold yellow] ⌨️")
                    task = Prompt.ask("What would you like to do next? Enter 'no' to exit")
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                else:
                    # Append tool results as user message
                    messages.append({
                        "role": "user",
                        "content": tool_result_content
                    })
                rr(f"Creating journal entry #{journal_entry_count}")
                # After processing the response and before the next iteration, add journal entry
                rr(f"There are {len(messages)} messages")
                # Check if messages need summarization
                if len(messages) > MAX_SUMMARY_MESSAGES:
                    rr(f"\n[yellow]Messages exceed {MAX_SUMMARY_MESSAGES} - generating summary...[/yellow]")
                    messages = await summarize_messages(messages)
                    with open(CWD / "messages.json", "w") as f:
                        for msg in messages:  
                            for_looking_at_messages_as_json = json.dumps(msg, indent=4)
                            f.write(for_looking_at_messages_as_json)
                            f.write("\n\n")
                    rr(f"[green]Summary generated - conversation compressed down to {len(messages)} messages[/green]")
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
                # Handle or skip the problematic message
                break        
            except Exception as e:
                ic(f"Error in sampling loop: {str(e).encode('ascii', errors='replace').decode('ascii')}")
                ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
                ic(e.__traceback__.tb_frame.f_locals)
                raise
            messages[1] = {
            "role": "user",
            "content": f"Here are notes of your progress from your journal:\n{get_journal_contents()}"
            }
             # Display total token usage before returning
            token_tracker.display()
        return messages

    except Exception as e:
        ic(e.__traceback__.tb_lineno)
        ic(e.__traceback__.tb_lasti)
        ic(e.__traceback__.tb_frame.f_code.co_filename)
        ic(e.__traceback__.tb_frame)
        ic(f"Error initializing sampling loop: {str(e)}")
        raise  # Re-raise the exception after logging it

def _inject_prompt_caching(
    messages: list[BetaMessageParam],
    ):
    breakpoints_remaining = 2
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
                # rr(f"Removing cache control from message: {content[-1]}")
                content[-1].pop("cache_control", None)
                # we'll only every have one extra turn per loop
                break

def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
    ):
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[BetaToolResultBlockParam],
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
    # for better cache behavior, we want to remove in chunks
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

async def summarize_messages(messages: List[BetaMessageParam]) -> List[BetaMessageParam]:   
    #CWD = Path.cwd()
    if len(messages) <= MAX_SUMMARY_MESSAGES:
        return messages
        
    original_prompt = messages[0]["content"]
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Anthropic API key not found in environment variables.")
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Get current journal contents
    current_journal = {
        "role": "user",
        "content": f"Here are notes of your progress from your journal:\n{get_journal_contents()}"
    }
    
    # Get the last 5 messages before summarization, excluding journal and summary messages
    last_five = []
    count = 0
    for msg in reversed(messages):
        if count >= 5:
            break
            
        # Extract only text content from complex messages
        if isinstance(msg.get('content'), list):
            text_blocks = []
            for block in msg['content']:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_blocks.append(block.get('text', ''))
            
            if text_blocks:  # Only add if we found text blocks
                last_five.insert(0, {
                    "role": msg['role'],
                    "content": text_blocks[0] if len(text_blocks) == 1 else "\n".join(text_blocks)
                })
                count += 1
        elif isinstance(msg.get('content'), str):
            if not (msg['content'].startswith("Here are notes of your progress from your journal:") or
                   "[CONVERSATION SUMMARY]" in msg['content']):
                last_five.insert(0, msg)
                count += 1

    # Build conversation to summarize
    messages_to_summarize = messages
    
    # Convert messages to a readable format for summarization
    conversation_text = ""
    for msg in messages_to_summarize:
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
    rr(f"Conversation to summarize: {conversation_text}")
    # write the conversation to a file
    with open(CWD / "summaries/conversation.md", "w", encoding="utf-8") as f:
        f.write(conversation_text)
    # Format the prompt
    formatted_prompt = f"""Please provide a detailed technical summary of this conversation. Include:
1. All file names and paths mentioned
2. Directory structures created or modified
3. Specific actions taken and their outcomes
4. Any technical decisions or solutions implemented
5. Current status of the task
6. Any pending or incomplete items
7. Provide the actual Lyrics or Source Code if any.
8. Someone reading the summary should have a detailed understanding of everything in the original, only omitting repetitive text while organizing the information to be more easily understandable.

Original task prompt for context:
{original_prompt}

Conversation to summarize:
{conversation_text}
"""
    
    # Save the formatted prompt
    os.makedirs(CWD / "summaries", exist_ok=True)
    with open(CWD / "summaries/summary.md", "w", encoding="utf-8") as f:
        f.write(formatted_prompt)
    
    try:
        response = client.messages.create(
                model=SUMMARY_MODEL,
                max_tokens=MAX_SUMMARY_TOKENS,
                messages=[{
                    "role": "user",
                    "content": f"Please provide a detailed technical summary following these requirements exactly:\n\n{formatted_prompt}\n\nIMPORTANT: Your summary must be comprehensive and detailed, covering all aspects mentioned in the requirements. Do not provide a brief or partial summary."
                }],
            )
    except asyncio.TimeoutError:
        ic("Summary generation timed out")
        return messages
    except Exception as e:
        ic(f"Error generating summary: {str(e)}")
        return messages
    
    summary = response.content[0].text
    
    # Write the summary
    with open(CWD / "summaries/summary.md", "w", encoding="utf-8") as f:
        f.write(summary)
        
    rr(f"Last 5 messages before summarization: {last_five}")
    ic(summary)
    
    # Create new messages list with only text content
    new_messages = [
        messages[0],  # Original Prompt
        current_journal,  # Current journal entry
        {
            "role": "assistant",
            "content": f"[CONVERSATION SUMMARY]\n\n{summary}"
        }
    ] + last_five  # Last 5 text-only messages

    rr(f"Number of messages after summarization: {len(new_messages)}")
    return new_messages

async def run_sampling_loop(task: str) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    ic(messages)
    running = True
    if not api_key:
        raise ValueError("API key not found. Please set the CLAUDE_API_KEY environment variable.")
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
    prompts_dir = current_working_dir / Path(r"prompts")
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
        ic()
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
        ic()
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

