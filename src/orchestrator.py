import os
import sys
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
        self.max_iterations = 5

    def run(self) -> dict:
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
            write_failures = 0

            # Ensure we are working with the absolute path
            full_path = (
                os.path.join(self.target_dir, file_path)
                if not os.path.isabs(file_path)
                else file_path
            )

            print(f"\n📁 Processing: {file_path} (Score: {original_score})")

            while iteration < self.max_iterations:
                iteration += 1
                print(f"   🔄 Iteration {iteration}/{self.max_iterations}")

                analysis["current_iteration"] = iteration
                fix_result = fixer.fix(analysis, error_logs)

                if not fix_result.get("file_written", False):
                    print(f"   ⚠️ Fix not written: {fix_result.get('error')}")
                    write_failures += 1
                    error_logs = (
                        f"Previous attempt failed to write file: {fix_result.get('error')}"
                    )
                    if write_failures >= 2:
                        print("   ❌ Aborting file due to repeated write failures.")
                        completed_files.append(
                            {
                                "file": file_path,
                                "status": "RETRY",
                                "iterations": iteration,
                                "final_verdict": {
                                    "verdict": "RETRY",
                                    "feedback": "Repeated write failures from Fixer.",
                                },
                            }
                        )
                        break
                    continue
                write_failures = 0

                # EVALUATION PHASE
                print("   ⚖️  Judging new code...")
                verdict = judge.evaluate(full_path, original_score, self.target_dir)
                v_status = verdict.get("verdict", "UNKNOWN").upper()

                if v_status == "PASS":
                    print(f"   ✅ PASS (Success)")
                    final_score = verdict.get("actual_new_score")
                    print(f"FINAL SCORE: {final_score}")
                    completed_files.append(
                        {
                            "file": file_path,
                            "status": "PASS",
                            "iterations": iteration,
                            "final_verdict": verdict,
                        }
                    )
                    break

                elif v_status == "RETRY":
                    feedback = verdict.get("feedback", "No feedback")
                    print(f"   🔄 RETRY NEEDED: {feedback}")
                    error_logs = (
                        f"Judge Feedback: {feedback}\n"
                        f"Test Output: {verdict.get('pytest_output', '')[:3000]}"
                    )
                    # Update analysis so Fixer sees the history
                    analysis["previous_fix"] = fix_result

                else:
                    print(f"   ❓ Unknown Verdict '{v_status}'. Retrying...")
                    error_logs = f"Judge returned unclear verdict: {v_status}. Please fix code validity."

            else:
                print(f"   🛑 Max iterations reached for {file_path}")
                completed_files.append(
                    {
                        "file": file_path,
                        "status": "RETRY",
                        "iterations": iteration,
                        "final_verdict": {
                            "verdict": "RETRY",
                            "feedback": "Max iterations reached.",
                        },
                    }
                )

        return {
            "mission_complete": True,
            "completed_files": completed_files,
            "total_files": len(analyses),
        }
