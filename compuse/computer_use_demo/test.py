import time
import shlex
import re
import asyncio  
## run.py
import os
"""Utility to run shell commands asynchronously with a timeout."""
from icecream import ic
import asyncio
# configure ic to include the filename and line number
ic.configureOutput(includeContext=True, contextAbsPath=True)
TRUNCATED_MESSAGE: str = "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file the line numbers of what you are looking for. Remember to use you are working in Windows.</NOTE>"
MAX_RESPONSE_LEN: int = 16000


def maybe_truncate(content: str, truncate_after: int | None = MAX_RESPONSE_LEN):
    """Truncate content and append a notice if content exceeds the specified length."""
    return (
        content
        if not truncate_after or len(content) <= truncate_after
        else content[:truncate_after] + TRUNCATED_MESSAGE
    )

"""Run a shell command asynchronously with a timeout."""
async def run(cmd: str,
    timeout: float | None = 120.0,  # seconds
    truncate_after: int | None = MAX_RESPONSE_LEN,
):
    process = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return (
            process.returncode or 0,
            maybe_truncate(stdout.decode(), truncate_after=truncate_after),
            maybe_truncate(stderr.decode(), truncate_after=truncate_after),
        )
    except asyncio.TimeoutError as exc:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        raise TimeoutError(
            f"Command '{cmd}' timed out after {timeout} seconds"
        ) from exc

def convert_bash_to_powershell(bash_command: str) -> str:
    """
    Convert a Bash command to its PowerShell equivalent.

    Args:
        bash_command (str): The Bash command as a string.

    Returns:
        str: The equivalent PowerShell command.

    Raises:
        ValueError: If the command or flags are unsupported.
    """
    command_map = {
        'ls': 'Get-ChildItem',
        'pwd': 'Get-Location',
        'cd': 'Set-Location',
        'cp': 'Copy-Item',
        'mv': 'Move-Item',
        'rm': 'Remove-Item',
        'cat': 'Get-Content',
        'echo': 'Write-Output',
        'mkdir': 'New-Item -ItemType Directory',
        'touch': 'New-Item -ItemType File -Force',
        'grep': 'Select-String',
        'find': 'Get-ChildItem',
    }

    flag_map = {
        'ls': {
            '-l': '',
            '-a': '-Force',
            '-la': '-Force',
            '-al': '-Force',
            '-R': '-Recurse',
            '-r': '-Recurse',
        },
        'rm': {
            '-r': '-Recurse',
            '-f': '-Force',
            '-rf': '-Recurse -Force',
            '-fr': '-Recurse -Force',
        },
        'cp': {
            '-r': '-Recurse',
            '-R': '-Recurse',
            '-f': '-Force',
        },
        'grep': {
            '-i': '-CaseSensitive:$false',
            '-v': '-NotMatch',
            '-r': '-Recurse',
            '-n': '',
        },
        'find': {
            '-name': '-Filter',
            '-iname': '-Filter',
            '-type': '',
        },
    }

    def translate_path(path: str) -> str:
        """Translate Unix-style paths to Windows-style paths."""
        if path.startswith('~'):
            path = path.replace('~', '$env:USERPROFILE')
        path = re.sub(r'\$(?!env:)(\w+)', r'$env:\1', path)  # Avoid double $env:
        path = path.replace('/', '\\')
        if re.match(r'^\\', path):
            path = 'C:' + path
        return f"'{path}'"

    def verify_path(path: str) -> str:
        """Verify if the translated path exists."""
        path = path.strip("'")
        if not os.path.exists(path):
            raise ValueError(f"Path '{path}' does not exist.")
        return path

    parts = shlex.split(bash_command)
    if not parts:
        raise ValueError("Empty command provided.")

    command = parts[0]
    args = parts[1:]

    if command not in command_map:
        raise ValueError(f"Unsupported command: '{command}'.")

    ps_command = command_map[command]
    ps_args = []

    if command == 'grep':
        # Handle grep specifically
        flags = []
        search_term = None
        file_path = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if arg in flag_map[command]:
                    flags.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            elif search_term is None:
                search_term = arg
            elif file_path is None:
                file_path = translate_path(arg)
            else:
                raise ValueError(f"Unexpected argument '{arg}' for command 'grep'.")
            i += 1

        if not search_term:
            raise ValueError("Missing search term for 'grep'.")
        if not file_path:
            raise ValueError("Missing file path for 'grep'.")

        ps_args.append(f"-Pattern {search_term}")
        ps_args.append(f"-Path {file_path}")
        ps_args.extend(flags)

    elif command == 'find':
        # Handle find specifically
        base_path = None
        flags = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if arg == '-type':
                    i += 1
                    if i < len(args):
                        type_arg = args[i]
                        if type_arg == 'f':
                            flags.append('| Where-Object { -not $_.PSIsContainer }')
                        elif type_arg == 'd':
                            flags.append('| Where-Object { $_.PSIsContainer }')
                        else:
                            raise ValueError(f"Unsupported type '{type_arg}' for '-type'.")
                    else:
                        raise ValueError("Expected type after '-type'.")
                elif arg in ['-name', '-iname']:
                    i += 1
                    if i < len(args):
                        name_arg = args[i]
                        flags.append(f"| Where-Object {{ $_.Name -like '{name_arg}' }}")
                    else:
                        raise ValueError(f"Expected pattern after '{arg}'.")
                elif arg in flag_map[command]:
                    flags.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            elif base_path is None:
                base_path = translate_path(arg)
            else:
                raise ValueError(f"Unexpected argument '{arg}' for command 'find'.")
            i += 1

        if not base_path:
            raise ValueError("Missing base path for 'find'.")

        ps_args.append(f"-Path {base_path}")
        ps_args.extend(flags)

    elif command == 'echo':
        ps_args.append(f"'{ ' '.join(args) }'")

    elif command == 'rm':
        ps_args.append('-ErrorAction SilentlyContinue')
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if command in flag_map and arg in flag_map[command]:
                    ps_args.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            else:
                ps_args.append(translate_path(arg))
            i += 1

    else:
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if command in flag_map and arg in flag_map[command]:
                    ps_args.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            else:
                ps_args.append(translate_path(arg))
            i += 1

    return f"{ps_command} {' '.join(ps_args)}"

bash_commands = [
    'ls -la /repo',
    'grep -i "Determine" ~/computer_use_demo/debug_log.json',
    'rm -rf /tmp/test',
    'find /var/log -type f -name "*.log"',
    'echo "Hello, World!"',
]

async def main():
    for bash_command in bash_commands:
        try:
            ps_command = convert_bash_to_powershell(bash_command)
            full_command = f'powershell -NoProfile -Command "{ps_command}"'

            print(f"Bash Command: {bash_command}")
            print(f"PowerShell Command: {ps_command}")
            print(f"Full Command: {full_command}")

            returncode, stdout, stderr = await run(full_command)

            print(f"Return Code: {returncode}")
            print("Standard Output:")
            print(stdout)
            print("Standard Error:")
            print(stderr)
            print("-" * 60)
        except ValueError as e:
            print(f"Error: {e}")
            print("-" * 60)

asyncio.run(main())
# async def main():
#     for bash_command in bash_commands:
#         try:
#             ic(bash_command)
#             ps_command = convert_bash_to_powershell(bash_command)
#             print(f"Bash Command: {bash_command}")
#             ic()
#             print(f"PowerShell Command: {ps_command}")
#             full_command = f'powershell -NoProfile -Command "{ps_command}"'
#             print(f"Full Command: {full_command}")
#             returncode, stdout, stderr = await run(full_command)
#             ic()
#             print(f"Return Code: {returncode}")
#             print("Standard Output:")
#             print(stdout)
#             print("Standard Error:")
#             print(stderr)
#             print("-" * 60)
#         except ValueError as e:
#             print(f"Error: {e}")
#             print("-" * 60)

# asyncio.run(main())