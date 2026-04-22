#We are deprecating the old Trello Support, as it was a pilot project just to try hands-on, with this now we're adding support for Atlassian Jira

"""
Main Story2Test orchestrator.
Full pipeline: Jira issue → parse → Move from TO-DO to IN PROGRESS → test cases → script → run → report → Move to DONE
"""



import time
import os
from dotenv import load_dotenv

from jira_client import (
    get_issues_in_status,
    post_comment,
    move_card,
)
from requirement_parser import parse_requirements
from test_cases_generator import generate_test_cases
from automation_script_writer import write_playwright_script
from script_runner import run_test_script, diagnose_failure
from reporter import build_trello_report as build_report, build_requirements_comment, build_blocker_comment

load_dotenv()

# Track processed issues in this session (reset on restart)
processed_issue_keys: set = set()


def process_issue(issue: dict):
    """Run the full 5-step Story2Test pipeline for one Jira issue."""

    card_id   = issue["key"]
    card_name = issue.get("name", "Untitled")
    card_desc = issue.get("desc", "")

    print(f"\n{'='*60}")
    print(f"🤖 Issue: {card_name}")
    print(f"{'='*60}")

    # ── Step 1: Parse requirements ───────────────────────────
    print("📋 Step 1 — Parsing requirements...")
    try:
        parsed = parse_requirements(card_name, card_desc)
    except Exception as e:
        post_comment(card_id,
            f"## ❌ Story2Test — Parse Error\n\n```\n{e}\n```\n\n"
            f"*Automated by Story2Test*")
        print(f"   ERROR: {e}")
        return

    print(f"   Summary: {parsed['summary'][:70]}...")
    print(f"   Blockers: {parsed['has_blockers']}")

    # Early exit if critical info missing
    if parsed["has_blockers"]:
        post_comment(card_id, build_blocker_comment(parsed["missing_info"]))
        print("   ⚠️  Blockers found — posted to issue and stopping.")
        return

    # Post requirements summary
    post_comment(card_id, build_requirements_comment(parsed))

    # ── Step 2: Generate test cases ──────────────────────────
    print("✍️  Step 2 — Generating test cases...")
    tc_filepath, tc_content = generate_test_cases(parsed, card_id)

    if tc_filepath is None:
        post_comment(card_id, tc_content)
        return

    post_comment(card_id,
        f"✅ **Test cases written** — {len(parsed['test_scenarios'])} scenarios\n"
        f"Saved: `{tc_filepath}`\n\n*Writing automation script...*"
    )

    # ── Step 3: Write Playwright script ──────────────────────
    print("🔧 Step 3 — Writing Playwright script...")
    script_path = write_playwright_script(parsed, tc_content, card_id)

    post_comment(card_id,
        f"🤖 **Automation script generated**\n"
        f"Saved: `{script_path}`\n\n*Running tests now...*"
    )
    move_card(card_id, "In Progress")

    # ── Step 4: Run the tests ─────────────────────────────────
    print("▶️  Step 4 — Running tests...")
    run_result = run_test_script(script_path, card_id)

    summary = run_result["test_summary"]
    print(f"   Passed: {summary['passed']}  "
          f"Failed: {summary['failed']}  "
          f"Errors: {summary['error']}")

    # ── Step 5: Diagnose failures + report ───────────────────
    diagnosis = ""
    if not run_result["success"]:
        print("🔍 Step 5 — Diagnosing failure with Claude...")
        diagnosis = diagnose_failure(run_result, script_path)

    print("📨 Posting final report to Jira...")
    report = build_report(
        run_result, diagnosis, tc_filepath, script_path, card_name
    )
    post_comment(card_id, report)

    # Move issue to Done or keep In Progress based on result
    final_list = "Done" if run_result["success"] else "In Progress"
    move_card(card_id, final_list)

    status = "✅ PASSED" if run_result["success"] else "❌ FAILED"
    print(f"\n   {status} — Results posted to Jira issue.")
    print(f"   Issue URL: {issue.get('url', 'N/A')}")


def run_once():
    """Process all issues in To Do — run once manually."""
    print("🚀 Story2Test Agent — Single Run")
    issues = get_issues_in_status("TO-DO")
    print(f"   Issues in To Do: {len(issues)}")
    if not issues:
        print("   No issues found. Create one in Jira TO-DO and run again.")
        return
    for issue in issues:
        process_issue(issue)


def run_polling_loop(interval_seconds: int = 60):
    """Poll Jira every N seconds for new To Do issues."""
    print(f"🚀 Story2Test — Polling every {interval_seconds}s (Ctrl+C to stop)\n")
    while True:
        try:
            issues = get_issues_in_status("To Do")
            new = [i for i in issues if i["key"] not in processed_issue_keys]
            if new:
                print(f"\nNew issue(s) found: {len(new)}")
                for issue in new:
                    processed_issue_keys.add(issue["key"])
                    process_issue(issue)
            else:
                print(f"  Waiting... ({interval_seconds}s) ", end="\r")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\nStory2Test Agent stopped.")
            break


if __name__ == "__main__":
    run_once()         # Change to run_polling_loop() for continuous mode