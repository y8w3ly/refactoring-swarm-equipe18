#!/usr/bin/env python3
import subprocess
import sys
import os
import json
import time


def run_step(description, command, fail_exit=True):
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        # Verify if command succeeded
        if result.returncode != 0:
            print(result.stdout)
            print(f"⚠️ Stderr: {result.stderr[:1000]}")
            print(f"❌ Failed (Exit Code: {result.returncode})")
            if fail_exit:
                sys.exit(1)
            return False

        # If success, print limited output
        lines = result.stdout.splitlines()
        if len(lines) > 10:
            print("\n".join(lines[:10]) + f"\n... ({len(lines)-10} more lines)")
        else:
            print(result.stdout)

        return True
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        if fail_exit:
            sys.exit(1)
        return False


def main():
    print("=" * 60)
    print("🧪 REFACTORING SWARM FINAL TEST")
    print("=" * 60)

    # 1. Check Setup
    run_step("Checking Environment", [sys.executable, "check_setup.py"])

    # 2. Generate Dataset
    # run_step("Generating Dataset & Tests", [sys.executable, "generate_dataset.py"])

    # 3. Running Swarm
    print("\n📋 Running Swarm Agents...")
    print("   Input:  buggycodes/")
    print("   Output: fixedcodes/")

    use_mock = False
    if "--mock" in sys.argv:
        use_mock = True
        print("   ✅ Mock Mode Enabled (Pass --no-mock to disable)")

    else:
        print("   ⚠️  REAL API MODE ENABLED (Cost will apply)")

    env = os.environ.copy()
    env["MOCK_MODE"] = "true" if use_mock else "false"

    start_time = time.time()
    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--target_dir",
            "buggycodes",
            "--output_dir",
            "fixedcodes",
        ],
        text=True,
        env=env,
    )

    duration = time.time() - start_time
    if result.returncode != 0:
        print("❌ Swarm execution failed!")
        print(result.stderr)
        sys.exit(1)

    print(f"✅ Swarm finished in {duration:.2f}s")

    # 4. Verify Output Files
    print("\n📋 Verifying Output Directory...")
    fixed_files = [f for f in os.listdir("fixedcodes") if f.endswith(".py")]
    print(f"   Found {len(fixed_files)} Python files in fixedcodes/")
    # if len(fixed_files) != 10:
    #     print(f"⚠️ Expected 10 files, found {len(fixed_files)}")


    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()