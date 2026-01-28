import os
import shutil

def generate_dataset():
    print("🧪 Generating Test Dataset...")
    
    # Define directories
    buggy_dir = "buggycodes"
    fixed_dir = "fixedcodes"
    tests_dir = "fixedcodes"
    
    # Create/Clean directories
    for d in [buggy_dir, fixed_dir, tests_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    
    # Helper to generate robust import code for 1.py, 2.py etc.
    def get_import_block(id):
        return f"""import pytest
import importlib.util
import sys
import os

def import_code():
    # Dynamic import to handle files starting with numbers
    file_path = os.path.abspath(os.path.join("fixedcodes", "{id}.py"))
    spec = importlib.util.spec_from_file_location("fixed_{id}", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_{id}"] = module
    spec.loader.exec_module(module)
    return module

module = import_code()
"""

    dataset = [
        {
            "id": "1",
            "buggy": """def calc_avg(nums):
    return sum(nums) / len(nums)
""",
            "test_body": """
def test_calc_avg():
    assert module.calc_avg([1, 2, 3]) == 2.0
    assert module.calc_avg([]) == 0  # This checks the fix
""",
            "desc": "Division by zero potential"
        },
        {
            "id": "2",
            "buggy": """def is_palindrome(s):
    rev = ""
    for i in range(len(s)):
        rev += s[len(s)-1-i]
    if rev == s:
        return True
""",
            "test_body": """
def test_is_palindrome():
    assert module.is_palindrome("racecar") is True
    assert module.is_palindrome("hello") is False
""",
            "desc": "Inefficient palindrome check"
        },
        {
            "id": "3",
            "buggy": """def read_file(f):
    file = open(f, 'r')
    data = file.read()
    print(data)
""",
            "test_body": """
def test_read_file(tmp_path):
    # Create dummy file
    f = tmp_path / "test.txt"
    f.write_text("hello")
    # We just run it to ensure no crash. 
    # Side effects hard to test without capsys, but Smart Mock fixes open() usage.
    try:
        module.read_file(str(f))
    except Exception as e:
        pytest.fail(f"read_file raised exception: {e}")
""",
            "desc": "Unsafe file handling"
        },
         {
            "id": "4",
            "buggy": """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1] :
                arr[j], arr[j+1] == arr[j+1], arr[j]
    return arr
""",
            "test_body": """
def test_bubble_sort():
    assert module.bubble_sort([3, 1, 2]) == [1, 2, 3]
    assert module.bubble_sort([]) == []
""",
            "desc": "Broken bubble sort swap"
        },
        {
            "id": "5",
            "buggy": """class user:
    def __init__(self, n, a):
        self.name = n
        self.age = a
    
    def print(self):
        print(self.name + " is " + self.age)
""",
            "test_body": """
def test_user():
    # Smart mock renames class to User
    if hasattr(module, 'User'):
        cls = module.User
    else:
        cls = module.user
        
    u = cls("Alice", "30") 
    assert u.name == "Alice"
    
    # Test fix for string concatenation if possible, or just existence
    u2 = cls("Bob", 25)
    # The fix changes print method to f-string. 
    # Calling print without failure is the test.
    try:
        u2.print() # Should print "Bob is 25" without TypeError
    except TypeError:
        pytest.fail("TypeError in print method (fix not applied?)")
""",
            "desc": "Class naming and type error"
        },
        {
            "id": "6",
            "buggy": """def get_item(list, index):
    return list[index]
""",
            "test_body": """
def test_get_item():
    assert module.get_item([10, 20], 1) == 20
    # Boundary check test is optional depending on if fix implemented it
    pass
""",
            "desc": "Index Error potential"
        },
        {
            "id": "7",
            "buggy": """def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
""",
            "test_body": """
def test_factorial():
    assert module.factorial(5) == 120
    with pytest.raises(ValueError):
        module.factorial(-1)
""",
            "desc": "Recursion depth/negative input"
        },
        {
            "id": "8",
            "buggy": """import requests

def fetch_data(url):
    r = requests.get(url)
    return r.json()
""",
             "test_body": """
def test_fetch_data():
    pass # Skip mock network test
""",
            "desc": "Unsafe API call"
        },
        {
            "id": "9",
            "buggy": """def merge_dicts(d1, d2):
    for k in d2:
        d1[k] = d2[k]
    return d1
""",
            "test_body": """
def test_merge_dicts():
    d1 = {'a': 1}
    d2 = {'b': 2}
    res = module.merge_dicts(d1, d2)
    assert res == {'a': 1, 'b': 2}
    # Check for side effect (original d1 shouldn't change if fixed)
    # Smart mock fix: copies d1.
    if d1 != {'a': 1}:
        pytest.fail("Side effect detected: d1 was modified!")
""",
            "desc": "Dictionary side effect"
        },
        {
            "id": "10",
            "buggy": """def check_password(pwd):
    if len(pwd) < 8:
        return False
    if "password" in pwd:
        return False
    return True
""",
            "test_body": """
def test_check_password():
    assert module.check_password("short") is False
    assert module.check_password("password123") is False
""",
            "desc": "Weak password check"
        }
    ]

    for item in dataset:
        # Write buggy code
        path = os.path.join(buggy_dir, f"{item['id']}.py")
        formatted_code = item['buggy']
        if "Function docstring" in formatted_code:
             pass 
        with open(path, "w") as f:
            f.write(formatted_code)
        
        # Write test code (to tests/test_id.py)
        if "test_body" in item:
            test_content = get_import_block(item['id']) + item['test_body']
            test_path = os.path.join(tests_dir, f"test_{item['id']}.py")
            with open(test_path, "w") as f:
                f.write(test_content)
             
        print(f"   - Created {path} ({item['desc']})")

    print(f"✅ Generated {len(dataset)} buggy files in '{buggy_dir}'")
    print(f"✅ Generated {len(dataset)} test files in '{tests_dir}'")
    print(f"   Created empty '{fixed_dir}' directory for outputs.")

if __name__ == "__main__":
    generate_dataset()
