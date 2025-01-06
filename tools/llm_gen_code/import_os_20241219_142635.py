import os
import pathlib
import subprocess

# Change to the specified directory
os.chdir('C:/repo')

# Create directory with parents if not exists
pathlib.Path('C:/repo/remi/static').mkdir(parents=True, exist_ok=True)

# Install packages using pip
try:
    subprocess.run(['pip', 'install', 'remi', 'pandas', 'plotly'], 
                   check=True, 
                   capture_output=True, 
                   text=True)
    print("Successfully installed remi, pandas, and plotly")
except subprocess.CalledProcessError as e:
    print(f"Error installing packages: {e.stderr}")