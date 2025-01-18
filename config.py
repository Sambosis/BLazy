from pathlib import Path
import json

global PROJECT_DIR
PROJECT_DIR = None
# Define the top-level directory
TOP_LEVEL_DIR = Path.cwd()

# Define the repository directory based on PROJECT_DIR
REPO_DIR = TOP_LEVEL_DIR / 'repo'  # Changed from TOP_LEVEL_DIR / 'repo'

# Define other relevant paths based on PROJECT_DIR
JOURNAL_DIR = TOP_LEVEL_DIR / 'journal'
JOURNAL_FILE = JOURNAL_DIR / 'journal.log'
JOURNAL_ARCHIVE_FILE = JOURNAL_DIR / 'journal_archive.log'
JOURNAL_SYSTEM_PROMPT_FILE = JOURNAL_DIR / 'journal_system_prompt.md'
SYSTEM_PROMPT_DIR = TOP_LEVEL_DIR / 'system_prompt'
SYSTEM_PROMPT_FILE = SYSTEM_PROMPT_DIR / 'system_prompt.md'
BASH_PROMPT_DIR = TOP_LEVEL_DIR / 'tools'
BASH_PROMPT_FILE = BASH_PROMPT_DIR / 'bash.md'
LLM_GEN_CODE_DIR = TOP_LEVEL_DIR / 'llm_gen_code'
TOOLS_DIR = TOP_LEVEL_DIR / 'tools'
SCRIPTS_DIR = TOP_LEVEL_DIR / 'scripts'
TESTS_DIR = TOP_LEVEL_DIR / 'tests'
LOGS_DIR = TOP_LEVEL_DIR / 'logs'  # Ensure LOGS_DIR is based on PROJECT_DIR
PROMPTS_DIR = TOP_LEVEL_DIR / 'prompts'

JOURNAL_MODEL = "claude-3-5-haiku-latest"
SUMMARY_MODEL = "claude-3-5-haiku-latest"
MAIN_MODEL = "claude-3-5-sonnet-latest"
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

JOURNAL_MAX_TOKENS = 1500
MAX_SUMMARY_MESSAGES = 40
MAX_SUMMARY_TOKENS = 8000

# create a cache directory if it does not exist
CACHE_DIR = TOP_LEVEL_DIR / 'cache'  # Changed from TOP_LEVEL_DIR / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# function to write the constants to a file
def write_constants_to_file():
    constants = {
        'TOP_LEVEL_DIR': str(TOP_LEVEL_DIR),
        'REPO_DIR': str(REPO_DIR),
        'JOURNAL_DIR': str(JOURNAL_DIR),
        'JOURNAL_FILE': str(JOURNAL_FILE),
        'JOURNAL_ARCHIVE_FILE': str(JOURNAL_ARCHIVE_FILE),
        'JOURNAL_SYSTEM_PROMPT_FILE': str(JOURNAL_SYSTEM_PROMPT_FILE),
        'SYSTEM_PROMPT_DIR': str(SYSTEM_PROMPT_DIR),
        'SYSTEM_PROMPT_FILE': str(SYSTEM_PROMPT_FILE),
        'BASH_PROMPT_DIR': str(BASH_PROMPT_DIR),
        'BASH_PROMPT_FILE': str(BASH_PROMPT_FILE),
        'LLM_GEN_CODE_DIR': str(LLM_GEN_CODE_DIR),
        'TOOLS_DIR': str(TOOLS_DIR),
        'SCRIPTS_DIR': str(SCRIPTS_DIR),
        'TESTS_DIR': str(TESTS_DIR),
        'JOURNAL_MODEL': JOURNAL_MODEL,
        'SUMMARY_MODEL': SUMMARY_MODEL,
        'MAIN_MODEL': MAIN_MODEL,
        'COMPUTER_USE_BETA_FLAG': COMPUTER_USE_BETA_FLAG,
        'PROMPT_CACHING_BETA_FLAG': PROMPT_CACHING_BETA_FLAG,
        'JOURNAL_MAX_TOKENS': JOURNAL_MAX_TOKENS,
        'MAX_SUMMARY_MESSAGES': MAX_SUMMARY_MESSAGES,
        'MAX_SUMMARY_TOKENS': MAX_SUMMARY_TOKENS,
        'LOGS_DIR': str(LOGS_DIR),
        'PROJECT_DIR': str(PROJECT_DIR) if PROJECT_DIR else "",
        'PROMPTS_DIR': str(PROMPTS_DIR),
    }
    with open(CACHE_DIR / 'constants.json', 'w') as f:
        json.dump(constants, f, indent=4)

def get_constants():
    with open(CACHE_DIR / 'constants.json', 'r') as f:
        constants = json.load(f)
    return constants

# function to load the constants from a file
def load_constants():
    try:
        with open(CACHE_DIR / 'constants.json', 'r') as f:
            constants = json.load(f)
        return constants
    except FileNotFoundError:
        return None

# get a constant by name
def get_constant(name):
    write_constants_to_file()
    constants = load_constants()
    if constants:
        return_constant = constants.get(name)
        # if return_constant contains PATH, DIR or FILE then return as Path
        if return_constant and ('PATH' in return_constant or 'DIR' in return_constant or 'FILE' in return_constant):
            return Path(return_constant)
        else:
            return(return_constant)
    else:
        return None

# function to set a constant
def set_constant(name, value):
    constants = load_constants()
    if constants:
        # Convert Path objects to strings for JSON serialization
        if isinstance(value, Path):
            constants[name] = str(value)
        else:
            constants[name] = value
        with open(CACHE_DIR / 'constants.json', 'w') as f:
            json.dump(constants, f, indent=4)
            return True
    else:
        return False

# function to set the project directory
def set_project_dir(new_dir):
    global PROJECT_DIR
    PROJECT_DIR = REPO_DIR / new_dir
    set_constant('PROJECT_DIR', str(PROJECT_DIR))
    return PROJECT_DIR

# function to get the project directory
def get_project_dir():
    return PROJECT_DIR
