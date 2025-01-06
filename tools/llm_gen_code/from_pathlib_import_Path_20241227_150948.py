from pathlib import Path

# Define the full absolute path for the directory
directory = Path(r"C:\repo\algebra-game\notes")

# Create the directory and any missing parent directories
try:
    # Use mkdir with parents=True to create nested directories
    directory.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {directory}")
except PermissionError:
    print(f"Permission denied when creating directory: {directory}")
except Exception as e:
    print(f"Error creating directory: {e}")