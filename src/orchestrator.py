import os
import sys  # Added sys to fix import errors
import time  # Added for safety delays
from src.agents.auditor import AuditorAgent
from src.agents.fixer import FixerAgent
from src.agents.judge import JudgeAgent
from src.tools.file_tools import set_sandbox
from src.utils.logger import log_experiment, ActionType


class Orchestrator:
    def __init__(self, target_dir: str, api_key: str):
        self.target_dir = os.path.abspath(target_dir)
        self.api_key = api_key
        set_sandbox(self.target_dir)
        self.max_iterations = 5  # Reduced from 10 to save tokens during debugging

    def run(self) -> dict:
        # CRITICAL FIX: Add the target dir to sys.path so the agents can "see" the modules
        if self.target_dir not in sys.path:
            sys.path.append(self.target_dir)

        log_experiment(
            agent_name="Orchestrator",
            model_used="system",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Starting on {self.target_dir}",
                "output_response": "Init",
            },
            status="SUCCESS",
        )

        auditor = AuditorAgent(self.api_key)
        fixer = FixerAgent(self.api_key)
        judge = JudgeAgent(self.api_key)

        print("🔍 Running Audit Phase...")
        audit_result = auditor.analyze(self.target_dir)
        analyses = audit_result.get("analyses", [])

        if not analyses:
            print("⚠️ No analyses returned. Check AuditorAgent.")
            return {"mission_complete": True, "completed_files": [], "total_files": 0}

        completed_files = []

        for analysis in analyses:
            file_path = analysis.get("file_path", "unknown")
            original_score = analysis.get("original_pylint_score", 0)
            iteration = 0
            error_logs = None

            # Ensure we are working with the absolute path
            full_path = (
                os.path.join(self.target_dir, file_path)
                if not os.path.isabs(file_path)
                else file_path
            )

            print(f"\nnb📁 Processing: {file_path} (Score: {original_score})")

            while iteration < self.max_iterations:
                iteration += 1
                print(f"   🔄 Iteration {iteration}/{self.max_iterations}")

                # FIX: Pass the 'iteration' number so the Fixer knows how desperate to be
                analysis["current_iteration"] = iteration
                fix_result = fixer.fix(analysis, error_logs)

                # FAIL-SAFE: If Fixer writes nothing, don't loop infinitely.
                if not fix_result.get("file_written", False):
                    print(f"   ⚠️ Fix not written: {fix_result.get('error')}")
                    error_logs = f"Previous attempt failed to write file: {fix_result.get('error')}"

                    # If we fail to write twice in a row, likely a permissions or API structure issue.
                    if iteration > 1 and "Previous attempt failed" in str(error_logs):
                        print("   ❌ Aborting file due to repeated write failures.")
                        break
                    continue

                # EVALUATION PHASE
                print("   ⚖️  Judging new code...")
                verdict = judge.evaluate(file_path, original_score, self.target_dir)
                v_status = verdict.get("verdict", "UNKNOWN").upper()

                if v_status == "PASS" and verdict.get("actual_tests_passed", False):
                    print(f"   ✅ PASS (Success)")
                    final_score = verdict.get("actual_new_score")
                    print(f"FINAL SCORE: {final_score}")
                    completed_files.append(
                        {"file": file_path, "status": "PASS", "iterations": iteration}
                    )
                    break

                elif v_status == "RETRY":
                    feedback = verdict.get("feedback", "No feedback")
                    print(f"   🔄 RETRY NEEDED: {feedback[:]}")
                    error_logs = f"Judge Feedback: {feedback}\nTest Output: {verdict.get('pytest_output', '')[:]}"
                    # Update analysis so Fixer sees the history
                    analysis["previous_fix"] = fix_result

                else:
                    # FIX: Handle unknown/failure states safely
                    print(f"   ❓ Unknown Verdict '{v_status}'. Retrying...")
                    error_logs = f"Judge returned unclear verdict: {v_status}. Please fix code validity."

            else:
                print(f"   🛑 Max iterations reached for {file_path}")
                completed_files.append(
                    {
                        "file": file_path,
                        "status": "MAX_ITERATIONS",
                        "iterations": iteration,
                    }
                )

        return {
            "mission_complete": True,
            "completed_files": completed_files,
            "total_files": len(analyses),
        }
