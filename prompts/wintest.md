Create a Python system to analyze Excel files using AI with the following requirements:
Core Features:
Load and parse Excel files using pandas and openpyxl
Extract tables, named ranges, and relationships between sheets
Convert numerical data into descriptive summaries
Store processed data in both SQLite and vector databases
Specific Components:
Create a TableExtractor class to identify and extract table structures
Implement a DataNormalizer class for cleaning and standardizing data
Build a VectorStorage class using ChromaDB for semantic search
Develop a SQLStorage class for structured querying
Create an AIAnalyzer class to interface with LLMs
Implementation Steps:
Process the file 'C:\\Users\\Machine81\\OneDrive\\Documents\\650 2025 Budget ollld.xlsx'
Work in directory 'c:\\repo\\xl'
Generate metadata about sheets, tables, and relationships
Store both raw and processed data
Create natural language descriptions of data patterns
Analysis Capabilities:
Detect data types and relationships automatically
Generate summary statistics and insights
Enable natural language queries about the data
Support visualization requests
Track data lineage and transformations
Output Requirements:
Store results in both JSON and database formats
Generate analysis reports in markdown
Create visualization-ready datasets
Maintain an audit trail of transformations
Please provide a modular implementation with error handling and logging."
This improved prompt:
Is more structured and specific
Breaks down the requirements into clear components
Specifies exact file paths and locations
Includes concrete deliverables
Addresses both storage and analysis needs
Focuses on practical implementation details