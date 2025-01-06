import os
import pathlib

# Define the base directory
base_dir = pathlib.Path(r'C:\repo\remi')

# Create the directories
directories = [
    base_dir / 'components',
    base_dir / 'static', 
    base_dir / 'uploads'
]

# Create directories with error handling
for directory in directories:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    except PermissionError:
        print(f"Permission denied when creating directory: {directory}")
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")

# Perform ls -la equivalent
print("\nDirectory contents:")
try:
    for item in base_dir.iterdir():
        stats = item.stat()
        print(f"{item.name:<20} {'Directory' if item.is_dir() else 'File'}")
except Exception as e:
    print(f"Error listing directory contents: {e}")