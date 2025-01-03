# #playtest.py
from playwright.sync_api import sync_playwright

def continue_with_saved_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Create context with saved state
        context = browser.new_context(storage_state=r"C:\mygit\compuse\computer_use_demo\state.json")
        page = context.new_page()
        
        # Navigate to page (state will be preserved)
        page.goto('https://www.autochlor.net/wps')
        
        # Verify state is loaded
        cookies = context.cookies()
        local_storage = page.evaluate("""() => {
            return Object.entries(localStorage);
        }""")
        
        print("Current cookies:", cookies)
        print("Current local storage:", local_storage)
        input("Press Enter to continue...")
        browser.close()

# Usage
continue_with_saved_state()


# from httpx import head
# from playwright.sync_api import sync_playwright
# import json

# def setup_browser_state():
#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch()
#             context = browser.new_context()
#             page = context.new_page()
            
#             # Set various states
#             # Local Storage
#             page.evaluate("""() => {
#                 localStorage.setItem('user', 'sparker');
#                 # localStorage.setItem('theme', 'dark');
#             }""")
            
#             # Cookies
#             context.add_cookies([
#                 {
#                     'name': 'session',
#                     'value': 'abc123',
#                     'url': 'https://www.autochlor.net/wps'
#                 },
#                 # {
#                 #     'name': 'preferences',
#                 #     'value': 'dark-mode',
#                 #     'url': 'https://your-url.com'
#                 # }
#             ])
            
#             # Save state for future use
#             context.storage_state(path="saved_state.json")
            
#             # Verify state
#             cookies = context.cookies()
#             local_storage = page.evaluate("""() => {
#                 return Object.entries(localStorage);
#             }""")
            
#             print("State setup completed successfully")
#             print(f"Cookies: {json.dumps(cookies, indent=2)}")
#             print(f"Local Storage: {local_storage}")
            
#             browser.close()
#             return True
            
#     except Exception as e:
#         print(f"Error setting up browser state: {str(e)}")
#         return False

# # Usage
# if __name__ == "__main__":
#     success = setup_browser_state()
#     if success:
#         print("Browser state setup successful")
#     else:
#         print("Browser state setup failed")


#         from playwright.sync_api import sync_playwright

# with sync_playwright() as p:
#     browser = p.chromium.launch(headless=False)
    
#     # Create a context and do some actions
#     context = browser.new_context()
#     page = context.new_page()
#     page.goto('https://www.autochlor.net/wps')
#     # page.fill('input[name="username"]', 'myuser')

#     # wait for the user to log in and move to the next page then save the state
#     input("Press Enter to continue...")
    
    
#     # Save the state to a file
#     context.storage_state(path="state.json")
    
#     # Create a new context with saved state
#     new_context = browser.new_context(storage_state="state.json")
#     new_page = new_context.new_page()
    
#     # browser.close()