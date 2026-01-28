import json
import os
from src.prompts.auditor_prompt import AUDITOR_SYSTEM_PROMPT
from src.tools.file_tools import read_file, list_python_files
from src.tools.analysis_tools import run_pylint
from src.utils.logger import log_experiment, ActionType
from src.utils.model_utils import get_model, call_with_retry


class AuditorAgent:
    def __init__(self, api_key: str):
        self.model = get_model(api_key)
        self.model_name = "gemini-3-flash-preview"

    def analyze(self, target_dir: str) -> dict:
        python_files = list_python_files(target_dir)
        all_analyses = []

        print(f"   📂 Found {len(python_files)} Python files to analyze")

        for file_path in python_files:
            try:
                print(f"   📄 Analyzing: {file_path}")
                code_content = read_file(file_path)
                pylint_result = run_pylint(file_path)

                user_prompt = f"""{AUDITOR_SYSTEM_PROMPT}

Analyze this Python file and provide a refactoring plan.

FILE PATH: {file_path}

CURRENT PYLINT SCORE: {pylint_result['score']}/10

PYLINT OUTPUT:
{pylint_result['output'][:]}

CODE:
```python
{code_content}
```

Provide your analysis as a JSON object."""

                response_text = call_with_retry(self.model, user_prompt)

                log_experiment(
                    agent_name="Auditor_Agent",
                    model_used=self.model_name,
                    action=ActionType.ANALYSIS,
                    details={
                        "file_analyzed": file_path,
                        "input_prompt": user_prompt[:1000],
                        "output_response": response_text[:1000],
                        "pylint_score": pylint_result["score"],
                    },
                    status="SUCCESS",
                )

                try:
                    clean_response = response_text
                    if "```json" in clean_response:
                        clean_response = clean_response.split("```json")[1].split(
                            "```"
                        )[0]
                    elif "```" in clean_response:
                        clean_response = clean_response.split("```")[1].split("```")[0]
                    analysis = json.loads(clean_response.strip())
                except json.JSONDecodeError:
                    analysis = {
                        "file_path": file_path,
                        "raw_analysis": response_text,
                        "pylint_score": pylint_result["score"],
                    }

                analysis["file_path"] = file_path
                analysis["original_code"] = code_content
                analysis["original_pylint_score"] = pylint_result["score"]
                all_analyses.append(analysis)
                print(f"   ✅ Analysis complete for {file_path}")

            except Exception as e:
                print(f"   ❌ Error analyzing {file_path}: {str(e)}")
                log_experiment(
                    agent_name="Auditor_Agent",
                    model_used=self.model_name,
                    action=ActionType.ANALYSIS,
                    details={
                        "file_analyzed": file_path,
                        "input_prompt": f"Analysis request for {file_path}",
                        "output_response": f"Error: {str(e)}",
                        "error": str(e),
                    },
                    status="FAILURE",
                )

        return {"analyses": all_analyses, "total_files": len(python_files)}
