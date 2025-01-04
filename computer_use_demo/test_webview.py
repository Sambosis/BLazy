ging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def main():
    try:
        # Create a simple window
        window = webview.create_window('Test Window', 
                                     html='<h1>Hello World</h1>',
                                     width=800,
                                     height=600)
        # Start webview with explicit GUI backend and debug mode
        webview.start(debug=True, gui='winforms')
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in main: {e}")python test_webview.py
pip install pywebview[winforms]
pip install PyQt5
notepad test_webview.py
import webview
import logging
import sys
from PyQt5.QtWidgets import QApplication

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def main():
    try:
        # Create a simple window
        window = webview.create_window('Test Window', 
                                     html='<h1>Hello World</h1>',
                                     width=800,
                                     height=600)
        # Start webview with explicit GUI backend and debug mode
        webview.start(debug=True, gui='qt')
    except Exception as e:
        print(f"Error occurred: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error in main: {e}")python test_webview.py
cd C:\mygit\compuse\computer_use_demo
python loop_tkinter.py
