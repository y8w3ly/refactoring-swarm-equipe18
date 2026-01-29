# The Refactoring Swarm (Equipe 18) 🚀

A multi-agent autonomous system built with Google Gemini to automatically audit, fix, and validate Python code.

## 🌟 Overview

This project implements a "Swarm" of specialized AI agents that work together to improve code quality:
1.  **Auditor Agent**: Analyzes code for bugs, style violations, and improved logic.
2.  **Fixer Agent**: Applies the refactoring plan to the code.
3.  **Judge Agent**: Runs tests (Pytest) and static analysis (Pylint) to validate the fix.

The system uses a robust orchestrator with self-healing capabilities (retries) and supports both a **Mock Mode** (free, offline) and **Production Mode** (live API).

---

## 📂 Project Structure

```
├── main.py                    # CLI Entry point
├── test_refactoring_swarm.py  # Master test script (runs end-to-end workflow)
├── generate_dataset.py        # Generates test dataset (buggy codes + unit tests)
├── check_setup.py             # Verifies environment (Python, .env, API key)
├── requirements.txt           # Python dependencies
├── .env                       # API Key configuration
├── src/
│   ├── orchestrator.py        # Core logic loop (Audit -> Fix -> Judge)
│   ├── agents/                # Agent definitions (Auditor, Fixer, Judge)
│   ├── tools/                 # File I/O, Pylint, Pytest wrappers
│   ├── utils/                 # Logger, Global Model Utilities
│   └── prompts/               # System prompts for agents
├── buggycodes/                # Input directory for bad code
├── fixedcodes/                # Output directory for fixed code
└── logs/                      # JSON logs of agent interactions
```

---

## ⚡ Quick Start

### 1. Setup
Ensure you have Python 3.10+ installed.

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API Key (for production mode)
# Create .env file and add: GOOGLE_API_KEY=your_key_here
```

### 2. Run the Demo (Mock Mode)
This runs the full workflow using the internal "Smart Mock" system (no API cost). It generates 10 buggy files, fixes them, and verifies the results.

```bash
python3 test_refactoring_swarm.py --mock
```

### 3. Run Production (Real API)
To use actual LLM agents to refactor the code (consumes API quota):

```bash
python3 test_refactoring_swarm.py 
```

---

## 🛠 Manual Usage

You can also run the system on any directory of Python files:

```bash
# Syntax
python3 main.py --target_dir <InputDirectory> --output_dir <OutputDirectory>

# Example
python3 main.py --target_dir ./my_legacy_code --output_dir ./clean_code
```

**Environment Variables:**
- `MOCK_MODE=true`: Forces mock agents (bypasses API).
- `MOCK_MODE=false`: Use real Gemini API (default if not set).

---

## 🧩 Architecture

The system avoids recursion limits by using a `while` loop orchestrator:

1.  **Input**: Files are copied from `target_dir` to `output_dir`.
2.  **Cycle**:
    - **Audit**: Analyzes code in `output_dir`.
    - **Fix**: Updates code in `output_dir`.
    - **Judge**: Runs `pytest` and `pylint`.
    - **Feedback**: If verification fails, the Fixer is called again with error logs.
3.  **result**: Clean, tested code in `output_dir`.

---

## ✅ Features

- **Sandboxed File I/O**: Agents cannot modify files outside the target directory.
- **Smart Mock Mode**: Heuristic-based fixer for testing without API keys.
- **Retry Logic**: Automatically handles API rate limits (429 errors).
- **Comprehensive Logging**: All actions recorded in `logs/experiment_data.json`.
