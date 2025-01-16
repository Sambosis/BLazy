from dotenv import load_dotenv
from pathlib import Path
import os
from icecream import ic
from datetime import datetime
import json
# from utils.output_manager import OutputManager
from config import TOP_LEVEL_DIR, REPO_DIR, JOURNAL_DIR, JOURNAL_FILE, JOURNAL_ARCHIVE_FILE, JOURNAL_SYSTEM_PROMPT_FILE, SYSTEM_PROMPT_DIR, SYSTEM_PROMPT_FILE, SCRIPTS_DIR, TESTS_DIR

# Get the directory where this script is located

# Load environment variables with error handling
try:
    load_dotenv()
except Exception as e:
    print(f"Error loading environment variables: {e}")

# Constants
MAX_SUMMARY_MESSAGES = 20
MAX_SUMMARY_TOKENS = 6000
WORKER_DIR = TOP_LEVEL_DIR
ICECREAM_OUTPUT_FILE =  WORKER_DIR / "debug_log.json"
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
JOURNAL_MODEL = "claude-3-5-haiku-latest"
SUMMARY_MODEL = "claude-3-5-haiku-latest"
JOURNAL_MAX_TOKENS = 4000
MAIN_MODEL = "claude-3-5-sonnet-latest"
# Add near the top with other Path definitions
PROJECT_DIR = TOP_LEVEL_DIR  # Default value

global PROMPT_NAME
PROMPT_NAME = None

HOME = Path.home()
def update_project_dir(new_dir):
    global PROJECT_DIR
    PROJECT_DIR = new_dir


# Create necessary directories
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

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


def write_to_file(s: str, file_path: str = ICECREAM_OUTPUT_FILE):
    """Write debug output to a file, formatting JSON content in a pretty way."""
    lines = s.split('\n')
    formatted_lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    for line in lines:
        if "tool_input:" in line:
            try:
                # Extract JSON part from the line
                json_part = line.split("tool_input: ")[1]
                 # check if it looks like a json object
                if json_part.strip().startswith('{') and json_part.strip().endswith('}'):
                    # Parse and pretty-print the JSON
                    json_obj = json.loads(json_part)
                    pretty_json = json.dumps(json_obj, indent=4)
                    formatted_lines.append(f" tool_input: " + pretty_json)
                else:
                   formatted_lines.append(line)
            except (IndexError, json.JSONDecodeError):
                # If parsing fails, just append the original line
                formatted_lines.append( line)
        else:
            formatted_lines.append(line)
    with open(file_path, 'a', encoding="utf-8") as f:
        f.write(f"{timestamp} ")
        f.write('\n'.join(formatted_lines))
        f.write('\n' + '-' * 80 + '\n')
ic.configureOutput(includeContext=True, outputFunction=write_to_file)

def get_workspace_dir():
    return HOME / f"{PROMPT_NAME}/workspace"

def get_logs_dir():
    return HOME / f"{PROMPT_NAME}/logs"

def update_paths(new_prompt_name):
    logs_dir = get_logs_dir()
    global PROMPT_NAME
    PROMPT_NAME = new_prompt_name
    return {
        'ICECREAM_OUTPUT_FILE': logs_dir / "debug_log.json",
        'JOURNAL_FILE': logs_dir / "journal/journal.log",
        'JOURNAL_ARCHIVE_FILE': logs_dir / "journal/journal.log.archive",
        'SUMMARY_FILE': logs_dir / "summaries/summary.md",
        'SYSTEM_PROMPT_FILE': logs_dir / "prompts/system_prompt.md",
        'JOURNAL_SYSTEM_PROMPT_FILE': logs_dir / "prompts/journal_prompt.md"
    }

def load_system_prompts():
    paths = update_paths()
    with open(paths['SYSTEM_PROMPT_FILE'], 'r', encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
    with open(paths['JOURNAL_SYSTEM_PROMPT_FILE'], 'r', encoding="utf-8") as f:
        JOURNAL_SYSTEM_PROMPT = f.read()
    return SYSTEM_PROMPT, JOURNAL_SYSTEM_PROMPT

# output_manager = OutputManager()
