# PowerShell script to execute a Python script located at C:/repo/dog.py

# Define the path to the Python script
$pythonScriptPath = "C:/repo/dog.py"

# Check if the Python script file exists
if (Test-Path $pythonScriptPath) {
    try {
        # Execute the Python script using the Python interpreter
        python $pythonScriptPath
    } catch {
        # Error handling if the execution fails
        Write-Host "An error occurred while executing the Python script:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
} else {
    # Error handling if the file does not exist
    Write-Host "Error: The specified Python script file does not exist at the path: $pythonScriptPath" -ForegroundColor Red
}