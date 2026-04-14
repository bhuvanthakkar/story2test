"""
Takes the structured requirements from requirement_parser.py
and asks Claude to expand them into detailed, written test cases.
Saves the output to reports/test_cases_{card_id}.txt
"""

import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_test_cases(parsed: dict, card_id: str) -> tuple[str | None, str]:
    """
    Generate detailed test cases from parsed requirements.

    Returns:
        (filepath, text_content)  on success
        (None, blocker_message)   if has_blockers is True
    """

    # Safety check — should have been caught earlier but double-check
    if parsed.get("has_blockers"):
        blocker_msg = (
            "## 🚫 Blocked — Cannot Generate Test Cases\n\n"
            "Missing critical information:\n"
        )
        for item in parsed.get("missing_info", []):
            blocker_msg += f"- {item}\n"
        blocker_msg += (
            "\nUpdate the Trello card with the missing details "
            "and the agent will retry automatically."
        )
        return None, blocker_msg

    scenarios_json = json.dumps(parsed["test_scenarios"], indent=2)
    requirements_text = "\n".join(
        f"- {r}" for r in parsed["requirements"]
    )

    prompt = f"""You are a senior QA engineer writing detailed test cases.

FEATURE SUMMARY:
{parsed["summary"]}

REQUIREMENTS:
{requirements_text}

TEST SCENARIOS TO EXPAND:
{scenarios_json}

Write a detailed test case document for each scenario above.
For EVERY scenario write the following sections:

---
Test Case ID: [use the id from the scenario]
Title: [use the title]
Type: [use the type: happy_path / negative / edge]
Priority: [High / Medium / Low — use your QA judgment]

Preconditions:
- [List what must be true before the test starts]
- [e.g. "User must not be logged in", "Test account must exist"]

Test Steps:
1. [Exact action to perform]
2. [Next action]
3. [Continue until the test flow is complete]

Expected Result:
[What exactly should happen — be specific about text, URLs, UI changes]

Test Data:
[Any specific inputs, values, or credentials needed for this test]
---

After all test cases, add a section:

## AUTOMATION NOTES
[For each test case, note whether it is:
 - AUTOMATABLE: Yes/No
 - AUTOMATION APPROACH: e.g. "Playwright UI test" or "API test with requests"
 - COMPLEXITY: Low/Medium/High]

Be specific and precise. A junior QA engineer should be able to follow these steps."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    test_cases_text = response.content[0].text.strip()

    # Make sure the reports folder exists
    os.makedirs("reports", exist_ok=True)
    filepath = f"reports/test_cases_{card_id}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Test Cases — Card {card_id}\n\n")
        f.write(test_cases_text)

    print(f"   Test cases saved to: {filepath}")
    return filepath, test_cases_text