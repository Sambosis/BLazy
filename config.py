from pathlib import Path

# Define the top-level directory
TOP_LEVEL_DIR = Path.cwd()

# Define the repository directory
REPO_DIR = TOP_LEVEL_DIR / 'repo'

# Define other relevant paths
JOURNAL_DIR = TOP_LEVEL_DIR / 'journal'
JOURNAL_FILE = JOURNAL_DIR / 'journal.log'
JOURNAL_ARCHIVE_FILE = JOURNAL_DIR / 'journal_archive.log'
JOURNAL_SYSTEM_PROMPT_FILE = JOURNAL_DIR / 'journal_system_prompt.md'
SYSTEM_PROMPT_DIR = TOP_LEVEL_DIR / 'system_prompt'
SYSTEM_PROMPT_FILE = SYSTEM_PROMPT_DIR / 'system_prompt.md'
LLM_GEN_CODE_DIR = REPO_DIR / 'llm_gen_code'
TOOLS_DIR = REPO_DIR / 'tools'
SCRIPTS_DIR = REPO_DIR / 'scripts'
TESTS_DIR = REPO_DIR / 'tests'
