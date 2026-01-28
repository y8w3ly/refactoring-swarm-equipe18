import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "10.py"))
    spec = importlib.util.spec_from_file_location("fixed_10", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_10"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()

def test_check_password():
    assert module.check_password("short") is False
    assert module.check_password("password123") is False
