import json
import time
import ast
import re
import os
from src.prompts.fixer_prompt import FIXER_SYSTEM_PROMPT
from src.tools.file_tools import write_file
from src.utils.logger import log_experiment, ActionType
from src.utils.model_utils import get_model, call_with_retry, MOCK_MODE


class FixerAgent:
    def __init__(self, api_key: str):
        self.model = get_model(api_key)
        self.model_name = "gemini-3-flash-preview"

    def fix(self, analysis: dict, error_logs: str = None) -> dict:
        file_path = analysis.get("file_path", "unknown")
        original_code = analysis.get("original_code", "")

        if MOCK_MODE:
            fixed_code, changes = self._smart_mock_fix(original_code)
            write_file(file_path, fixed_code)
            log_experiment(
                agent_name="Fixer_Agent",
                model_used="smart_mock",
                action=ActionType.FIX,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": "Smart Mock mode fix",
                    "output_response": f"Applied fixes: {changes}",
                },
                status="SUCCESS",
            )
            return {
                "file_path": file_path,
                "fixed_code": fixed_code,
                "file_written": True,
                "changes_made": changes,
            }

        user_prompt = f"""{FIXER_SYSTEM_PROMPT}

Fix the following Python code based on the analysis.

FILE PATH: {file_path}

ORIGINAL CODE:
```python
{original_code}
```

ANALYSIS REPORT:
{json.dumps(analysis, indent=2, default=str)[:3000]}
"""

        if error_logs:
            user_prompt += f"\n\nPREVIOUS ERROR LOGS:\n{error_logs[:1500]}\n\nPlease fix the issues mentioned in the error logs."

        user_prompt += "\n\nProvide the fixed code as a JSON object."

        try:
            response_text = call_with_retry(self.model, user_prompt)

            log_experiment(
                agent_name="Fixer_Agent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": user_prompt[:1000],
                    "output_response": response_text[:1000],
                    "is_retry": error_logs is not None,
                },
                status="SUCCESS",
            )

            try:
                clean_response = response_text
                if "```json" in clean_response:
                    clean_response = clean_response.split("```json")[1].split("```")[0]
                elif "```" in clean_response:
                    clean_response = clean_response.split("```")[1].split("```")[0]
                fix_result = json.loads(clean_response.strip())
            except json.JSONDecodeError:
                code_block = response_text
                if "```python" in code_block:
                    code_block = code_block.split("```python")[1].split("```")[0]
                fix_result = {
                    "file_path": file_path,
                    "fixed_code": code_block.strip(),
                    "changes_made": ["Auto-extracted"],
                }

            if "fixed_code" in fix_result and fix_result["fixed_code"]:
                write_file(file_path, fix_result["fixed_code"])
                fix_result["file_written"] = True
                print(f"   ✅ Fixed code written to {file_path}")
            else:
                fix_result["file_written"] = False

            fix_result["file_path"] = file_path
            return fix_result

        except Exception as e:
            print(f"   ❌ Fixer error: {str(e)}")
            log_experiment(
                agent_name="Fixer_Agent",
                model_used=self.model_name,
                action=ActionType.FIX,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": user_prompt[:500],
                    "output_response": f"Error: {str(e)}",
                },
                status="FAILURE",
            )
            return {"file_path": file_path, "error": str(e), "file_written": False}

    def _smart_mock_fix(self, code: str) -> tuple[str, list]:
        """
        Applies heuristic fixes to simulate an LLM without an API.
        Targeting common issues in the generated dataset.
        """
        changes = []
        fixed_code = code

        # Bug 1: Average calc (Both variants)
        if "sum / len(nums)" in fixed_code:
            fixed_code = fixed_code.replace(
                "sum / len(nums)", "sum / len(nums) if nums else 0"
            )
            changes.append("Fixed division by zero in average calculation")
        elif "sum(nums) / len(nums)" in fixed_code:
            fixed_code = fixed_code.replace(
                "sum(nums) / len(nums)", "sum(nums) / len(nums) if nums else 0"
            )
            changes.append("Fixed division by zero in average calculation")

        # Bug 2: Palindrome logic
        if "rev += s[len(s)-1-i]" in fixed_code:
            # Basic loop replacement
            fixed_code = fixed_code.replace(
                "rev += s[len(s)-1-i]", "rev = s[::-1]"
            ).replace(
                "for i in range(len(s)):\n        rev += s[len(s)-1-i]", "rev = s[::-1]"
            )
            # Fix return logic to avoid implicit None
            if "if rev == s:" in fixed_code and "else" not in fixed_code:
                fixed_code = fixed_code.replace(
                    "if rev == s:\n        return True", "return rev == s"
                )
            changes.append("Optimized palindrome check and return logic")

        # Bug 3: File read unsafe
        if "file = open(f, 'r')" in fixed_code:
            fixed_code = fixed_code.replace(
                "file = open(f, 'r')", "with open(f, 'r') as file:"
            )
            fixed_code = fixed_code.replace(
                "data = file.read()", "    data = file.read()"
            )
            fixed_code = fixed_code.replace("print(data)", "    print(data)")
            changes.append("Added context manager for file I/O")

        # Bug 4: Bubble sort swap
        if "arr[j], arr[j+1] == arr[j+1], arr[j]" in fixed_code:
            fixed_code = fixed_code.replace("==", "=")
            changes.append("Fixed assignment operator in bubble sort swap")

        # Bug 5: Class naming
        if "class user:" in fixed_code:
            fixed_code = fixed_code.replace("class user:", "class User:")
            changes.append("Fixed class naming (PEP8)")

        # Bug 6: String concat in print
        if 'print(self.name + " is " + self.age)' in fixed_code:
            fixed_code = fixed_code.replace(
                'print(self.name + " is " + self.age)',
                'print(f"{self.name} is {self.age}")',
            )
            changes.append("Fixed type error in string concatenation")

        # Bug 7: Factorial recursion limit/negative
        if "return n * factorial(n - 1)" in fixed_code:
            if "if n < 0:" not in fixed_code:
                # Use Regex to match def line regardless of type hints or spacing
                fixed_code = re.sub(
                    r"(def factorial\(.*?\):)",
                    r"\1\n    if n < 0: raise ValueError('Negative n')",
                    fixed_code,
                )
                changes.append("Added negative number check for factorial")

        # Bug 8: Requests error handling
        if "requests.get(url)" in fixed_code and "try:" not in fixed_code:
            fixed_code = fixed_code.replace(
                "r = requests.get(url)",
                "try:\n        r = requests.get(url, timeout=10)\n        r.raise_for_status()\n    except Exception as e:\n        return None",
            )
            fixed_code = fixed_code.replace("return r.json()", "    return r.json()")
            changes.append("Changed requests to use timeout and error handling")

        # Bug 9: Merge dicts side effect
        if "d1[k] = d2[k]" in fixed_code:
            fixed_code = fixed_code.replace(
                "d1[k] = d2[k]", "d3 = d1.copy()\n    d3.update(d2)\n    return d3"
            ).replace("return d1", "")
            changes.append("Fixed dictionary merge side-effect")

        # General: Add docstrings if missing
        lines = fixed_code.split("\n")
        if not lines[0].startswith('"""') and not lines[0].startswith("'''"):
            fixed_code = '"""Auto-generated module docstring."""\n' + fixed_code
            changes.append("Added module docstring")

        # Add Type Hints LAST (to ensure they don't break regexes above)
        if "def " in fixed_code and "->" not in fixed_code:
            fixed_code = re.sub(
                r"def (\w+)\(([^)]*)\):", r"def \1(\2) -> None:", fixed_code
            )
            changes.append("Added basic type hints")

        return fixed_code, changes