import asyncio
import base64
import os
import shlex
import shutil
from enum import StrEnum
from typing import Optional, Union, Tuple, Literal, TypedDict
from pathlib import Path
from uuid import uuid4
import pyautogui
import logging
import time
import pygetwindow as gw
from PIL import Image
from anthropic.types.beta import BetaToolComputerUse20241022Param
import pyperclip
from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
from .run import run

OUTPUT_DIR = os.path.join(os.getenv('APPDATA', ''), 'computer_tool', 'outputs')

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50
Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]

class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: Optional[int]

class ComputerTool(BaseAnthropicTool):
    description=f"""
 Use a mouse and keyboard to interact with a computer, and take screenshots.
* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.
* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to see the results of your actions. E.g. if you click on Firefox and a window doesn't open, try taking another screenshot.
* The screen's resolution is {{ display_width_px }}x{{ display_height_px }}.
* The display number is {{ display_number }}
* Whenever you intend to move the cursor to click on an element like an icon, you should consult a screenshot to determine the coordinates of the element before moving the cursor.
* If you tried clicking on a program or link but it failed to load, even after waiting, try adjusting your cursor position so that the tip of the cursor visually falls on the element that you want to click.
* Make sure to click any buttons, links, icons, etc with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.

    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 1.0
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        width, height = self.scale_coordinates(
            ScalingSource.COMPUTER, self.width, self.height
        )
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self):
        super().__init__()
        self.width = pyautogui.size().width
        self.height = pyautogui.size().height
        self.display_num = None
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    async def __call__(
        self,
        *,
        action: Action,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            if action in ("mouse_move", "left_click_drag"):
                if coordinate is None:
                    raise ToolError(f"coordinate is required for {action}")
                if text is not None:
                    raise ToolError(f"text is not accepted for {action}")
                if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
                    raise ToolError(f"{coordinate} must be a tuple of length 2")
                if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                    raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

                x, y = self.scale_coordinates(
                    ScalingSource.API, coordinate[0], coordinate[1]
                )

                if action == "mouse_move":
                    pyautogui.moveTo(x, y)
                    return ToolResult(output=f"Moved mouse to {x}, {y}")
                else:  # left_click_drag
                    pyautogui.dragTo(x, y, button='left')
                    return ToolResult(output=f"Dragged mouse to {x}, {y}")

            if action in ("key", "type"):
                if text is None:
                    raise ToolError(f"text is required for {action}")
                if coordinate is not None:
                    raise ToolError(f"coordinate is not accepted for {action}")
                if not isinstance(text, str):
                    raise ToolError(f"{text} must be a string")

                if action == "key":
                    pyautogui.press(text)
                    return ToolResult(output=f"Pressed key: {text}")
                else:  # type
                    pyautogui.write(text, interval=TYPING_DELAY_MS/1000)
                    screenshot = await self.screenshot()
                    return ToolResult(
                        output=f"Typed text: {text}",
                        base64_image=screenshot.base64_image
                    )

            if action in (
                "left_click",
                "right_click",
                "double_click",
                "middle_click",
                "screenshot",
                "cursor_position",
            ):
                if text is not None:
                    raise ToolError(f"text is not accepted for {action}")
                if coordinate is not None:
                    raise ToolError(f"coordinate is not accepted for {action}")

                if action == "screenshot":
                    return await self.screenshot()

                elif action == "cursor_position":
                    pos = pyautogui.position()
                    x, y = self.scale_coordinates(
                        ScalingSource.COMPUTER, pos.x, pos.y
                    )
                    return ToolResult(output=f"X={x},Y={y}")
                else:
                    click_map = {
                        "left_click": lambda: pyautogui.click(button='left'),
                        "right_click": lambda: pyautogui.click(button='right'),
                        "middle_click": lambda: pyautogui.click(button='middle'),
                        "double_click": lambda: pyautogui.doubleClick(),
                    }
                    click_map[action]()
                    return ToolResult(output=f"Performed {action}")

            raise ToolError(f"Invalid action: {action}")

        except Exception as e:
            return ToolResult(error=str(e))

    async def screenshot(self) -> ToolResult:
        """Take a screenshot of the current screen and return the base64 encoded image."""
        try:
            path = Path(OUTPUT_DIR) / f"screenshot_{uuid4().hex}.png"
            
            # Take screenshot
            screen = pyautogui.screenshot()
            
            # Scale if enabled
            if self._scaling_enabled:
                x, y = self.scale_coordinates(
                    ScalingSource.COMPUTER, self.width, self.height
                )
                screen = screen.resize((x, y), Image.Resampling.LANCZOS)
            
            # Save and encode
            screen.save(str(path))
            base64_image = base64.b64encode(path.read_bytes()).decode()
            
            # Clean up old files
            self._cleanup_screenshots()
            
            return ToolResult(
                output="Screenshot taken",
                base64_image=base64_image
            )
        except Exception as e:
            return ToolResult(error=f"Failed to take screenshot: {str(e)}")

    def _cleanup_screenshots(self, max_files: int = 100):
        """Clean up old screenshots, keeping only the most recent ones."""
        try:
            screenshots = sorted(
                Path(OUTPUT_DIR).glob("*.png"),
                key=lambda x: x.stat().st_mtime
            )
            if len(screenshots) > max_files:
                for screenshot in screenshots[:-max_files]:
                    screenshot.unlink()
        except Exception as e:
            logging.warning(f"Error cleaning up screenshots: {e}")

    def scale_coordinates(self, source: ScalingSource, x: int, y: int):
        """Scale coordinates to a target maximum resolution."""
        if not self._scaling_enabled:
            return x, y
        ratio = self.width / self.height
        target_dimension = None
        for dimension in MAX_SCALING_TARGETS.values():
            # allow some error in the aspect ratio - not ratios are exactly 16:9
            if abs(dimension["width"] / dimension["height"] - ratio) < 0.02:
                if dimension["width"] < self.width:
                    target_dimension = dimension
                break
        if target_dimension is None:
            return x, y
        # should be less than 1
        x_scaling_factor = target_dimension["width"] / self.width
        y_scaling_factor = target_dimension["height"] / self.height
        if source == ScalingSource.API:
            if x > self.width or y > self.height:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            # scale up
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        # scale down
        return round(x * x_scaling_factor), round(y * y_scaling_factor)
