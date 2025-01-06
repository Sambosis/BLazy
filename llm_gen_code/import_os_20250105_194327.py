import os
from pathlib import Path

# Define the base directory
base_dir = Path("C:/repo/testsite2")

# Create static subdirectories
static_subdirs = ['css', 'js', 'images', 'uploads']
static_base = base_dir / "app" / "static"
for subdir in static_subdirs:
    try:
        (static_base / subdir).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {static_base / subdir}")
    except PermissionError:
        print(f"Warning: Could not create directory {static_base / subdir}. Check permissions.")

# Create app-level directories
app_subdirs = ['templates', 'models', 'utils']
app_base = base_dir / "app"
for subdir in app_subdirs:
    try:
        (app_base / subdir).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {app_base / subdir}")
    except PermissionError:
        print(f"Warning: Could not create directory {app_base / subdir}. Check permissions.")

# Create tests directory
try:
    (base_dir / "tests").mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {base_dir / 'tests'}")
except PermissionError:
    print(f"Warning: Could not create directory {base_dir / 'tests'}. Check permissions.")

# Create virtual environment
try:
    import venv
    venv_path = base_dir / "venv"
    venv.create(venv_path, with_pip=True)
    print(f"Created virtual environment in {venv_path}")
except Exception as e:
    print(f"Error creating virtual environment: {e}")