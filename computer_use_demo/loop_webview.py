"""
Modified version of loop.py that uses pywebview to display output in a GUI window.
"""
import os
import asyncio
import webview
import threading
from datetime import datetime
from typing import List, Any
from anthropic import Anthropic
from anthropic.types.beta import BetaMessageParam
from tools import (BashTool, ComputerTool, EditTool, ToolCollection, 
                  GetExpertOpinionTool, WebNavigatorTool, WindowsNavigationTool)
from icecream import ic
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from io import StringIO

# Initialize rich console with string buffer
output_buffer = StringIO()
console = Console(file=output_buffer, record=True)

class WebViewOutput:
    def __init__(self):
        self.window = None
        self.html_content = []
        
    def create_window(self):
        self.window = webview.create_window('Assistant Output', 
                                          html="<h1>Assistant Interface</h1>",
                                          width=800, 
                                          height=600)
        
    def update_content(self, content):
        if not self.window:
            return
            
        # Convert content to HTML
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .message {{
                    margin: 10px 0;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .user {{
                    background-color: #e3f2fd;
                }}
                .assistant {{
                    background-color: #f3e5f5;
                }}
                .tool-result {{
                    background-color: #e8f5e9;
                }}
                pre {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
        self.window.html = html_content

class OutputManager:
    def __init__(self, image_dir: Path, webview_output: WebViewOutput):
        self.image_dir = image_dir
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.image_counter = 0
        self.webview_output = webview_output
        
    def format_message_to_html(self, role: str, content: Any) -> str:
        html = f'<div class="message {role.lower()}">'
        html += f'<strong>{role.upper()}:</strong><br/>'
        
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        html += '<div class="tool-result">'
                        html += f'<strong>Tool Result:</strong><br/>'
                        for item in block.get("content", []):
                            if item.get("type") == "text":
                                html += f'<pre>{item.get("text")}</pre>'
                            elif item.get("type") == "image":
                                html += '<em>(Screenshot captured)</em><br/>'
                        html += '</div>'
                    else:
                        html += f'<pre>{str(block)}</pre>'
                else:
                    html += f'<pre>{str(block)}</pre>'
        else:
            html += f'<pre>{str(content)}</pre>'
            
        html += '</div>'
        return html

    def update_display(self, messages: List[BetaMessageParam]):
        html_content = ""
        for msg in messages[-10:]:  # Show last 10 messages
            html_content += self.format_message_to_html(msg["role"], msg["content"])
        self.webview_output.update_content(html_content)

async def sampling_loop(*, 
                       model: str, 
                       messages: List[BetaMessageParam], 
                       api_key: str, 
                       max_tokens: int = 8000,
                       output_manager: OutputManager) -> List[BetaMessageParam]:
    try:
        tool_collection = ToolCollection(
            BashTool(),
            EditTool(),
            GetExpertOpinionTool(),
            ComputerTool(),
            WebNavigatorTool(),
            WindowsNavigationTool()
        )
        
        client = Anthropic(api_key=api_key)
        running = True
        i = 0
        
        while running:
            console.print(f"\n[bold yellow]Iteration {i}[/bold yellow] 🔄")
            i += 1
            
            try:
                response = client.beta.messages.create(
                    max_tokens=max_tokens,
                    messages=messages,
                    model=model,
                    tools=tool_collection.to_params()
                )
                
                # Convert response content to params format
                response_params = []
                for block in response.content:
                    if hasattr(block, 'text'):
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
                
                messages.append({
                    "role": "assistant",
                    "content": response_params
                })
                
                # Update the webview display
                output_manager.update_display(messages)
                
                # Process tool uses and collect results
                tool_result_content = []
                for content_block in response_params:
                    if content_block["type"] == "tool_use":
                        result = await tool_collection.run(
                            name=content_block["name"],
                            tool_input=content_block["input"],
                        )
                        
                        tool_result = {
                            "type": "tool_result",
                            "content": [{
                                "type": "text",
                                "text": str(result)
                            }] if isinstance(result, str) else [
                                {"type": "text", "text": result.output} if result.output else None,
                                {"type": "image", "source": {
                                    "type": "base64",
                                    "data": result.base64_image
                                }} if result.base64_image else None
                            ],
                            "tool_use_id": content_block["id"]
                        }
                        tool_result_content.append(tool_result)
                
                if not tool_result_content:
                    # Create an HTML form for user input
                    input_form = '''
                    <div class="message user">
                        <form id="userInput">
                            <label for="task">What would you like to do next? (Enter 'no' to exit)</label><br>
                            <input type="text" id="task" name="task" style="width: 100%"><br>
                            <input type="submit" value="Submit">
                        </form>
                    </div>
                    '''
                    webview_output.window.evaluate_js(f"document.body.innerHTML += `{input_form}`")
                    
                    # Wait for user input
                    task = await asyncio.to_thread(input, "What would you like to do next? Enter 'no' to exit: ")
                    if task.lower() in ["no", "n"]:
                        running = False
                    messages.append({"role": "user", "content": task})
                else:
                    messages.append({
                        "role": "user",
                        "content": tool_result_content
                    })
                
                output_manager.update_display(messages)
                
            except Exception as e:
                console.print(f"[red]Error in iteration: {str(e)}[/red]")
                break
                
        return messages
        
    except Exception as e:
        console.print(f"[red]Error in sampling loop: {str(e)}[/red]")
        raise

async def run_sampling_loop(task: str, webview_output: WebViewOutput) -> List[BetaMessageParam]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
        
    messages.append({"role": "user", "content": task})
    
    output_manager = OutputManager(
        image_dir=Path('logs/computer_tool_images'),
        webview_output=webview_output
    )
    
    messages = await sampling_loop(
        model="claude-3-5-sonnet-latest",
        messages=messages,
        api_key=api_key,
        output_manager=output_manager
    )
    
    return messages

def start_webview():
    webview_output = WebViewOutput()
    webview_output.create_window()
    return webview_output

async def main_async():
    # Create and start webview in a separate thread
    webview_output = await asyncio.to_thread(start_webview)
    
    try:
        with open(r"C:\mygit\compuse\computer_use_demo\prompt.md", 'r', encoding="utf-8") as f:
            task = f.read()
            
        messages = await run_sampling_loop(task, webview_output)
        console.print("\n[green]Task Completed Successfully[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during execution: {str(e)}[/red]")
    finally:
        # Close the webview window
        if webview_output.window:
            webview_output.window.destroy()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()