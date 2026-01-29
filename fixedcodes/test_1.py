import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "1.py"))
    spec = importlib.util.spec_from_file_location("fixed_1", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_1"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()

def test_calc_avg():
    assert module.calc_avg([1, 2, 3]) == 2.0
    # Empty list should return 0, but buggy code divides by zero and fails.
    assert module.calc_avg([]) == 0
