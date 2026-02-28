import subprocess
import re
import sys
from pathlib import Path


def run_pylint(file_path: str) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pylint", file_path, "--output-format=text"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        score_match = re.search(r"Your code has been rated at ([\d.-]+)/10", output)
        score = float(score_match.group(1)) if score_match else 0.0
        return {"score": score, "output": output, "success": True}
    except Exception as e:
        return {"score": 0.0, "output": str(e), "success": False}


def run_pytest(target_dir: str = "fixedcodes") -> dict:
    tests_root = Path(target_dir)
    if not tests_root.exists():
        return {
            "passed": True,
            "output": f"Directory not found: {target_dir}. Skipping pytest.",
            "return_code": 0,
        }

    test_files = list(tests_root.glob("test_*.py"))
    if not test_files:
        return {
            "passed": True,
            "output": f"No tests found under {target_dir}. Skipping pytest.",
            "return_code": 0,
        }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target_dir, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        return {
            "passed": passed,
            "output": result.stdout + result.stderr,
            "return_code": result.returncode,
        }
    except Exception as e:
        return {"passed": False, "output": str(e), "return_code": -1}


def get_pylint_score(file_path: str) -> float:
    result = run_pylint(file_path)
    return result["score"]
