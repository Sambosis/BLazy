import re
from typing import Optional

def normalize_path(path: Optional[str]) -> str:
    """
    Normalize a file path to ensure it starts with 'C:/repo/'.
    
    Args:
        path: Input path string that needs to be normalized
        
    Returns:
        Normalized path string starting with 'C:/repo/'
        
    Raises:
        ValueError: If the path is None or empty
    """
    if not path:
        raise ValueError('Path cannot be empty')
    
    # Convert to string in case we receive a Path object
    normalized_path = str(path)
    
    # Convert all backslashes to forward slashes
    normalized_path = normalized_path.replace('\\', '/')
    
    # Remove any leading/trailing whitespace
    normalized_path = normalized_path.strip()
    
    # Remove multiple consecutive forward slashes
    normalized_path = re.sub(r'/+', '/', normalized_path)
    
    # Remove 'C:' or 'c:' if it exists at the start
    normalized_path = re.sub(r'^[cC]:', '', normalized_path)
    
    # Remove '/repo/' if it exists at the start
    normalized_path = re.sub(r'^/repo/', '', normalized_path)
    
    # Remove leading slash if it exists
    normalized_path = re.sub(r'^/', '', normalized_path)
    
    # Combine with base path
    return f'C:/repo/{normalized_path}'


def run_tests():
    """Run test cases for the normalize_path function."""
    test_cases = [
        {
            'input': 'file.txt',
            'expected': 'C:/repo/file.txt',
            'description': 'Simple filename'
        },
        {
            'input': '/file.txt',
            'expected': 'C:/repo/file.txt',
            'description': 'Path with leading slash'
        },
        {
            'input': 'C:/repo/file.txt',
            'expected': 'C:/repo/file.txt',
            'description': 'Path already in correct format'
        },
        {
            'input': 'c:/repo/file.txt',
            'expected': 'C:/repo/file.txt',
            'description': 'Path with lowercase c: drive'
        },
        {
            'input': '/repo/file.txt',
            'expected': 'C:/repo/file.txt',
            'description': 'Path starting with /repo/'
        },
        {
            'input': 'subfolder/file.txt',
            'expected': 'C:/repo/subfolder/file.txt',
            'description': 'Path with subfolder'
        },
        {
            'input': '\\windows\\style\\path.txt',
            'expected': 'C:/repo/windows/style/path.txt',
            'description': 'Windows-style path with backslashes'
        },
        {
            'input': 'C:\\repo\\windows\\style.txt',
            'expected': 'C:/repo/windows/style.txt',
            'description': 'Windows path with C: drive'
        },
        {
            'input': '  spaces/in/path.txt  ',
            'expected': 'C:/repo/spaces/in/path.txt',
            'description': 'Path with leading/trailing spaces'
        },
        {
            'input': 'repo/double//slash//file.txt',
            'expected': 'C:/repo/double/slash/file.txt',
            'description': 'Path with multiple consecutive slashes'
        }
    ]

    passed_tests = 0
    failed_tests = 0

    for i, test_case in enumerate(test_cases, 1):
        try:
            result = normalize_path(test_case['input'])
            if result == test_case['expected']:
                print(f"✓ Test {i} passed: {test_case['description']}")
                print(f"  Input:    \"{test_case['input']}\"")
                print(f"  Output:   \"{result}\"")
                passed_tests += 1
            else:
                print(f" Test {i} failed: {test_case['description']}")
                print(f"  Input:    \"{test_case['input']}\"")
                print(f"  Expected: \"{test_case['expected']}\"")
                print(f"  Got:      \"{result}\"")
                failed_tests += 1
        except Exception as e:
            print(f" Test {i} failed with error: {test_case['description']}")
            print(f"  Input:    \"{test_case['input']}\"")
            print(f"  Error:    {str(e)}")
            failed_tests += 1
        print()  # Add blank line between tests

    print("Test Summary:")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Total:  {len(test_cases)}")


if __name__ == '__main__':
    # Example usage
    print("Running tests...\n")
    run_tests()
    
    # Additional examples
    print("\nAdditional examples:")
    examples = [
        'my/file.txt',
        '/some/path/file.txt',
        'C:\\repo\\windows\\style.txt'
    ]
    
    for example in examples:
        print(f"normalize_path('{example}') -> '{normalize_path(example)}'")