import os
from pathlib import Path

_sandbox_root = None

def set_sandbox(path: str):
    global _sandbox_root
    _sandbox_root = os.path.abspath(path)

def _validate_path(path: str) -> str:
    if _sandbox_root is None:
        raise RuntimeError("Sandbox not configured. Call set_sandbox() first.")
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(_sandbox_root):
        raise PermissionError(f"Access denied: {path} is outside sandbox")
    return abs_path

def read_file(path: str) -> str:
    safe_path = _validate_path(path)
    with open(safe_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path: str, content: str) -> None:
    safe_path = _validate_path(path)
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, 'w', encoding='utf-8') as f:
        f.write(content)

def list_python_files(directory: str) -> list:
    safe_dir = _validate_path(directory)
    files = []
    for root, _, filenames in os.walk(safe_dir):
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('test_'):
                files.append(os.path.join(root, filename))
    return files
