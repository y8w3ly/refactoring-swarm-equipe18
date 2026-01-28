import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "2.py"))
    spec = importlib.util.spec_from_file_location("fixed_2", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_2"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()

def test_is_palindrome():
    assert module.is_palindrome("racecar") is True
    assert module.is_palindrome("hello") is False
