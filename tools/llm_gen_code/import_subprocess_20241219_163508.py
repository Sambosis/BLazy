import subprocess
import sys

def run_pip_command(command_type, packages):
    """
    Run pip commands to uninstall or install packages
    
    Args:
        command_type (str): 'uninstall' or 'install'
        packages (list): List of package names to process
    """
    try:
        # Construct the base pip command
        base_cmd = [sys.executable, '-m', 'pip', command_type]
        
        # Add yes flag for uninstall
        if command_type == 'uninstall':
            base_cmd.append('-y')
        
        # Add packages to the command
        base_cmd.extend(packages)
        
        # Execute the pip command
        result = subprocess.run(base_cmd, capture_output=True, text=True)
        
        # Print output for logging/debugging
        if result.stdout:
            print(f"{command_type.capitalize()} stdout:", result.stdout)
        
        if result.stderr:
            print(f"{command_type.capitalize()} stderr:", result.stderr)
        
        # Check for successful execution
        if result.returncode != 0:
            print(f"Warning: {command_type} command may have encountered issues")
    
    except Exception as e:
        print(f"Error during {command_type} operation: {e}")

# Uninstall packages
uninstall_packages = ['numpy', 'pandas', 'openpyxl']
run_pip_command('uninstall', uninstall_packages)

# Install packages (with numpy version constraint)
install_packages = ['numpy<2.0', 'pandas', 'openpyxl']
run_pip_command('install', install_packages)