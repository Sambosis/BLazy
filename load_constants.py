from dotenv import load_dotenv
from pathlib import Path
import os

# Get the directory where this script is located

# Load environment variables
load_dotenv()

# Constants
MAX_SUMMARY_MESSAGES = 18
MAX_SUMMARY_TOKENS = 6000
ICECREAM_OUTPUT_FILE =  Path("debug_log.json")
JOURNAL_DIR = Path("journal")
JOURNAL_FILE = JOURNAL_DIR / "journal.log"
JOURNAL_ARCHIVE_FILE = JOURNAL_DIR / "journal_archive.log"
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
JOURNAL_MODEL = "claude-3-5-haiku-latest"
SUMMARY_MODEL = "claude-3-5-haiku-latest"
JOURNAL_MAX_TOKENS = 4000
MAIN_MODEL = "claude-3-5-sonnet-latest"
JOURNAL_SYSTEM_PROMPT_FILE = JOURNAL_DIR / "journal_system_prompt.md"
SYSTEM_PROMPT_DIR = Path(".")
SYSTEM_PROMPT_FILE = SYSTEM_PROMPT_DIR / "system_prompt.md"

# Add JOURNAL_SYSTEM_PROMPT and SYSTEM_PROMPT constants
JOURNAL_SYSTEM_PROMPT = ""
SYSTEM_PROMPT = ""

# Create necessary directories
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
print(f"Journal directory: {JOURNAL_DIR}")
print(f"debug_log.json: {ICECREAM_OUTPUT_FILE}")
# Load journal system prompt
try:
    with open(JOURNAL_SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
        JOURNAL_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    JOURNAL_SYSTEM_PROMPT = ""
    print(f"Warning: Journal system prompt file not found at {JOURNAL_SYSTEM_PROMPT_FILE}")

# Load system prompt
try:
    with open(SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = ""
    print(f"Warning: System prompt file not found at {SYSTEM_PROMPT_FILE}")

# Add reload_prompts function to reload system prompts
def reload_prompts():
    global SYSTEM_PROMPT
    global JOURNAL_SYSTEM_PROMPT
    try:
        with open(SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
            SYSTEM_PROMPT = f.read()
    except FileNotFoundError:
        print(f"Warning: System prompt file not found at {SYSTEM_PROMPT_FILE}")
    try:
        with open(JOURNAL_SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
            JOURNAL_SYSTEM_PROMPT = f.read()
    except FileNotFoundError:
        print(f"Warning: Journal system prompt file not found at {JOURNAL_SYSTEM_PROMPT_FILE}")

