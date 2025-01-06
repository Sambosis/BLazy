from pathlib import Path
import os

# Change to the specified directory
base_dir = Path(r'C:\repo\remi')
os.chdir(base_dir)

# Function to find files with specific extensions
def find_files(directory, extensions):
    """
    Recursively find files with specified extensions in the given directory.
    
    Args:
        directory (Path): Base directory to start search
        extensions (list): List of file extensions to find
    
    Returns:
        list: Paths of matching files
    """
    matching_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                # Check if file ends with any of the specified extensions
                if any(file.endswith(ext) for ext in extensions):
                    full_path = Path(root) / file
                    matching_files.append(str(full_path.relative_to(directory)))
        return matching_files
    except Exception as e:
        print(f"Error searching files: {e}")
        return []

# Find Python and CSS files
found_files = find_files(base_dir, ['.py', '.css'])

# Print found files
for file in found_files:
    print(file)