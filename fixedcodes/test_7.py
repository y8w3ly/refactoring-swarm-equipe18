import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "7.py"))
    spec = importlib.util.spec_from_file_location("fixed_7", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_7"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()

def test_factorial():
    assert module.factorial(5) == 120
    with pytest.raises(ValueError):
        module.factorial(-1)
