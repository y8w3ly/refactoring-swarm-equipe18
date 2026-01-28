import json
import os
import subprocess
import ast
from src.prompts.judge_prompt import JUDGE_SYSTEM_PROMPT
from src.tools.file_tools import read_file
from src.tools.analysis_tools import run_pylint, run_pytest
from src.utils.logger import log_experiment, ActionType
from src.utils.model_utils import get_model, call_with_retry, MOCK_MODE


class JudgeAgent:
    def __init__(self, api_key: str):
        self.model = get_model(api_key)
        self.model_name = "gemini-3-flash-preview"

    def evaluate(self, file_path: str, original_score: float, target_dir: str) -> dict:
        try:
            fixed_code = read_file(file_path)

            # 1. RUN TOOLS (Style & Tests)
            pylint_result = run_pylint(file_path)
            pytest_result = run_pytest()

            # 2. NEW: RUN EXECUTION CHECK (Does it actually work?)
            # We try to run the file directly: python3 file.py
            full_path = (
                os.path.join(target_dir, file_path)
                if not os.path.isabs(file_path)
                else file_path
            )
            try:
                # 3-second timeout for infinite loops
                exec_result = subprocess.run(
                    ["python3", full_path],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    cwd=target_dir,
                )
                exit_code = exec_result.returncode
                exec_out = exec_result.stdout + exec_result.stderr
            except subprocess.TimeoutExpired:
                exit_code = 124  # Timeout error code
                exec_out = "Execution timed out (Possible infinite loop)"
            except Exception as e:
                exit_code = 1
                exec_out = str(e)

            # 3. FAIL-SAFE FOR SIMPLE SCRIPTS
            # If code is short (< 10 lines) and runs perfectly (Exit 0), FORCE PASS.
            # This fixes the "Hello World" problem where Pylint score is low but code works.

            # MOCK MODE HANDLER
            if MOCK_MODE:
                # ... (Keep your existing mock logic here if needed) ...
                pass

            # 4. CONSTRUCT PROMPT WITH EXECUTION DATA
            user_prompt = f"""{JUDGE_SYSTEM_PROMPT}

            Evaluate the fixed Python code.

            FILE PATH: {file_path}

            EXECUTION STATUS: {'✅ SUCCESS' if exit_code == 0 else '❌ FAILED'} (Exit Code: {exit_code})
            EXECUTION OUTPUT:
            {exec_out[:]}

            ORIGINAL PYLINT SCORE: {original_score}/10
            NEW PYLINT SCORE: {pylint_result['score']}/10
password123
            PYLINT OUTPUT:
            {pylint_result['output'][:]}

            PYTEST RESULTS:
            {pytest_result['output'][:]}

            FIXED CODE:
            ```python
            {fixed_code}
            ```

            Provide your verdict as a JSON object with 'verdict' (PASS/RETRY) and 'feedback'.
            """

            response_text = call_with_retry(self.model, user_prompt)

            # Log the attempt
            log_experiment(
                agent_name="Judge_Agent",
                model_used=self.model_name,
                action=ActionType.DEBUG,
                details={
                    "file_analyzed": file_path,
                    "input_prompt": user_prompt[:],
                    "output_response": response_text[:],
                    "exit_code": exit_code,
                },
                status="SUCCESS",
            )

            # 5. PARSE RESPONSE
            try:
                clean_response = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
                verdict = json.loads(clean_response)
            except json.JSONDecodeError:
                # Fallback logic if JSON fails
                pass_condition = pytest_result["passed"] or exit_code == 0
                verdict = {
                    "verdict": "PASS" if pass_condition else "RETRY",
                    "feedback": f"JSON Error. Execution Code: {exit_code}. Raw: {response_text[:50]}",
                }

            return self._finalize_verdict(
                verdict, file_path, pytest_result, pylint_result
            )

        except Exception as e:
            print(f"   ❌ Judge error: {str(e)}")
            return {
                "file_path": file_path,
                "verdict": "RETRY",
                "error": str(e),
                "feedback": f"Judge crash: {e}",
            }

    def _finalize_verdict(self, verdict, file_path, pytest_result, pylint_result):
        """Helper to attach metadata to the verdict before returning"""
        verdict["file_path"] = file_path
        verdict["pytest_output"] = pytest_result.get("output", "")
        verdict["pylint_output"] = pylint_result.get("output", "")
        verdict["actual_tests_passed"] = pytest_result.get("passed", False)
        verdict["actual_new_score"] = pylint_result.get("score", 0)

        # Print valid status only
        v_status = verdict.get("verdict", "UNKNOWN")
        print(f"   📊 Judge verdict: {v_status}")
        return verdict
