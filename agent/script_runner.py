"""
Executes a generated pytest file, captures output,
and asks Claude to diagnose any failures
"""

import subprocess
import sys
import os
import json
import anthropic
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def run_test_script(script_path: str, card_id: str) -> dict:
    """
    Run a pytest file and return a results dict.

    Returns dict with keys:
        success      : True if all tests passed
        exit_code    : 0 = pass, 1 = some tests failed, 2 = error
        stdout       : full captured output from pytest
        stderr       : any error output
        report_path  : path to the JSON report file
        timestamp    : ISO timestamp of when the run happened
        test_summary : dict with passed/failed/error counts (from JSON report)
    """

    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/result_{card_id}.json"

    print(f"   Running: pytest {script_path}")

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                script_path,
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={report_path}",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Tests timed out after 3 minutes.",
            "report_path": None,
            "timestamp": datetime.now().isoformat(),
            "test_summary": {"passed": 0, "failed": 0, "error": 1},
        }

    # Parse the JSON report if it was created
    test_summary = {"passed": 0, "failed": 0, "error": 0}
    if os.path.exists(report_path):
        try:
            with open(report_path) as f:
                report_data = json.load(f)
            summary = report_data.get("summary", {})
            test_summary["passed"] = summary.get("passed", 0)
            test_summary["failed"] = summary.get("failed", 0)
            test_summary["error"]  = summary.get("error", 0)
        except Exception:
            pass  # If report parsing fails, we still have stdout

    return {
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "report_path": report_path,
        "timestamp": datetime.now().isoformat(),
        "test_summary": test_summary,
    }


def diagnose_failure(run_result: dict, script_path: str) -> str:
    """
    When tests fail, ask Claude to read the error and explain:
    - What went wrong
    - Whether it's a script bug or missing information
    - Exactly what needs to be fixed
    """

    # Read the script so Claude can see the code that failed
    try:
        with open(script_path, encoding="utf-8") as f:
            script_content = f.read()
    except FileNotFoundError:
        script_content = "(Script file not found)"

    # Combine stdout and stderr for Claude to analyse
    error_output = (run_result["stdout"] + "\n" + run_result["stderr"]).strip()

    prompt = f"""A Playwright pytest test just failed. You are a senior QA engineer diagnosing it.

PYTEST OUTPUT:
{error_output[:4000]}

TEST SCRIPT THAT FAILED:
{script_content[:3000]}

Diagnose the failure. Answer these questions concisely:

1. ROOT CAUSE: What specifically went wrong?
   Options: wrong selector, missing env var, app not available, 
   assertion mismatch, timing issue, network error, import error, other

2. FAILURE TYPE:
   - SCRIPT BUG: The generated code has an error (wrong selector, wrong assertion, etc.)
   - MISSING INFO: A required env var or credential is not set
   - APP ISSUE: The application itself behaved unexpectedly
   - CONFIG ISSUE: Playwright or environment setup problem

3. EXACT FIX NEEDED:
   Give the specific thing that must change. Examples:
   - "Set APP_URL in .env file. Current value is empty."
   - "The selector '.login-btn' does not exist. Use 'button[type=submit]' instead."
   - "Expected text 'Dashboard' but app shows 'Home'. Update the assertion."

4. If env vars are missing — list EXACTLY which ones and what value format they need.

Keep your response under 250 words. Be direct. No fluff."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()