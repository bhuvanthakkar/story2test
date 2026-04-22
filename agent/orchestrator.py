"""
Main QA Agent orchestrator.
Full pipeline: Trello card → parse → test cases → script → run → report
"""

import time
import os
from dotenv import load_dotenv

from trello_reader import (
    get_cards_in_list,
    post_comment,
    move_card,
)
from requirement_parser import parse_requirements
from test_cases_generator import generate_test_cases
from automation_script_writer import write_playwright_script
from script_runner import run_test_script, diagnose_failure
from reporter import build_trello_report

load_dotenv()

# Track processed cards in this session (reset on restart)
processed_card_ids: set = set()


def process_card(card: dict):
    """Run the full 5-step QA agent pipeline for one card."""

    card_id   = card["id"]
    card_name = card.get("name", "Untitled")
    card_desc = card.get("desc", "")

    print(f"\n{'='*60}")
    print(f"🤖 Card: {card_name}")
    print(f"{'='*60}")

    # ── Step 1: Parse requirements ───────────────────────────
    print("📋 Step 1 — Parsing requirements...")
    try:
        parsed = parse_requirements(card_name, card_desc)
    except Exception as e:
        post_comment(card_id,
            f"## ❌ QA Agent — Parse Error\n\n```\n{e}\n```\n\n"
            f"*Automated by QA Agent Pipeline*")
        print(f"   ERROR: {e}")
        return

    print(f"   Summary: {parsed['summary'][:70]}...")
    print(f"   Blockers: {parsed['has_blockers']}")

    # Early exit if critical info missing
    if parsed["has_blockers"]:
        blocker_comment = (
            "## 🚫 QA Agent — Blocked\n\n"
            "**Cannot proceed — missing critical information:**\n\n"
        )
        for item in parsed["missing_info"]:
            blocker_comment += f"- {item}\n"
        blocker_comment += (
            "\nPlease update this card with the missing details.\n"
            "The agent will retry on the next check.\n\n"
            "*Automated by QA Agent Pipeline*"
        )
        post_comment(card_id, blocker_comment)
        print("   ⚠️  Blockers found — posted to card and stopping.")
        return

    # Post requirements summary
    req_lines = "\n".join(f"- {r}" for r in parsed["requirements"])
    sc_lines  = "\n".join(
        f"- [{s['id']}] {s['title']} ({s['type']})"
        for s in parsed["test_scenarios"]
    )
    post_comment(card_id,
        f"## 📋 QA Agent — Requirements Parsed\n\n"
        f"**Summary:** {parsed['summary']}\n\n"
        f"**Requirements:**\n{req_lines}\n\n"
        f"**Test Scenarios ({len(parsed['test_scenarios'])}):**\n{sc_lines}\n\n"
        f"*Generating test cases next...*"
    )

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

    print("📨 Posting final report to Trello...")
    report = build_trello_report(
        run_result, diagnosis, tc_filepath, script_path, card_name
    )
    post_comment(card_id, report)

    # Move card to Done or keep In Progress based on result
    final_list = "Done" if run_result["success"] else "In Progress"
    move_card(card_id, final_list)

    status = "✅ PASSED" if run_result["success"] else "❌ FAILED"
    print(f"\n   {status} — Results posted to Trello card.")
    print(f"   Card URL: {card.get('url', 'N/A')}")


def run_once():
    """Process all cards in Backlog — run once manually."""
    print("🚀 QA Agent — Single Run")
    cards = get_cards_in_list("Backlog")
    print(f"   Cards in Backlog: {len(cards)}")
    if not cards:
        print("   No cards found. Create one and run again.")
        return
    for card in cards:
        process_card(card)


def run_polling_loop(interval_seconds: int = 60):
    """Poll Trello every N seconds for new Backlog cards."""
    print(f"🚀 QA Agent — Polling every {interval_seconds}s (Ctrl+C to stop)\n")
    while True:
        try:
            cards = get_cards_in_list("Backlog")
            new = [c for c in cards if c["id"] not in processed_card_ids]
            if new:
                print(f"\nNew card(s) found: {len(new)}")
                for card in new:
                    processed_card_ids.add(card["id"])
                    process_card(card)
            else:
                print(f"  Waiting... ({interval_seconds}s) ", end="\r")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n\nAgent stopped.")
            break


if __name__ == "__main__":
    run_once()         # Change to run_polling_loop() for continuous mode
