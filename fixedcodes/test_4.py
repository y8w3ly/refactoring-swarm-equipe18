import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "4.py"))
    spec = importlib.util.spec_from_file_location("fixed_4", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_4"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()

def test_bubble_sort():
    assert module.bubble_sort([3, 1, 2]) == [1, 2, 3]
    assert module.bubble_sort([]) == []
