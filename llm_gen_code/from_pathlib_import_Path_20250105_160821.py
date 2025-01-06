from pathlib import Path

# Define the base directory
base_dir = Path(r'C:\repo\testsite2')

# Create directories
directories = [
    'static',
    'templates', 
    'static/css', 
    'static/js', 
    'static/images',
    'utils'
]

# Create files
files = [
    'requirements.txt',
    'app.py',
    'README.md'
]

# Create directories
for dir_path in directories:
    full_path = base_dir / dir_path
    try:
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    except Exception as e:
        print(f"Error creating directory {full_path}: {e}")

# Create files
for file_name in files:
    full_path = base_dir / file_name
    try:
        full_path.touch()
        print(f"Created file: {full_path}")
    except Exception as e:
        print(f"Error creating file {full_path}: {e}")