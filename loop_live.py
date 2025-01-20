import asyncio
import base64
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from re import U
from typing import Any, Callable, Dict, List, Optional, cast
from config import *
write_constants_to_file()

import ftfy
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
from rich.prompt import Prompt, Confirm
# from load_constants import SYSTEM_PROMPT, BASH_PROMPT_FILE
from tools import (
    BashTool,
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

ICECREAM_OUTPUT_FILE = Path.cwd() / "debug_log.json"

with open(SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()



def write_to_file(s: str, file_path: str = ICECREAM_OUTPUT_FILE):
    lines = s.split('\n')
    formatted_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    for line in lines:
        if "tool_input:" in line:
            try:
                ic(line)
                json_part = line.split("tool_input: ")[1]
                if json_part.strip().startswith('{') and json_part.strip().endswith('}'):
                    json_obj = json.loads(json_part)
                    pretty_json = json.dumps(json_obj, indent=4)
                    formatted_lines.append("tool_input: " + pretty_json)
                else:
                   formatted_lines.append(line)
            except (IndexError, json.JSONDecodeError):
                formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    with open(file_path, 'a', encoding="utf-8") as f:
        f.write('\n'.join(formatted_lines))
        f.write('\n' + '-' * 80 + '\n')
ic.configureOutput(includeContext=True, outputFunction=write_to_file)


def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> Dict:
    """Create a tool result dictionary with proper error handling."""
    tool_result_content = []
    is_error = False

    if result is None:
        is_error = True
        tool_result_content.append({
            "type": "text", 
            "text": "Tool execution resulted in None"
        })
    elif isinstance(result, str):
        is_error = True
        tool_result_content.append({
            "type": "text", 
            "text": result
        })
    elif hasattr(result, 'output') and result.output:
        tool_result_content.append({
            "type": "text", 
            "text": result.output
        })
        if hasattr(result, 'base64_image') and result.base64_image:
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
    def __init__(self, display: AgentDisplay):
        self.total_cache_creation = 0
        self.total_cache_retrieval = 0
        self.total_input = 0
        self.total_output = 0
        self.recent_cache_creation = 0
        self.recent_cache_retrieval = 0
        self.recent_input = 0
        self.recent_output = 0
        self.displayA = display

    def update(self, response):
        self.recent_cache_creation = response.usage.cache_creation_input_tokens
        self.recent_cache_retrieval = response.usage.cache_read_input_tokens
        self.recent_input = response.usage.input_tokens
        self.recent_output = response.usage.output_tokens
        
        self.total_cache_creation += self.recent_cache_creation
        self.total_cache_retrieval += self.recent_cache_retrieval
        self.total_input += self.recent_input
        self.total_output += self.recent_output

    def display(self):
        """Display token usage with Rich formatting."""
        # Format recent token usage
        recent_usage = [
            "[bold yellow]Recent Token Usage[/bold yellow] 📊",
            f"[yellow]Recent Cache Creation:[/yellow] {self.recent_cache_creation:,}",
            f"[yellow]Recent Cache Retrieval:[/yellow] {self.recent_cache_retrieval:,}",
            f"[yellow]Recent Input:[/yellow] {self.recent_input:,}",
            f"[yellow]Recent Output:[/yellow] {self.recent_output:,}",
            f"[bold yellow]Recent Total:[/bold yellow] {self.recent_cache_creation + self.recent_cache_retrieval + self.recent_input + self.recent_output:,}",
        ]

        # Format total token usage
        total_usage = [
            "[bold yellow]Total Token Usage[/bold yellow] 📈",
            f"[yellow]Total Cache Creation:[/yellow] {self.total_cache_creation:,}",
            f"[yellow]Total Cache Retrieval:[/yellow] {self.total_cache_retrieval:,}",
            f"[yellow]Total Input:[/yellow] {self.total_input:,}",
            f"[yellow]Total Output:[/yellow] {self.total_output:,}",
            f"[bold yellow]Total Tokens:[/bold yellow] {self.total_cache_creation + self.total_cache_retrieval + self.total_input + self.total_output:,}",
        ]

        # Combine the sections with proper spacing
        token_display = "\n".join(recent_usage) + "\n\n" + "\n".join(total_usage)
        
        # Send to display using system message type
        self.displayA.add_message("system", token_display)

with open(JOURNAL_SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
    JOURNAL_SYSTEM_PROMPT = f.read()


def _extract_text_from_content(content: Any) -> str:
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
    try:
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            file_contents =  f.read()
            return ftfy.fix_text(file_contents)
    except FileNotFoundError:
        return "No journal entries yet."

def truncate_message_content(content: Any, max_length: int = 20000) -> Any:
    if isinstance(content, str):
        return content[:max_length]
    elif isinstance(content, list):
        return [truncate_message_content(item, max_length) for item in content]
    elif isinstance(content, dict):
        return {k: truncate_message_content(v, max_length) if k != 'source' else v
                for k, v in content.items()}
    return content

async def sampling_loop(*, model: str, messages: List[BetaMessageParam], api_key: str, max_tokens: int = 8000, display: AgentDisplay) -> List[BetaMessageParam]:
    """Main loop for agentic sampling."""
    # ic(messages)
    try:
        tool_collection = ToolCollection(
            BashTool(display=display),
            EditTool(),
            GetExpertOpinionTool(),
            WebNavigatorTool(),
            ProjectSetupTool()
        )
        # ic(tool_collection)
        display.add_message("system", tool_collection.get_tool_names_as_string())
        system = BetaTextBlockParam(type="text", text=SYSTEM_PROMPT_FILE)
        output_manager = OutputManager(display)
        client = Anthropic(api_key=api_key)
        i = 0
        running = True
        token_tracker = TokenTracker(display)
        enable_prompt_caching = True
        betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
        image_truncation_threshold = 1
        only_n_most_recent_images = 2
        while running:
            await asyncio.sleep(0.1)  # Smal


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

                # ic(messages)

                truncated_messages = [
                    {"role": msg["role"], "content": truncate_message_content(msg["content"])}
                    for msg in messages
                ]
                await asyncio.sleep(0.2)
                # display.live.stop()  # Stop the live display
                # # Ask user if they are done reviewing the info using rich's Confirm.ask
                # while Confirm.ask("Do you need more time?", default=True):
                #     ci=0
                #     for message in messages:
                #         rr(f"Message # {ci}")
                #         ci+=1
                #         rr(message)
                # display.live.start()  # Restart the live display
                
                messages_to_display = messages[-1:] if len(messages) > 1 else messages[-1:]
                for message in messages_to_display:
                    if isinstance(message, dict):
                        if message.get("type") == "text":
                            display_output = message.get("text", "")
                            display.add_message("user", "type text")

                        elif message.get("type") == "image":
                            display_output = "Image"
                        elif message.get("type") == "tool_result":
                            display_output = message["content"][0].get("text", "")
                            display.add_message("user", "type tool result")
                        elif message.get("type") == "tool_result_image":
                            display_output = "Image"
                        elif message.get("type") == "tool_use":
                            display_output = f"Calling tool: {message.get('name', '')}"
                            display_output += f"Input: {json.dumps(message.get('input', {}))}"
                            display.add_message("user", "tool use")
                        else:
                            # display.add_message("user", "First Else")
                            if len(messages) == 1:
                                display_output = message['content']
                            else:
                                try:
                                    display_output = message['content'][0]['content'][0]['text']
                                except:
                                    try:
                                        display_output = message['content'][0]['text']
                                    except:
                                        display_output = message
                    elif isinstance(message, str):
                        display.add_message("user", "first elif")

                        display_output = message
                    else:
                        display_output = str(message)
                        display.add_message("user", "second Else")

                    
                    display.add_message("user", display_output)
                    await asyncio.sleep(delay=0.5)
                quick_summary = await summarize_recent_messages(messages[-4:], display)
                display.add_message("assistant", f"Here is a quick summary of what I did:\n {quick_summary}")
                await asyncio.sleep(0.2)
                response = client.beta.messages.create(
                    max_tokens=MAX_SUMMARY_TOKENS,
                    messages=truncated_messages,
                    model=MAIN_MODEL,
                    system=system,
                    tools=tool_collection.to_params(),
                    betas=betas,
                )
                if len(messages) < 2:
                    display.clear_messages("all")

                # display.add_message("assistant", response.content[0].text) # Update display
                # await asyncio.sleep(0.2)
                



                response_params = []
                for block in response.content:
                    if hasattr(block, 'text'):
                        # output_manager.format_api_response(response)
                        response_params.append({"type": "text", "text": block.text})
                        display.add_message("assistant", block.text) # Update display
                    elif getattr(block, 'type', None) == "tool_use":
                        response_params.append({
                            "type": "tool_use",
                            "name": block.name,
                            "id": block.id,
                            "input": block.input
                        })
                messages.append({"role": "assistant", "content": response_params})

                tool_result_content: List[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    output_manager.format_content_block(content_block)
                    if content_block["type"] == "tool_use":
                        display.add_message("tool", f"Calling tool: {content_block['name']}")
                        display.live.stop()
                        await asyncio.sleep(0.5)
                        try:
                            ic(content_block['name'])
                            ic(content_block["input"])
                            result = await tool_collection.run(
                                name=content_block["name"],
                                tool_input=content_block["input"],
                            )
                            # Ensure we have a valid result
                            if result is None:
                                result = ToolResult(output="Tool execution failed with no result")
                            
                            tool_result = _make_api_tool_result(result, content_block["id"])
                            ic(tool_result)
                            tool_result_content.append(tool_result)
                            
                            tool_output = result.output if hasattr(result, 'output') else str(result)
                            # ...existing code...
                        except Exception as e:
                            error_result = ToolResult(output=f"Tool execution failed: {str(e)}")
                            tool_result = _make_api_tool_result(error_result, content_block["id"])
                            tool_result_content.append(tool_result)
                        display.live.start()
                        await asyncio.sleep(10.5)

                        # output_manager.format_tool_output(result, content_block["name"])
                        tool_result = _make_api_tool_result(result, content_block["id"])
                        ic(tool_result)
                        tool_result_content.append(tool_result)
                        tool_output = result.output if hasattr(result, 'output') else str(result)
                        # display.add_message("tool", (content_block["name"], _extract_text_from_content(tool_output)))
                        
                        # Create a combined content list with both text and tool result
                        combined_content = [{
                            "type": "tool_result",
                            "content": tool_result["content"],
                            "tool_use_id": tool_result["tool_use_id"],
                            "is_error": tool_result["is_error"]
                        }]
                        
                        # Add descriptive text about the tool usage
                        combined_content.append({
                            "type": "text",
                            "text": f"Tool '{content_block['name']}' was called with input: {json.dumps(content_block['input'])}.\nResult: {_extract_text_from_content(tool_output)}"
                        })
                        
                        # Add a single message with the combined content
                        messages.append({
                            "role": "user",
                            "content": combined_content
                        })

                if not tool_result_content:
                    display.live.stop()  # Stop the live display
                    # add a small delay
                    await asyncio.sleep(0.2)
                    rr("\nAwaiting User Input ⌨️")
                    task = Prompt.ask("What would you like to do next? Enter 'no' to exit")
                    display.live.start()  # Restart the live display
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                # display.clear_messages("user")
                await asyncio.sleep(0.2)
                messages_to_display = messages[-2:] if len(messages) > 1 else messages[-1:]
                for message in messages_to_display:
                    display.add_message("tool", message["content"][0]) # Update display

                # display.add_message("user",f"There are {len(messages)} messages")
                # await asyncio.sleep(1.0)

                # display.live.stop()  # Stop the live display
                # # Ask user if they are done reviewing the info using rich's Confirm.ask
                # while Confirm.ask("Do you need more time?", default=True):
                #     ci=0
                #     for message in messages:
                #         rr(f"Message # {ci}")
                #         ci+=1
                #         rr(message)
                # display.live.start()  # Restart the live display
                # asyncio.sleep(delay=0.5)
                token_tracker.update(response)



            except UnicodeEncodeError as ue:
                ic(f"UnicodeEncodeError: {ue}")
                rr(f"Unicode encoding error: {ue}")
                rr(f"ascii: {ue.args[1].encode('ascii', errors='replace').decode('ascii')}")
                break
            except Exception as e:
                ic(f"Error in sampling loop: {str(e).encode('ascii', errors='replace').decode('ascii')}")
                ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
                ic(e.__traceback__.tb_frame.f_locals)
                display.add_message("tool", ("Error", str(e))) # Update display with error
                raise
        token_tracker.display()
        return messages

    except Exception as e:
        ic(e.__traceback__.tb_lineno)
        ic(e.__traceback__.tb_lasti)
        ic(e.__traceback__.tb_frame.f_code.co_filename)
        ic(e.__traceback__.tb_frame)
        display.add_message("tool", ("Initialization Error", str(e))) # Update display with initialization error
        ic(f"Error initializing sampling loop: {str(e)}")
        raise

def _inject_prompt_caching(messages: List[BetaMessageParam]):
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
    min_removal_threshold: int
    ):
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

async def summarize_recent_messages(messages: List[BetaMessageParam], display: AgentDisplay) -> str:

    sum_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    conversation_text = ""
    for msg in messages:
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


    summary_prompt = f"""Please provide a concise casual natural language summary of the messages. 
    They are the actual LLM messages log of interaction and you will provide between 1 and 3 conversational style sentences imforming someone what was done. 
    Focusing on the actions taken and providing the names of and file, functions or other items that were specifically acted on and
    a basic idea of what action was taken and why. We are goint to call this your SUMMARY_RESPONSE. Your SUMMARY_RESPONSE should be enclosed in XML style tags such as like this <SUMMARY_RESPONSE> and </SUMMARY_RESPONSE>
    Your SUMMARY_RESPONSE should  be phased speaking in the first person like you are informing someone as to what you are doing. You could say somthing like this:
    Ok, I will now give you the summary of the conversation.
    <SUMMARY_RESPONSE>
    I have just created a new file called foo.py in the foo/bar directory. 
    I have also updated the great_code.py file with the following changes:
    Added error handling to the function foo() to handle the case when the user enters an invalid input and added a new function called bar() that takes a string as input and returns the string in reverse order.
    </SUMMARY_RESPONSE>
    
    
    Include:
    1. All file names, functions, directories and paths mentioned
    2. Directory structures created or modified
    3. Specific actions taken and their outcomes
    4. Any technical decisions or solutions implemented

    Messages to summarize:
    {conversation_text}"""
    response = sum_client.messages.create(
        model=SUMMARY_MODEL,
        max_tokens=MAX_SUMMARY_TOKENS,
        messages=[{
            "role": "user",
            "content": summary_prompt
        }]
    )
    summary = response.content[0].text
    # filter out everything from the summary that is not enclosed in the XML style tags
    start_tag = "<SUMMARY_RESPONSE>"
    end_tag = "</SUMMARY_RESPONSE>"
    if start_tag in summary and end_tag in summary:
        summary = summary[summary.find(start_tag)+len(start_tag):summary.find(end_tag)]




    return summary

async def run_sampling_loop(task: str, display: AgentDisplay) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    # ic(messages)
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    messages.append({"role": "user","content": task})
    display.add_message("user", task)
 

    messages = await sampling_loop(
        model=MAIN_MODEL,  # Use MAIN_MODEL from config.py
        messages=messages,
        api_key=api_key,
        display=display
    )
    return messages


async def main_async():
    """Async main function with proper error handling."""
    prompts_dir =PROMPTS_DIR
    prompt_files = list(prompts_dir.glob("*.md"))
    rr("\nAvailablePrompts:")
    for i, file in enumerate(prompt_files, 1):
        rr(f"{i}. {file.name}")
    rr(f"{len(prompt_files) + 1}. Create new prompt")

    choice = Prompt.ask(
        "Select prompt number",
        choices=[str(i) for i in range(1, len(prompt_files) + 2)]
    )

    if int(choice) == len(prompt_files) + 1:
        filename = Prompt.ask("Enter new prompt filename (without .md)")
        new_prompt_path = prompts_dir / f"{filename}.md"
    else:
        prompt_path = prompt_files[int(choice) - 1]
        new_prompt_path = prompt_path
        filename = prompt_path.stem


    if int(choice) == len(prompt_files) + 1:
        prompt_text = Prompt.ask("Enter your prompt")
        new_prompt_path = prompts_dir / f"{filename}.md"
        with open(new_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_text)
        task = prompt_text
    else:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            task = f.read()
    project_dir = set_project_dir(filename)
    set_constant("PROJECT_DIR", str(project_dir))
    task += f"Your project directory is {project_dir}. You need to make sure that all files you create and work you do is done in that directory. \n"
    # Create the display instance and setup the layout
    display = AgentDisplay()  # Create instance of AgentDisplay
    layout = display.create_layout()  # Create initial layout

    try:
        # Create console for Live display
        console = Console()
        
        # Start Live display with the layout
        with Live(display.create_layout(), refresh_per_second=4, auto_refresh=True) as live:
            display.live = live  # Set the live attribute
            update_task = asyncio.create_task(display.update_display(live))
            # Run the main sampling loop
            messages = await run_sampling_loop(task, display)
            
            # Wait for any pending updates
            await update_task
            
        rr("\nTask Completed Successfully")

    except Exception as e:
        rr(f"Error during execution: {e}")
        raise  # Re-raise the exception for debugging

def main():
    """Main entry point with proper async handling."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
