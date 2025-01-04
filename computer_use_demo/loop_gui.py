"""
GUI version of the Anthropic API loop using pywebview for display.
Extends the original loop.py functionality with a graphical interface.
"""
import webview
import asyncio
from typing import Optional, List, Any
from pathlib import Path
from datetime import datetime
import json
import os
from anthropic import Anthropic, APIResponse
from anthropic.types.beta import BetaContentBlock, BetaMessageParam
from icecream import ic

# Import original functionality
from loop import OutputManager, TokenTracker, _make_api_tool_result

class GUIOutputManager(OutputManager):
    """GUI-enhanced version of OutputManager using pywebview."""
    
    def __init__(self, image_dir: Optional[Path] = None):
        super().__init__(image_dir)
        self.window = None
        self.html_content = []
        self.setup_gui()

    def setup_gui(self):
        """Initialize the GUI window."""
        self.window = webview.create_window(
            'Anthropic API Output',
            html="<html><body><div id='content'></div></body></html>",
            width=800,
            height=600
        )
        
    def update_gui(self):
        """Update the GUI window with current content."""
        if self.window:
            html_content = "\n".join(self.html_content)
            full_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .tool-output {{ background-color: #f0f0f0; padding: 10px; margin: 10px 0; }}
                    .api-response {{ background-color: #e6f3ff; padding: 10px; margin: 10px 0; }}
                    .recent-conversation {{ border-left: 3px solid #ccc; padding-left: 10px; margin: 10px 0; }}
                    img {{ max-width: 100%; height: auto; }}
                </style>
            </head>
            <body>
                <div id='content'>
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.window.html = full_html

    def format_tool_output(self, result: Any, tool_name: str) -> None:
        """Format and display tool output in GUI."""
        output_html = f"<div class='tool-output'><h3>Tool Execution: {tool_name}</h3>"
        
        if isinstance(result, str):
            output_html += f"<p style='color: red;'>Error: {result}</p>"
        else:
            if result.output:
                output_text = result.output
                if len(output_text) > 500:
                    output_text = output_text[:200] + "...\n..." + output_text[-200:]
                output_html += f"<p>{output_text}</p>"
            
            if result.base64_image:
                image_path = self.save_image(result.base64_image)
                if image_path:
                    output_html += f"<p>Screenshot saved: {image_path}</p>"
                    output_html += f"<img src='file://{image_path}' alt='Screenshot'>"
                else:
                    output_html += "<p style='color: red;'>Failed to save screenshot</p>"
        
        output_html += "</div>"
        self.html_content.append(output_html)
        self.update_gui()

    def format_api_response(self, response: APIResponse) -> None:
        """Format and display API response in GUI."""
        response_html = "<div class='api-response'><h3>Assistant Response</h3>"
        if hasattr(response.content[0], 'text'):
            text = response.content[0].text
            if len(text) > 500:
                text = text[:300] + "..." + text[-300:]
            response_html += f"<p>{text}</p>"
        response_html += "</div>"
        self.html_content.append(response_html)
        self.update_gui()

    def format_recent_conversation(self, messages: List[BetaMessageParam], num_recent: int = 2) -> None:
        """Format and display recent conversation in GUI."""
        conv_html = "<div class='recent-conversation'><h3>Recent Conversation</h3>"
        recent_messages = messages[-num_recent*2:] if len(messages) > num_recent*2 else messages
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                conv_html += "<div style='color: green;'><strong>User:</strong><br>"
            else:
                conv_html += "<div style='color: blue;'><strong>Assistant:</strong><br>"
            
            content = msg['content']
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            if len(text) > 500:
                                text = text[:200] + "...\n..." + text[-200:]
                            conv_html += f"<p>{text}</p>"
                        elif block.get("type") == "tool_use":
                            conv_html += f"<p>Using tool: {block.get('name')}</p>"
            elif isinstance(content, str):
                if len(content) > 500:
                    content = content[:200] + "...\n..." + content[-200:]
                conv_html += f"<p>{content}</p>"
            
            conv_html += "</div>"
        
        conv_html += "</div>"
        self.html_content.append(conv_html)
        self.update_gui()

def main():
    """Main entry point for the GUI version."""
    # Initialize GUI components
    image_dir = Path("output_images")
    output_manager = GUIOutputManager(image_dir)
    
    # Start the GUI event loop
    webview.start(debug=True)

if __name__ == "__main__":
    main()