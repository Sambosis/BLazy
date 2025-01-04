from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Set
from pathlib import Path
import pandas as pd
import ast
from dataclasses import dataclass
import networkx as nx
import importlib
import importlib.metadata
import importlib.util
import os
import sys
from rich import print as rr
from importlib.metadata import distributions, version, PackageNotFoundError
from tqdm import tqdm
def get_stdlib_modules() -> Set[str]:
    """Get a set of standard library module names"""
    stdlib_paths = {
        os.path.dirname(os.__file__),  # Standard library path
        os.path.dirname(importlib.__file__),  # Additional standard library path
    }
    
    stdlib_modules = set()
    for path in stdlib_paths:
        if os.path.exists(path):
            for item in os.listdir(path):
                name, ext = os.path.splitext(item)
                if ext in {'.py', '.pyc'}:
                    stdlib_modules.add(name)
    
    return stdlib_modules

class DependencyInfo(BaseModel):
    name: str
    version: Optional[str] = None
    is_standard_lib: bool = False
    is_local: bool = False

    @classmethod
    def from_import(cls, module_name: str, code_root: Path) -> "DependencyInfo":
        """Create DependencyInfo from a module name"""
        root_module = module_name.split('.')[0]
        
        # Check if its a standard library module
        if root_module in get_stdlib_modules():
            return cls(
                name=root_module,
                is_standard_lib=True
            )
        
        # Check if its a local module
        local_module_path = code_root / f"{root_module}.py"
        if local_module_path.exists():
            return cls(
                name=root_module,
                is_local=True
            )
        
        # Must be an external dependency
        try:
            dep_version = version(root_module)
            return cls(
                name=root_module,
                version=dep_version
            )
        except PackageNotFoundError:
            return cls(name=root_module)


class ArgumentInfo(BaseModel):
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None

class MethodInfo(BaseModel):
    name: str
    code: str
    docstring: Optional[str] = None
    args: List[ArgumentInfo] = Field(default_factory=list)
    return_annotation: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False

class ClassInfo(BaseModel):
    name: str
    code: str
    docstring: Optional[str] = None
    methods: List[MethodInfo] = Field(default_factory=list)
    base_classes: List[str] = Field(default_factory=list)
    filepath: str
    class_variables: Dict[str, Optional[str]] = Field(default_factory=dict)

    def _is_special_method(self, decorator_list: List[str]) -> tuple:
        """Determine if method has special decorators"""
        is_property = any(d for d in decorator_list if isinstance(d, str) and "property" in d)
        is_classmethod = any(d for d in decorator_list if isinstance(d, str) and "classmethod" in d)
        is_staticmethod = any(d for d in decorator_list if isinstance(d, str) and "staticmethod" in d)
        return is_property, is_classmethod, is_staticmethod

    def _extract_class_info(self, node: ast.ClassDef, content: str, filepath: str) -> "ClassInfo":
        """Extract information about a class"""
        methods = []
        class_variables = {}
        
        # Get base classes
        base_classes = [ast.unparse(base) for base in node.bases]
        
        for body_item in node.body:
            if isinstance(body_item, ast.FunctionDef):
                method_code = ast.unparse(body_item)
                decorators = self._extract_decorators(body_item)
                is_property = any("property" in d for d in decorators)
                is_classmethod = any("classmethod" in d for d in decorators)
                is_staticmethod = any("staticmethod" in d for d in decorators)
                
                # Parse arguments
                args = []
                for i, arg in enumerate(body_item.args.args[1:] if not is_staticmethod else body_item.args.args):
                    default = body_item.args.defaults[i] if i < len(body_item.args.defaults) else None
                    args.append(self._parse_argument(arg, default))

                methods.append(MethodInfo(
                    name=body_item.name,
                    code=method_code,
                    docstring=ast.get_docstring(body_item),
                    args=args,
                    return_annotation=ast.unparse(body_item.returns) if body_item.returns else None,
                    decorators=decorators,
                    is_property=is_property,
                    is_classmethod=is_classmethod,
                    is_staticmethod=is_staticmethod
                ))
            elif isinstance(body_item, ast.AnnAssign):
                # Class variable with type annotation
                target_str = ast.unparse(body_item.target)
                value = ast.unparse(body_item.value) if body_item.value else None
                class_variables[target_str] = value
            elif isinstance(body_item, ast.Assign):
                # Class variable without type annotation
                for target in body_item.targets:
                    target_str = ast.unparse(target)
                    value = ast.unparse(body_item.value) if body_item.value else None
                    class_variables[target_str] = value

        return ClassInfo(
            name=node.name,
            code=ast.unparse(node),
            docstring=ast.get_docstring(node),
            methods=methods,
            base_classes=base_classes,
            filepath=filepath,
            class_variables=class_variables
        )

class ImportInfo(BaseModel):
    module_name: str
    imported_names: List[str] = Field(default_factory=list)
    is_from_import: bool = False
    alias: Optional[str] = None


class FunctionInfo(BaseModel):
    code: strr
    function_name: str
    filepath: str
    docstring: Optional[str] = None
    args: List[ArgumentInfo] = Field(default_factory=list)
    return_annotation: Optional[str] = None
    decorators: List[str] = Field(default_factory=list)

class FileInfo(BaseModel):
    path: Path
    content: str = ""  # New field to store the full code content
    functions: List[FunctionInfo] = Field(default_factory=list)
    classes: List[ClassInfo] = Field(default_factory=list)
    imports: List[ImportInfo] = Field(default_factory=list)
    dependencies: List[DependencyInfo] = Field(default_factory=list)

class CodeAnalyzer(BaseModel):
    code_root: Path
    def_prefixes: List[str] = Field(default=['def ', 'async def '])
    newline: str = Field(default='\n')
    files: List[FileInfo] = Field(default_factory=list)
    dependency_graph: Optional[nx.DiGraph] = None
    
    class Config:
        arbitrary_types_allowed = True
        
    @classmethod
    def create(cls, code_root: Path) -> "CodeAnalyzer":
        """Factory method to create a CodeAnalyzer instance"""
        return cls(
            code_root=code_root,
            files=[],
            dependency_graph=None
        )

    # Remove the __init__ method and use model_validator instead
    @model_validator(mode='after')
    def initialize_graph(self) -> "CodeAnalyzer":
        """Initialize the dependency graph after model creation"""
        if self.dependency_graph is None:
            self.dependency_graph = nx.DiGraph()
        return self

    def _parse_argument(self, arg: ast.arg, default=None) -> ArgumentInfo:
        """Parse function/method argument information"""
        return ArgumentInfo(
            name=arg.arg,
            type_annotation=ast.unparse(arg.annotation) if arg.annotation else None,
            default_value=ast.unparse(default) if default else None
        )

    def _extract_decorators(self, node: ast.FunctionDef) -> List[str]:
        """Extract decorator information from a function/method node"""
        return [ast.unparse(decorator) for decorator in node.decorator_list]

    def _is_special_method(self, decorator_list: List[str]) -> tuple:
        """Determine if method has special decorators"""
        is_property = any(property in d for d in decorator_list)
        is_classmethod = any(classmethod in d for d in decorator_list)
        is_staticmethod = any(staticmethod in d for d in decorator_list)
        return is_property, is_classmethod, is_staticmethod

    def _extract_imports(self, node: ast.Module) -> List[ImportInfo]:
        """Extract import information from a module"""
        imports = []
        for node_item in node.body:
            if isinstance(node_item, ast.Import):
                for name in node_item.names:
                    imports.append(ImportInfo(
                        module_name=name.name,
                        alias=name.asname,
                        imported_names=[]
                    ))
            elif isinstance(node_item, ast.ImportFrom):
                if node_item.module:
                    imports.append(ImportInfo(
                        module_name=node_item.module,
                        imported_names=[name.name for name in node_item.names],
                        is_from_import=True,
                        alias=None
                    ))
        return imports

    def _analyze_dependencies(self, imports: List[ImportInfo]) -> List[DependencyInfo]:
        """Analyze dependencies from imports"""
        seen_modules = set()
        dependencies = []
        
        for imp in imports:
            module_name = imp.module_name
            if module_name in seen_modules:
                continue
                
            seen_modules.add(module_name)
            dependencies.append(
                DependencyInfo.from_import(module_name, self.code_root)
            )
        
        return dependencies

    def analyze_file(self, filepath: str) -> FileInfo:
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            tree = ast.parse(content)
            
            functions = []
            classes = []
            
            # Extract imports first
            imports = self._extract_imports(tree)
            dependencies = self._analyze_dependencies(imports)
            
            def visit_node(node):
                """Recursively visit nodes to find all functions and methods"""
                if isinstance(node, ast.FunctionDef):
                    functions.append(self._extract_function_info(node, filepath))
                elif isinstance(node, ast.ClassDef):
                    classes.append(self._extract_class_info(node, content, filepath))
                    # Also visit class body for nested functions/classes
                    for item in node.body:
                        visit_node(item)
                elif isinstance(node, ast.Module):
                    for item in node.body:
                        visit_node(item)
                # Handle other node types that might contain functions (like If, With, etc.)
                elif hasattr(node, 'body'):
                    if isinstance(node.body, list):
                        for item in node.body:
                            visit_node(item)
                    else:
                        visit_node(node.body)
                if hasattr(node, 'orelse'):
                    if isinstance(node.orelse, list):
                        for item in node.orelse:
                            visit_node(item)
                    elif node.orelse is not None:
                        visit_node(node.orelse)
                if hasattr(node, 'finalbody'):
                    for item in node.finalbody:
                        visit_node(item)

            # Start the recursive visit
            visit_node(tree)
                
            return FileInfo(
                path=Path(filepath),
                content=content,  # Store the full code content here
                functions=functions,
                classes=classes,
                imports=imports,
                dependencies=dependencies
            )
        except Exception as e:
            print(f"Error parsing file {filepath}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return FileInfo(path=Path(filepath))
    
    def build_dependency_graph(self):
        """Build a dependency graph of the project"""
        self.dependency_graph = nx.DiGraph()
        
        for file_info in self.files:
            file_node = str(file_info.path)
            self.dependency_graph.add_node(file_node)
            
            for dep in file_info.dependencies:
                if dep.is_local:
                    # Add edge for local dependencies
                    dep_file = str(self.code_root / f"{dep.name}.py")
                    self.dependency_graph.add_edge(file_node, dep_file)

    def get_class_hierarchy(self) -> nx.DiGraph:
        """Build and return the class hierarchy graph"""
        hierarchy = nx.DiGraph()
        
        for file_info in self.files:
            for class_info in file_info.classes:
                hierarchy.add_node(class_info.name)
                for base in class_info.base_classes:
                    hierarchy.add_edge(base, class_info.name)
                    
        return hierarchy

    def get_dependency_cycles(self) -> List[List[str]]:
        """Find circular dependencies in the project"""
        if not self.dependency_graph:
            self.build_dependency_graph()
        return list(nx.simple_cycles(self.dependency_graph))

    def to_dataframe(self) -> Dict[str, pd.DataFrame]:
        """Convert the analyzed data to multiple DataFrames"""
        try:
            # Functions DataFrame
            functions_data = [
                {
                'filepath': func.filepath,
                'name': func.function_name,
                'docstring': func.docstring,
                'args': [arg.dict() for arg in func.args],
                'return_annotation': func.return_annotation,
                'decorators': func.decorators
                }
                for file in self.files
                for func in file.functions
            ]
        
            # Classes DataFrame
            classes_data = [
                {
                    'filepath': cls.filepath,
                'name': cls.name,
                'docstring': cls.docstring,
                'methods_count': len(cls.methods),
                'base_classes': cls.base_classes,
                'variables_count': len(cls.class_variables),
                'methods': [method.name for method in cls.methods],
                    'has_docstring': cls.docstring is not None
                }
                for file in self.files
                for cls in file.classes
            ]
        
            # Dependencies DataFrame
            dependencies_data = [
                  {
                    'filepath': str(file.path),
                    'dependency': dep.name,
                    'version': dep.version,
                    'is_standard_lib': dep.is_standard_lib,
                    'is_local': dep.is_local
                }
                for file in self.files
                for dep in file.dependencies
            ]

            # Full Code Content DataFrame
            files_data = [
                {
                'filepath': str(file.path),
                    'content': file.content  # Include the full code content here
                }
                for file in self.files
            ]

            return {
                'functions': pd.DataFrame(functions_data) if functions_data else pd.DataFrame(),
                'classes': pd.DataFrame(classes_data) if classes_data else pd.DataFrame(),
                'dependencies': pd.DataFrame(dependencies_data) if dependencies_data else pd.DataFrame(),
                'files': pd.DataFrame(files_data) if files_data else pd.DataFrame()  # New DataFrame for full code content
            }
        except Exception as e:
            print(f"Error creating DataFrames: {str(e)}")
            return {
                'functions': pd.DataFrame(),
                'classes': pd.DataFrame(),
                'dependencies': pd.DataFrame(),
                'files': pd.DataFrame()  # Ensure an empty DataFrame is returned on error
            }
    def _extract_function_info(self, node: ast.FunctionDef, filepath: str) -> FunctionInfo:
        """Extract information about a function"""
        args = []
        for i, arg in enumerate(node.args.args):
            default = node.args.defaults[i] if i < len(node.args.defaults) else None
            args.append(self._parse_argument(arg, default))

        return FunctionInfo(
            code=ast.unparse(node),
            function_name=node.name,
            filepath=filepath,
            docstring=ast.get_docstring(node),
            args=args,
            return_annotation=ast.unparse(node.returns) if node.returns else None,
            decorators=self._extract_decorators(node)
        )

    # def to_dataframe(self) -> pd.DataFrame:
    #     """
    #     Convert the analyzed data to a pandas DataFrame
    #     """
    #     rows = []
    #     for file in self.files:
    #         for func in file.functions:
    #             rows.append({
    #                 filepath: func.filepath,
    #                 function_name: func.function_name,
    #                 code: func.code,
    #                 docstring: func.docstring,
    #                 args: func.args,
    #                 return_annotation: func.return_annotation
    #             })
    #     return pd.DataFrame(rows)
    def analyze_repo(self) -> List[FileInfo]:
        """
        Analyze all Python files in the repository.
        Returns a list of FileInfo objects containing analysis results.
        """
        def should_skip_path(path: Path) -> bool:
            """Helper to determine if a path should be skipped"""
            parts = path.parts
            return any(
                part.startswith('.') or 
                part == '.venv' or 
                part == 'venv' or
                part == '__pycache__' or
                part == 'build' or
                part == 'dist'
                for part in parts
            )

        code_files = [
            f for f in self.code_root.glob("**/*.py")
            if not should_skip_path(f.relative_to(self.code_root))
        ]

        num_files = len(code_files)
        rr(f"[blue]Total number of .py files: {num_files}[/blue]")

        if num_files == 0:
            rr("[red]Verify the repository exists and code_root is set correctly.[/red]")
            return []

        self.files = []
        total_functions = 0
        total_methods = 0
        total_classes = 0
        
        for code_file in code_files:
            try:
                file_info = self.analyze_file(str(code_file))
                self.files.append(file_info)
                
                # Count functions and methods separately
                total_functions += len(file_info.functions)
                for class_info in file_info.classes:
                    total_methods += len(class_info.methods)
                    total_classes += 1
                    
                rr(f"[green]Analyzed: {code_file}[/green]")
                rr(f"  Functions: {len(file_info.functions)}")
                rr(f"  Classes: {len(file_info.classes)}")
                for class_info in file_info.classes:
                    rr(f"    Class {class_info.name}: {len(class_info.methods)} methods")
                    
            except Exception as e:
                rr(f"[red]Error analyzing {code_file}: {str(e)}[/red]")
                import traceback
                rr(f"[red]{traceback.format_exc()}[/red]")

        # Print summary statistics
        successful = len([f for f in self.files if f.functions or f.classes])
        failed = num_files - successful
        
        rr("\n[blue]Analysis complete:[/blue]")
        rr(f"[green]Files processed successfully: {successful}[/green]")
        rr(f"[yellow]Files failed: {failed}[/yellow]")
        rr(f"[cyan]Total classes found: {total_classes}[/cyan]")
        rr(f"[cyan]Total standalone functions found: {total_functions}[/cyan]")
        rr(f"[cyan]Total methods found: {total_methods}[/cyan]")
        rr(f"[cyan]Total functions + methods: {total_functions + total_methods}[/cyan]")

        return self.files
    def _extract_function_info(self, node: ast.FunctionDef, filepath: str) -> FunctionInfo:
        """Extract information about a function"""
        args = []
        for i, arg in enumerate(node.args.args):
            default = node.args.defaults[i] if i < len(node.args.defaults) else None
            args.append(self._parse_argument(arg, default))

        return FunctionInfo(
            code=ast.unparse(node),
            function_name=node.name,
            filepath=filepath,
            docstring=ast.get_docstring(node),
            args=args,
            return_annotation=ast.unparse(node.returns) if node.returns else None,
            decorators=self._extract_decorators(node)
        )

    def _extract_class_info(self, node: ast.ClassDef, content: str, filepath: str) -> ClassInfo:
        """Extract information about a class"""
        methods = []
        class_variables = {}
        
        # Get base classes
        base_classes = [ast.unparse(base) for base in node.bases]
        
        for body_item in node.body:
            if isinstance(body_item, ast.FunctionDef):
                method_code = ast.unparse(body_item)
                decorators = self._extract_decorators(body_item)
                is_property = any("property" in d for d in decorators)
                is_classmethod = any("classmethod" in d for d in decorators)
                is_staticmethod = any("staticmethod" in d for d in decorators)
                
                # Parse arguments
                args = []
                for i, arg in enumerate(body_item.args.args[1:] if not is_staticmethod else body_item.args.args):
                    default = body_item.args.defaults[i] if i < len(body_item.args.defaults) else None
                    args.append(self._parse_argument(arg, default))

                methods.append(MethodInfo(
                    name=body_item.name,
                    code=method_code,
                    docstring=ast.get_docstring(body_item),
                    args=args,
                    return_annotation=ast.unparse(body_item.returns) if body_item.returns else None,
                    decorators=decorators,
                    is_property=is_property,
                    is_classmethod=is_classmethod,
                    is_staticmethod=is_staticmethod
                ))
            elif isinstance(body_item, ast.AnnAssign):
                # Class variable with type annotation
                target_str = ast.unparse(body_item.target)
                value = ast.unparse(body_item.value) if body_item.value else None
                class_variables[target_str] = str(value) if value is not None else None
            elif isinstance(body_item, ast.Assign):
                # Class variable without type annotation
                for target in body_item.targets:
                    target_str = ast.unparse(target)
                    value = ast.unparse(body_item.value) if body_item.value else None
                    class_variables[target_str] = str(value) if value is not None else None

        return ClassInfo(
            name=node.name,
            code=ast.unparse(node),
            docstring=ast.get_docstring(node),
            methods=methods,
            base_classes=base_classes,
            filepath=filepath,
            class_variables=class_variables
        )
def main():
    analyzer = CodeAnalyzer.create(code_root=Path("c:/mygit/compuse/computer_use_demo"))
    analyzer.analyze_repo()
    df = analyzer.to_dataframe()
    df['functions'].to_csv("functions1.csv", index=False)
    df['classes'].to_csv("classes1.csv", index=False)
    df['dependencies'].to_csv("dependencies1.csv", index=False)
    df['files'].to_csv("files1.csv", index=False)
if __name__ == "__main__":
    main()


