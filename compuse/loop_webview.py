import webview
import logging
import threading
import time
from datetime import datetime
import json
import sys
import traceback

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('webview.log')
    ]
)

def validate_backend():
    """Validate and select the appropriate WebView backend."""
    available_backends = webview.platforms.AVAILABLE_GUILDERS
    preferred_backends = ['edgechromium', 'edgehtml', 'cef']
    
    logging.info(f"Available backends: {available_backends}")
    
    for backend in preferred_backends:
        if backend in available_backends:
            logging.info(f"Selected backend: {backend}")
            return backend
            
    logging.error("No preferred backend available!")
    return None

class WebViewInterface:
    def __init__(self):
        self.messages = []
        self.window = None
        self.message_file = "messages.json"
        self.load_messages()  # Load previous messages if they exist
        
    def load_messages(self):
        """Load messages from JSON file if it exists."""
        try:
            if os.path.exists(self.message_file):
                with open(self.message_file, 'r') as f:
                    self.messages = json.load(f)
                logging.info(f"Loaded {len(self.messages)} messages from {self.message_file}")
        except Exception as e:
            logging.error(f"Error loading messages: {str(e)}")
            
    def save_messages(self):
        """Save messages to JSON file."""
        try:
            with open(self.message_file, 'w') as f:
                json.dump(self.messages, f, indent=2)
            logging.info(f"Saved {len(self.messages)} messages to {self.message_file}")
        except Exception as e:
            logging.error(f"Error saving messages: {str(e)}")
            
    def submit_message(self, message):
        """Handle user message submission."""
        try:
            # Add user message
            self.add_message('Human', message)
            
            # Process user input and generate response
            response = self.process_user_input(message)
            
            # Add assistant response
            self.add_message('Assistant', response)
            
            # Save messages to file
            self.save_messages()
            
            return True
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return False
            
    def process_user_input(self, message):
        """Process user input and generate appropriate response."""
        message = message.lower().strip()
        
        # Basic command processing
        if 'help' in message:
            return ("I can help you with:\n" +
                   "- File management (open, save, delete files)\n" +
                   "- Application usage (start, stop programs)\n" +
                   "- Web browsing (search, navigate)\n" +
                   "- System settings (display, sound, etc)\n" +
                   "- Troubleshooting issues\n\n" +
                   "Just describe what you'd like to do!")
        
    def set_window(self, window):
        self.window = window
        
    def add_message(self, role, content):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            'role': role,
            'content': content,
            'timestamp': timestamp
        }
        self.messages.append(message)
        if self.window:
            self.window.set_html(self.get_html())
        return message
    
    def get_messages(self):
        return self.messages
    
    def get_html(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }
                .message-container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                .message {
                    background-color: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .human {
                    border-left: 4px solid #007bff;
                }
                .assistant {
                    border-left: 4px solid #28a745;
                }
                .timestamp {
                    color: #666;
                    font-size: 0.8em;
                    margin-top: 5px;
                }
                .role {
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: #444;
                }
                .content {
                    white-space: pre-wrap;
                    line-height: 1.5;
                }
            </style>
        </head>
        <body>
            <div class="message-container">
                <h2>Computer Use Assistant</h2>
        """
        
        for msg in self.messages:
            html += f"""
                <div class="message {msg['role'].lower()}">
                    <div class="role">{msg['role'].title()}</div>
                    <div class="content">{msg['content']}</div>
                    <div class="timestamp">{msg['timestamp']}</div>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        return html

def main():
    try:
        # Validate and select backend
        backend = validate_backend()
        if not backend:
            logging.error("No suitable backend found. Please install either EdgeHTML or CEF backend.")
            sys.exit(1)

        logging.info("Initializing WebView interface...")
        api = WebViewInterface()
        
        # Create window with enhanced error handling
        try:
            window = webview.create_window(
                'Computer Use Assistant',
                html=api.get_html(),
                js_api=api,
                width=1000,
                height=800,
                min_size=(600, 400),
                gui=backend
            )
        except Exception as e:
            logging.error(f"Failed to create window using {backend} backend: {str(e)}")
            logging.error(traceback.format_exc())
            sys.exit(1)

        api.set_window(window)
        
        def update_messages():
            try:
                time.sleep(2)  # Wait for window to load
                api.add_message('Assistant', 'Hello! I am your Computer Use Assistant. How can I help you today?')
                time.sleep(1)
                api.add_message('Human', 'Can you help me use this computer?')
                time.sleep(1)
                api.add_message('Assistant', 'Of course! I can help you with various tasks like:\n' + 
                              '- File management and organization\n' +
                              '- Application usage and settings\n' +
                              '- Web browsing and downloads\n' +
                              '- System settings and configuration\n' +
                              '- Performance optimization\n' +
                              '- Troubleshooting issues\n\n' +
                              'What would you like assistance with?')
            except Exception as e:
                logging.error(f"Error in update_messages: {str(e)}")
                logging.error(traceback.format_exc())
        
        # Start message update thread
        logging.info("Starting message update thread...")
        t = threading.Thread(target=update_messages)
        t.daemon = True
        t.start()
        
        # Start WebView with debug mode and error handling
        logging.info("Starting WebView application...")
        try:
            webview.start(debug=True)
        except Exception as e:
            logging.error(f"Failed to start WebView: {str(e)}")
            logging.error(traceback.format_exc())
            sys.exit(1)
        
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        logging.error(traceback.format_exc())
        raise

if __name__ == '__main__':
    main()