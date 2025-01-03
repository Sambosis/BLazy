Create an interactive website for code analysis visualization that allows users to:
1. Upload Python files
2. View function relationships and dependencies
3. Search through code semantically
4. Visualize function call graphs

Please follow these specific steps:

1. First, create a complete directory structure at"C:\repo\testsite" and set up a Python virtual environment.  You will be working in Microsoft Windows. So use the appropriate commands for Windows including powershell.  
- Also, make sure that the paths you use are complete paths including the drive letter. which will be C:\
- Show exact commands for creating and activating venv
- Include a requirements.txt file with all necessary dependencies
- Show pip install commands

2. Create a Flask-based website with the following features:
- A modern, responsive interface using Bootstrap
- A split-pane layout with file tree on left, visualization on right
- File upload functionality
- Code syntax highlighting
- Interactive visualization using D3.js for function relationships
- Search functionality that works across uploaded files

3. Implement these specific endpoints:
- /upload for file handling
- /analyze for code analysis
- /search for code search
- /visualize for generating graphs
- /api/functions for getting function details

4. Include complete error handling and user feedback

5. Write the complete code for:
- All HTML templates
- All JavaScript files
- All Python routes and logic
- All CSS styling
- All utility functions for code analysis

6. Provide specific testing instructions:
- How to start the server
- How to upload test files
- How to verify each feature
- Expected behavior for each interaction

7. Include detailed comments in all code files explaining functionality

8. Show the exact commands to:
- Run the application
- Test all features
- Verify the visualization is working
- Confirm search functionality

The final application should be fully functional locally and demonstrate proper separation of concerns, error handling, and user experience design.

Please provide all code files, setup instructions, and testing steps in a clear, organized manner.
Remember to ask for expert opinions and provide full details to the expert about the commands you have tried. 
It may be helpful to create and run some python scripts to create files directories etc.  You can also write powershell scripts to do some actions if you need to.
