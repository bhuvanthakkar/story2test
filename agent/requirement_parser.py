import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def parse_requirements(card_name: str, card_description: str) -> dict:
    """
    Send card content to Claude → get back structured requirements as JSON.

    Returns a dict with keys:
        summary        : 2-3 sentence plain-English summary
        requirements   : list of extracted functional requirements
        missing_info   : list of things needed for testing but not provided
        has_blockers   : True if critical info is missing (stop the pipeline)
        test_scenarios : list of {id, title, type} dicts
    """

    prompt = f"""You are a senior QA engineer reviewing a user story.

STORY TITLE:
{card_name}

STORY DESCRIPTION:
{card_description if card_description.strip() else "(No description provided)"}

YOUR TASK — analyse this story and return a JSON object with these exact keys:

1. "summary": A 2-3 sentence plain English summary of what this feature does.

2. "requirements": A list of strings — every functional requirement you can extract.
   Example: ["User must be able to log in with email and password",
             "Dashboard must load after successful login"]

3. "missing_info": A list of strings — things you need to test but are NOT provided.
   Always check for:
   - Application URL (where to open the browser)
   - Login credentials for test accounts
   - API endpoints if API testing is needed
   - Test data (e.g. valid/invalid card numbers for payment)
   - Environment name (staging/production)
   Example: ["Application URL not provided",
             "Test user email and password not provided"]

4. "has_blockers": true if missing_info contains anything that would STOP
   you from writing or running tests. false if you have enough to proceed.
   Rule: missing URL or credentials = blocker. Missing nice-to-have detail = not blocker.

5. "test_scenarios": A list of dicts. Write 5-8 scenarios covering:
   - Happy path (main success flow)
   - Negative cases (wrong input, missing fields)
   - Edge cases (boundary values, empty states)
   Each dict must have: "id" (e.g. "TC001"), "title", "type" (happy_path/negative/edge)
   Example: [{{"id": "TC001", "title": "Login with valid credentials", "type": "happy_path"}}]

RESPOND WITH ONLY VALID JSON. No explanation before or after. No markdown code fences."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw_text = response.content[0].text.strip()

    # Handle case where Claude wraps in markdown fences despite instructions
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]   # remove first line (```json)
        raw_text = raw_text.rsplit("```", 1)[0]  # remove closing ```

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # If Claude still didn't return valid JSON, raise with useful message
        raise ValueError(
            f"Claude did not return valid JSON.\n"
            f"Error: {e}\n"
            f"Raw response:\n{raw_text}"
        )

    # Validate all required keys exist
    required_keys = ["summary", "requirements", "missing_info",
                     "has_blockers", "test_scenarios"]
    for key in required_keys:
        if key not in parsed:
            raise ValueError(f"Claude response missing required key: '{key}'")

    return parsed