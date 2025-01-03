import webview
import logging
import sys
import threading
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Api:
    def __init__(self):
        self.messages = []
        
    def add_message(self, content):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.messages.append({
            'content': content,
            'timestamp': timestamp
        })
        return self.get_messages()
    
    def get_messages(self):
        return self.messages

def create_html(messages):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f0f0f0;
            }
            .message {
                background-color: white;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .timestamp {
                color: #666;
                font-size: 0.8em;
            }
        </style>
    </head>
    <body>
        <h2>Message Display Test</h2>
        <div id="messages">
    """
    
    for msg in messages:
        html += f"""
            <div class="message">
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
        api = Api()
        window = webview.create_window(
            'WebView Test',
            html=create_html([]),
            js_api=api,
            width=800,
            height=600,
            min_size=(400, 300)
        )
        
        def update_content():
            time.sleep(2)  # Wait for window to load
            api.add_message("Test message 1")
            window.set_html(create_html(api.get_messages()))
            time.sleep(2)
            api.add_message("Test message 2")
            window.set_html(create_html(api.get_messages()))
        
        t = threading.Thread(target=update_content)
        t.daemon = True
        t.start()
        
        webview.start(debug=True)
        
    except Exception as e:
        logging.exception("An error occurred while creating the WebView window")
        sys.exit(1)

if __name__ == '__main__':
    main()