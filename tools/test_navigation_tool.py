# windows_navigation_tool.py
# windows_navigation_tool.py

import pyautogui
import time
from typing import Optional
from rich import print as rr

# Define available shortcuts
# shortcuts = {
#     "switch_window": {"keys": ["alt", "tab"]},
#     "open_start_menu": {"keys": ["win"]},
#     "minimize_window": {"keys": ["win", "down"]},
#     "maximize_window": {"keys": ["win", "up"]},
#     "close_window": {"keys": ["alt", "f4"]},
#     "take_screenshot": {"keys": ["win", "printscreen"]},
#     # Add more shortcuts as needed
# }
shortcuts = {
    "switch_window": {
        "keys": ["alt", "tab"]
                    },
    "open_start_menu": {
        "keys": ["win"]
                    },
    "minimize_window": {
        "keys": ["win", "down"]
                    },
    "maximize_window": {
        "keys": ["win", "up"]
                    },
    "restore_window": {
        "keys": ["win", "down"]
                    },
    "close_window": {
        "keys": ["alt", "f4"]
                    },
    "take_screenshot": {
        "keys": ["win", "prtsc"]
                    },
    "go_to_desktop": {
        "keys": ["win", "d"]
                    },
    "switch_virtual_desktop_left": {
        "keys": ["win", "ctrl", "left"]
                    },
    "switch_virtual_desktop_right": {
        "keys": ["win", "ctrl", "right"]
                    },
    "open_file_explorer": {
        "keys": ["win", "e"]
                    },
    "refresh_explorer": {
        "keys": ["f5"]
                    },
    "open_task_manager": {
        "keys": ["ctrl", "shift", "esc"]
                    },
    "lock_workstation": {
        "keys": ["win", "l"]
                    },
    "sign_out": {
        "keys": ["ctrl", "alt", "del"]
                    },
    "hibernate": {
        "keys": ["win", "x", "u", "h"]
                    },
    "sleep": {
        "keys": ["win", "x", "u", "s"]
                    },
    "copy": {
        "keys": ["ctrl", "c"]
                    },
    "paste": {
        "keys": ["ctrl", "v"]
                    },
    "cut": {
        "keys": ["ctrl", "x"]
                    },
    "select_all": {
        "keys": ["ctrl", "a"]
                    },
    "open_run_dialog": {
        "keys": ["win", "r"]
                    },
    "open_settings": {
        "keys": ["win", "i"]
                    },
    "open_search": {
        "keys": ["win", "s"]
                    },
    "toggle_high_contrast": {
        "keys": ["altleft", "shiftleft", "printscreen"]
                        },
    "toggle_narrator": {
        "keys": ["winleft", "ctrl", "enter"]
                    },
    "toggle_magnifier": {
        "keys": ["winleft", "plus"]
                    },
                        # Additional shortcuts
    "undo": {"keys": ["ctrl", "z"]},
    "redo": {"keys": ["ctrl", "y"]},
    "new_virtual_desktop": {"keys": ["win", "ctrl", "d"]},
    "close_virtual_desktop": {"keys": ["win", "ctrl", "f4"]},
    "switch_between_open_apps": {"keys": ["alt", "esc"]},
    "open_action_center": {"keys": ["win", "a"]},
    "open_game_bar": {"keys": ["win", "g"]},
    "open_project_menu": {"keys": ["win", "x"]},
    "open_clipboard_history": {"keys": ["win", "v"]},
    "open_emoji_panel": {"keys": ["win", "period"]},
    "snap_window_left": {"keys": ["win", "left"]},
    "snap_window_right": {"keys": ["win", "right"]},
    "open_task_view": {"keys": ["win", "tab"]},
    "open_file_menu": {"keys": ["alt"]},
    "rename_selected_item": {"keys": ["f2"]},
    "search_for_files": {"keys": ["f3"]},
    "display_properties": {"keys": ["alt", "enter"]},
    "open_address_bar": {"keys": ["f4"]},
    "cycle_through_screen_elements": {"keys": ["f6"]},
    "refresh_active_window": {"keys": ["f5"]},
    "activate_menu_bar": {"keys": ["f10"]},
    "show_context_menu": {"keys": ["shift", "f10"]},
    "open_cortana": {"keys": ["win", "c"]},
    "lock_device_orientation": {"keys": ["win", "o"]},
    "open_quick_link_menu": {"keys": ["win", "x"]},
    "open_notification_center": {"keys": ["win", "n"]},
    "focus_hidden_icons": {"keys": ["win", "b"]},
    "open_ease_of_access_center": {"keys": ["win", "u"]},
    "open_windows_ink_workspace": {"keys": ["win", "w"]},
    "open_connect_pane": {"keys": ["win", "k"]},
    "open_share_pane": {"keys": ["win", "h"]},
    "open_device_pane": {"keys": ["win", "k"]},
    "open_system_properties": {"keys": ["win", "pause"]},
    "open_file_explorer_options": {"keys": ["alt", "t", "o"]},
    "create_new_folder": {"keys": ["ctrl", "shift", "n"]},
    "open_properties_of_selected_item": {"keys": ["alt", "enter"]},
    "open_this_pc": {"keys": ["win", "e"]},
    "cycle_through_taskbar_items": {"keys": ["win", "t"]},
    "open_new_instance_of_app": {"keys": ["shift", "click_taskbar_icon"]},
    "pin_app_to_taskbar": {"keys": ["shift", "right_click_taskbar_icon"]},
    "show_windows_side_by_side": {"keys": ["win", "shift", "left/right"]},
    "minimize_all_windows": {"keys": ["win", "m"]},
    "restore_minimized_windows": {"keys": ["win", "shift", "m"]},
    "stretch_window_to_top_and_bottom": {"keys": ["win", "shift", "up"]},
    "move_window_to_other_monitor": {"keys": ["win", "shift", "left/right"]},
    "rotate_screen": {"keys": ["ctrl", "alt", "arrow_keys"]},
    "open_snipping_tool": {"keys": ["win", "shift", "s"]},
}
shortcuts.update({
    # "new_tab": {"keys": ["ctrl", "t"]},
    # "close_tab": {"keys": ["ctrl", "w"]},
    # "reopen_closed_tab": {"keys": ["ctrl", "shift", "t"]},
    # "open_browser_history": {"keys": ["ctrl", "h"]},
    # "open_downloads": {"keys": ["ctrl", "j"]},
    # "refresh_page": {"keys": ["ctrl", "r"]},
    #     "bookmark_page": {"keys": ["ctrl", "d"]},
    #     "search_page": {"keys": ["ctrl", "f"]},
    #     "zoom_in": {"keys": ["ctrl", "plus"]},
    #     "zoom_out": {"keys": ["ctrl", "minus"]},
    #     "reset_zoom": {"keys": ["ctrl", "0"]},
        "open_dev_tools": {"keys": ["ctrl", "shift", "i"]}
        })
shortcuts.update({
        "new_virtual_desktop": {"keys": ["win", "ctrl", "d"]},
        "close_virtual_desktop": {"keys": ["win", "ctrl", "f4"]},
        "snap_window_left": {"keys": ["win", "left"]},
        "snap_window_right": {"keys": ["win", "right"]},
        "snap_window_top": {"keys": ["win", "up"]},
        "snap_window_bottom": {"keys": ["win", "down"]},
        "open_action_center": {"keys": ["win", "a"]},
        "open_notifications": {"keys": ["win", "n"]}
    })
shortcuts.update({
        "move_cursor_word_left": {"keys": ["ctrl", "left"]},
        "move_cursor_word_right": {"keys": ["ctrl", "right"]},
        "move_cursor_start_line": {"keys": ["home"]},
        "move_cursor_end_line": {"keys": ["end"]},
        "move_cursor_start_document": {"keys": ["ctrl", "home"]},
        "move_cursor_end_document": {"keys": ["ctrl", "end"]},
        "delete_word_left": {"keys": ["ctrl", "backspace"]},
        "delete_word_right": {"keys": ["ctrl", "delete"]},
        "select_word_left": {"keys": ["ctrl", "shift", "left"]},
        "select_word_right": {"keys": ["ctrl", "shift", "right"]},
        "select_line": {"keys": ["shift", "home"]},
        "select_to_end": {"keys": ["shift", "end"]}
    })
shortcuts.update({
        "play_pause_media": {"keys": ["fn", "f5"]},
        "next_track": {"keys": ["fn", "f6"]},
        "previous_track": {"keys": ["fn", "f7"]},
        "mute_volume": {"keys": ["fn", "f8"]},
        "volume_up": {"keys": ["fn", "f9"]},
        "volume_down": {"keys": ["fn", "f10"]}
    })
shortcuts.update({
        "toggle_filter_keys": {"keys": ["hold", "shiftright", "8"]},
        "open_ease_of_access_center": {"keys": ["win", "u"]},
        "toggle_screen_reader": {"keys": ["ctrl", "alt", "s"]},
        "open_on_screen_keyboard": {"keys": ["win", "ctrl", "o"]},
        "start_dictation": {"keys": ["win", "h"]}
    })
windows_navigate_function = {
    "name": "windows_navigate",
    "description": "A tool for Windows navigation using keyboard shortcuts.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": list(shortcuts.keys()),
                "description": "The Windows action to perform."
            },
            "modifier": {
                "type": ["string", "null"],
                "enum": ["ctrl", "alt", "shift", "win"],
                "description": "Optional modifier key."
            },
            "target": {
                "type": ["string", "null"],
                "description": "Optional target for the action (e.g., window title)."
            }
        },
        "required": ["action"],
    },
}
def windows_navigate(action: str, modifier: Optional[str] = None, target: Optional[str] = None) -> str:
    """
    Execute the requested Windows action.
    Args:
        action (str): The action to perform.
        modifier (Optional[str]): Optional modifier key(s).
        target (Optional[str]): Optional target for the action.
    Returns:
        str: Result message.    """
    # shortcuts = {
    #             "switch_window": {"keys": ["alt", "tab"]},
    #             "open_start_menu": {"keys": ["win"]},
    #             "minimize_window": {"keys": ["win", "down"]},
    #             "maximize_window": {"keys": ["win", "up"]},
    #             "restore_window": {"keys": ["win", "up"]},
    #             "close_window": {"keys": ["alt", "f4"]},
    #             "take_screenshot": {"keys": ["win", "prtsc"]},
    #             "go_to_desktop": {"keys": ["win", "d"]},
    #             "switch_virtual_desktop_left": {"keys": ["win", "ctrl", "left"]},
    #             "switch_virtual_desktop_right": {"keys": ["win", "ctrl", "right"]},
    #             "open_file_explorer": {"keys": ["win", "e"]},
    #             "refresh_explorer": {"keys": ["f5"]},
    #             "open_task_manager": {"keys": ["ctrl", "shift", "esc"]},
    #             "lock_workstation": {"keys": ["win", "l"]},
    #             "sign_out": {"keys": ["ctrl", "alt", "del"]},
    #             "hibernate": {"keys": ["win", "x", "u", "h"]},
    #             "sleep": {"keys": ["win", "x", "u", "s"]},
    #             "copy": {"keys": ["ctrl", "c"]},
    #             "paste": {"keys": ["ctrl", "v"]},
    #             "cut": {"keys": ["ctrl", "x"]},
    #             "select_all": {"keys": ["ctrl", "a"]},
    #             "open_run_dialog": {"keys": ["win", "r"]},
    #             "open_settings": {"keys": ["win", "i"]},
    #             "open_search": {"keys": ["win", "s"]},
    #             "toggle_high_contrast": {"keys": ["altleft", "shiftleft", "printscreen"]},
    #             "toggle_narrator": {"keys": ["winleft", "ctrl", "enter"]},
    #             "toggle_magnifier": {"keys": ["winleft", "plus"]},
    #             "undo": {"keys": ["ctrl", "z"]},
    #             "redo": {"keys": ["ctrl", "y"]},
    #             "new_virtual_desktop": {"keys": ["win", "ctrl", "d"]},
    #             "close_virtual_desktop": {"keys": ["win", "ctrl", "f4"]},
    #             "switch_between_open_apps": {"keys": ["alt", "esc"]},
    #             "open_action_center": {"keys": ["win", "a"]},
    #             "open_game_bar": {"keys": ["win", "g"]},
    #             "open_project_menu": {"keys": ["win", "x"]},
    #             "open_clipboard_history": {"keys": ["win", "v"]},
    #             "open_emoji_panel": {"keys": ["win", "period"]},
    #             "snap_window_left": {"keys": ["win", "left"]},
    #             "snap_window_right": {"keys": ["win", "right"]},
    #             "open_task_view": {"keys": ["win", "tab"]},
    #             "open_file_menu": {"keys": ["alt"]},
    #             "rename_selected_item": {"keys": ["f2"]},
    #             "search_for_files": {"keys": ["f3"]},
    #             "display_properties": {"keys": ["alt", "enter"]},
    #             "open_address_bar": {"keys": ["f4"]},
    #             "cycle_through_screen_elements": {"keys": ["f6"]},
    #             "refresh_active_window": {"keys": ["f5"]},
    #             "activate_menu_bar": {"keys": ["f10"]},
    #             "show_context_menu": {"keys": ["shift", "f10"]},
    #             "open_cortana": {"keys": ["win", "c"]},
    #             "lock_device_orientation": {"keys": ["win", "o"]},
    #             "open_quick_link_menu": {"keys": ["win", "x"]},
    #             "open_notification_center": {"keys": ["win", "n"]},
    #             "focus_hidden_icons": {"keys": ["win", "b"]},
    #             "open_ease_of_access_center": {"keys": ["win", "u"]},
    #             "open_windows_ink_workspace": {"keys": ["win", "w"]},
    #             "open_connect_pane": {"keys": ["win", "k"]},
    #             "open_share_pane": {"keys": ["win", "h"]},
    #             "open_device_pane": {"keys": ["win", "k"]},
    #             "open_system_properties": {"keys": ["win", "pause"]},
    #             "open_file_explorer_options": {"keys": ["alt", "t", "o"]},
    #             "create_new_folder": {"keys": ["ctrl", "shift", "n"]},
    #             "open_properties_of_selected_item": {"keys": ["alt", "enter"]},
    #             "open_this_pc": {"keys": ["win", "e"]},
    #             "cycle_through_taskbar_items": {"keys": ["win", "t"]},
    #             "open_new_instance_of_app": {"keys": ["shift", "click_taskbar_icon"]},
    #             "pin_app_to_taskbar": {"keys": ["shift", "right_click_taskbar_icon"]},
    #             "show_windows_side_by_side": {"keys": ["win", "shift", "left/right"]},
    #             "minimize_all_windows": {"keys": ["win", "m"]},
    #             "restore_minimized_windows": {"keys": ["win", "shift", "m"]},
    #             "stretch_window_to_top_and_bottom": {"keys": ["win", "shift", "up"]},
    #             "move_window_to_other_monitor": {"keys": ["win", "shift", "left/right"]},
    #             "rotate_screen": {"keys": ["ctrl", "alt", "arrow_keys"]},
    #             "open_snipping_tool": {"keys": ["win", "shift", "s"]},
    #             "search_in_browser": {"keys": ["ctrl", "k"]},
    #             "new_tab": {"keys": ["ctrl", "t"]},
    #             "close_tab": {"keys": ["ctrl", "w"]},
    #             "reopen_closed_tab": {"keys": ["ctrl", "shift", "t"]},
    #             "open_browser_history": {"keys": ["ctrl", "h"]},
    #             "open_downloads": {"keys": ["ctrl", "j"]},
    #             "refresh_page": {"keys": ["ctrl", "r"]},
    #             "bookmark_page": {"keys": ["ctrl", "d"]},
    #             "search_page": {"keys": ["ctrl", "f"]},
    #             "zoom_in": {"keys": ["ctrl", "plus"]},
    #             "zoom_out": {"keys": ["ctrl", "minus"]},
    #             "reset_zoom": {"keys": ["ctrl", "0"]},
    #             "open_dev_tools": {"keys": ["ctrl", "shift", "i"]},
    #             "new_virtual_desktop": {"keys": ["win", "ctrl", "d"]},
    #             "close_virtual_desktop": {"keys": ["win", "ctrl", "f4"]},
    #             "snap_window_left": {"keys": ["win", "left"]},
    #             "snap_window_right": {"keys": ["win", "right"]},
    #             "snap_window_top": {"keys": ["win", "up"]},
    #             "snap_window_bottom": {"keys": ["win", "down"]},
    #             "open_action_center": {"keys": ["win", "a"]},
    #             "open_notifications": {"keys": ["win", "n"]},
    #             "move_cursor_word_left": {"keys": ["ctrl", "left"]},
    #             "move_cursor_word_right": {"keys": ["ctrl", "right"]},
    #             "move_cursor_start_line": {"keys": ["home"]},
    #             "move_cursor_end_line": {"keys": ["end"]},
    #             "move_cursor_start_document": {"keys": ["ctrl", "home"]},
    #             "move_cursor_end_document": {"keys": ["ctrl", "end"]},
    #             "delete_word_left": {"keys": ["ctrl", "backspace"]},
    #             "delete_word_right": {"keys": ["ctrl", "delete"]},
    #             "select_word_left": {"keys": ["ctrl", "shift", "left"]},
    #             "select_word_right": {"keys": ["ctrl", "shift", "right"]},
    #             "select_line": {"keys": ["shift", "home"]},
    #             "select_to_end": {"keys": ["shift", "end"]},
    #             "play_pause_media": {"keys": ["fn", "f5"]},
    #             "next_track": {"keys": ["fn", "f6"]},
    #             "previous_track": {"keys": ["fn", "f7"]},
    #             "mute_volume": {"keys": ["fn", "f8"]},
    #             "volume_up": {"keys": ["fn", "f9"]},
    #             "volume_down": {"keys": ["fn", "f10"]},
    #             "toggle_filter_keys": {"keys": ["hold", "shiftright", "8"]},
    #             "open_ease_of_access_center": {"keys": ["win", "u"]},
    #             "toggle_screen_reader": {"keys": ["ctrl", "alt", "s"]},
    #             "open_on_screen_keyboard": {"keys": ["win", "ctrl", "o"]},
    #             "start_dictation": {"keys": ["win", "h"]}
    # }
    try:
        shortcut = shortcuts.get(action)
        if not shortcut:
            return f"Unknown action: {action}"

        keys = shortcut["keys"]
        if modifier:
            keys = [modifier] + keys
        # Activate target window if specified
        if target:
            windows = pyautogui.getWindowsWithTitle(target)
            if windows:
                windows[0].activate()
                time.sleep(0.5)
            else:
                return f"No window found with title '{target}'"
        rr(f"keys: {keys}")
        # Execute the key combination
        # pyautogui.hotkey(*keys)
        for key in keys:
            pyautogui.keyDown(key)
            time.sleep(0.1)

        for key in reversed(keys):
            pyautogui.keyUp(key)
            time.sleep(0.1)

        return f"Successfully executed '{action}'"
    except Exception as e:
        return f"Failed to execute '{action}': {str(e)}"
