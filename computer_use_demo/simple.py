import asyncio
import pyautogui
import pyperclip
import time
import subprocess
import base64
from pathlib import Path
from anthropic import Anthropic
from tools.computer import WindowsUseTool
from tools.base import ToolResult
import os 
api_key = os.getenv("ANTHROPIC_API_KEY")
# Initialize Anthropic client (replace with your actual API key)
anthropic = Anthropic(api_key=api_key)
async def ask_model(prompt, image=None):
    messages = [{"role": "user", "content": prompt}]
    if image:
        # Remove the data URI prefix and set the correct media type
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image}}
        ]
    
    response = anthropic.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1000,
        messages=messages
    )
    return response.content[0].text

async def take_screenshot():
    computer_tool = WindowsUseTool()
    result = await computer_tool(action="screenshot")
    if isinstance(result, ToolResult) and result.base64_image:
        return result.base64_image
    return None

async def web_scrape_to_word():
    # computer_tool = WindowsUseTool()
    url = "https://www.autochlor.net/wps"
    subprocess.Popen(r""""C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Default" """)  # Windows
    time.sleep(1)

    
    # Focus on address bar
    pyautogui.hotkey("ctrl", "l")
    # Paste the URL using clipboard
    pyperclip.copy(url)  # Copy URL to clipboard
    pyautogui.hotkey("ctrl", "v")   
    pyautogui.hotkey("return")
    time.sleep(1)


    pyautogui.hotkey("ctrl", "u")
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "c")
    source_code = pyperclip.paste()
    subprocess.Popen('notepad.exe')  # Windows
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.hotkey("ctrl", "s")
    time.sleep(1)
    pyperclip.copy("acpag90e.txt")
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")
    pyperclip.paste()
    pyautogui.hotkey("enter")
# Run the script
asyncio.run(web_scrape_to_word())


    # # Verify Chrome is open
    # screenshot = await take_screenshot()
    # response = await ask_model("Is Chrome open in this screenshot?", screenshot)
    # print(response)
    # if "yes" not in response.lower():
    #     print("Chrome didn't open properly. Stopping.")
    #     return
    # # Verify Chrome is open
    # screenshot = await take_screenshot()
    # response = await ask_model("Is Chrome open in this screenshot?", screenshot)
    # print(response)
    # if "yes" not in response.lower():
    #     print("Chrome didn't open properly. Stopping.")
    #     return
