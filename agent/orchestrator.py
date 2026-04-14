"""
Main agent loop.
This version: reads Trello card → parses requirements → posts summary back.
Future versions will also generate and run tests.
"""
import time
import json
import os
from dotenv import load_dotenv

from trello_reader import (
    get_cards_in_list,
    post_comment,
    move_card,
)
from requirement_parser import parse_requirements

load_dotenv()

# Track which cards we've already processed in this session
processed_card_ids = set()


def format_blocker_comment(parsed: dict) -> str:
    """Format a clear comment when there's not enough info to test"""
    lines = [
        "## 🚫 QA Agent — Blocked",
        "",
        "**Cannot generate tests — the following information is missing:**",
        "",
    ]
    for item in parsed["missing_info"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "**Please update this card with the missing details.**",
        "The agent will pick it up again on the next check.",
        "",
        "---",
        "_Automated by QA Agent Pipeline_",
    ]
    return "\n".join(lines)


def format_requirements_comment(parsed: dict) -> str:
    """Format a summary comment when requirements are understood"""
    lines = [
        "## ✅ QA Agent — Requirements Parsed",
        "",
        f"**Summary:** {parsed['summary']}",
        "",
        "**Requirements identified:**",
    ]
    for req in parsed["requirements"]:
        lines.append(f"- {req}")

    lines += ["", "**Test scenarios planned:**"]
    for scenario in parsed["test_scenarios"]:
        icon = {"happy_path": "✅", "negative": "❌", "edge": "⚠️"}.get(
            scenario["type"], "•"
        )
        lines.append(f"{icon} [{scenario['id']}] {scenario['title']}")

    lines += [
        "",
        "---",
        "_Test case generation starting... (next step)_",
        "_Automated by QA Agent Pipeline_",
    ]
    return "\n".join(lines)


def process_card(card: dict):
    """Run the full pipeline for a single Trello card"""
    card_id   = card["id"]
    card_name = card["name"]
    card_desc = card.get("desc", "")

    print(f"\n{'='*60}")
    print(f"🤖 Processing card: {card_name}")
    print(f"   URL: {card.get('url', 'N/A')}")
    print(f"{'='*60}")

    # ── Step 1: Parse requirements ───────────────────────────
    print("📋 Step 1: Parsing requirements with Claude...")
    try:
        parsed = parse_requirements(card_name, card_desc)
    except Exception as e:
        error_msg = (
            f"## ❌ QA Agent — Error\n\n"
            f"Failed to parse requirements:\n```\n{str(e)}\n```\n\n"
            f"_Automated by QA Agent Pipeline_"
        )
        post_comment(card_id, error_msg)
        print(f"   ❌ Error: {e}")
        return

    print(f"   Summary: {parsed['summary'][:80]}...")
    print(f"   has_blockers: {parsed['has_blockers']}")
    print(f"   Scenarios: {len(parsed['test_scenarios'])}")

    # ── Step 2: Post result back to Trello ──────────────────
    if parsed["has_blockers"]:
        print("   ⚠️  Blockers detected — posting blocked comment")
        comment = format_blocker_comment(parsed)
        post_comment(card_id, comment)
        # Add a red label so the team can see it's blocked
        print("   Posting blocker comment to card...")
    else:
        print("   ✅ Requirements clear — posting summary comment")
        comment = format_requirements_comment(parsed)
        post_comment(card_id, comment)
        # Move card to In Progress
        move_card(card_id, "In Progress")
        print("   Card moved to: In Progress")

    print(f"   Done! Open your Trello card to see the comment.")


def run_once():
    """Process all cards currently in Backlog — run this manually to test"""
    print("🚀 QA Agent — Single run mode")
    cards = get_cards_in_list("Backlog")
    print(f"Found {len(cards)} card(s) in Backlog")
    if not cards:
        print("No cards to process. Create a card in the Backlog list and run again.")
        return
    for card in cards:
        process_card(card)


def run_polling_loop(interval_seconds: int = 60):
    """Continuously poll Trello every N seconds"""
    print(f"🚀 QA Agent — Polling mode (every {interval_seconds}s)")
    print("   Press Ctrl+C to stop\n")
    while True:
        cards = get_cards_in_list("Backlog")
        new_cards = [c for c in cards if c["id"] not in processed_card_ids]
        if new_cards:
            print(f"Found {len(new_cards)} new card(s)")
            for card in new_cards:
                processed_card_ids.add(card["id"])
                process_card(card)
        else:
            print(f"No new cards. Next check in {interval_seconds}s...", end="\r")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    # Change to run_polling_loop() when you want continuous mode
    run_once()