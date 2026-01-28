import argparse
import sys
import os
import shutil
from dotenv import load_dotenv
from src.orchestrator import Orchestrator
from src.utils.logger import log_experiment, ActionType

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="The Refactoring Swarm - Multi-Agent Code Refactoring System"
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Path to the directory containing code to refactor (Input)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=False,
        help="Path to save the fixed code (Output). If set, input files are copied here first.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.target_dir):
        print(f"❌ Input directory {args.target_dir} not found.")
        sys.exit(1)

    # If output_dir is specified, set it up
    work_dir = args.target_dir

    if args.output_dir:
        print(f"📦 Setting up output directory: {args.output_dir}")
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        # Copy all files from target to output
        # We use a simple copy loop to avoid copying .git or other garbage if using shutil.copytree indiscriminately
        # But for this purpose, let's just copy the python files or the whole content?
        # The user wants "index by 1..10.py", implying a flat structure.
        # Let's copy everything.
        try:
            # If directory exists and is not empty, we might overwrite. Safe enough for this lab.
            # We use dirs_exist_ok=True (Python 3.8+)
            shutil.copytree(args.target_dir, args.output_dir, dirs_exist_ok=True)
            print(f"✅ Copied input files to {args.output_dir}")
            work_dir = args.output_dir
        except Exception as e:
            print(f"❌ Failed to copy files: {e}")
            sys.exit(1)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file.")
        sys.exit(1)

    print(f"🚀 STARTING REFACTORING SWARM ON: {work_dir}")

    log_experiment(
        agent_name="System",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": f"System startup with target: {work_dir}",
            "output_response": "Initializing orchestrator",
        },
        status="SUCCESS",
    )

    try:
        orchestrator = Orchestrator(work_dir, api_key)
        result = orchestrator.run()

        print("\n" + "=" * 50)
        print("📊 MISSION REPORT")
        print("=" * 50)
        print(f"✅ Mission Complete: {result['mission_complete']}")
        print(
            f"📁 Files Processed: {len(result['completed_files'])}/{result['total_files']}"
        )

        for file_info in result["completed_files"]:
            verdict = file_info.get("final_verdict", {})
            status = "✅ PASS" if verdict.get("verdict") == "PASS" else "🔄 RETRY"
            print(
                f"   - {file_info['file']}: {status} (iterations: {file_info['iterations']})"
            )

        print("=" * 50)
        print("✅ MISSION_COMPLETE")

        if args.output_dir:
            print(f"\n✨ Fixed code is available in: {args.output_dir}")

        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.GENERATION,
            details={
                "input_prompt": "System completion",
                "output_response": f"Mission complete. Processed {len(result['completed_files'])} files.",
            },
            status="SUCCESS",
        )

    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.DEBUG,
            details={
                "input_prompt": "System error",
                "output_response": f"Error: {str(e)}",
            },
            status="FAILURE",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
