"""
Takes parsed requirements + test case text and asks Claude
to write a runnable Playwright + pytest Python script.
Saves to tests/generated/test_{card_id}.py
"""

import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def write_playwright_script(
    parsed: dict,
    test_cases_text: str,
    card_id: str
) -> str:
    """
    Ask Claude to write a Playwright test script.
    Returns the filepath of the saved script.
    """

    requirements_text = "\n".join(
        f"- {r}" for r in parsed["requirements"]
    )

    # Limit test cases text to avoid token overflow
    tc_excerpt = test_cases_text[:3000]

    prompt = f"""You are a senior SDET writing a Playwright Python automation script.

FEATURE SUMMARY:
{parsed["summary"]}

REQUIREMENTS:
{requirements_text}

TEST CASES TO AUTOMATE (excerpt):
{tc_excerpt}

Write a complete, runnable Python test file using:
- pytest as the test framework
- playwright.sync_api (sync, not async)
- Page Object Model pattern

STRICT RULES — follow every one of these:

RULE 1 — ENV VARS ONLY, NO HARDCODING:
All URLs, credentials, and environment-specific values MUST come from
os.getenv(). At the top of the file, check for required env vars like this:

    import os
    APP_URL = os.getenv("APP_URL")
    APP_USERNAME = os.getenv("APP_USERNAME")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    
    if not APP_URL:
        raise EnvironmentError(
            "Missing env var: APP_URL\\n"
            "Add to your .env file: APP_URL=https://your-app.com"
        )
    if not APP_USERNAME:
        raise EnvironmentError(
            "Missing env var: APP_USERNAME\\n"
            "Add to your .env file: APP_USERNAME=test@example.com"
        )
    if not APP_PASSWORD:
        raise EnvironmentError(
            "Missing env var: APP_PASSWORD\\n"
            "Add to your .env file: APP_PASSWORD=yourpassword"
        )

RULE 2 — PAGE OBJECT MODEL:
Create a class for the page(s) being tested. Example:

    class LoginPage:
        def __init__(self, page):
            self.page = page
            self.email_input    = page.locator("#email")
            self.password_input = page.locator("#password")
            self.submit_button  = page.locator("button[type='submit']")
            self.error_message  = page.locator(".error-message")

        def navigate(self):
            self.page.goto(APP_URL)

        def login(self, email, password):
            self.email_input.fill(email)
            self.password_input.fill(password)
            self.submit_button.click()

        def get_error_text(self):
            return self.error_message.text_content()

RULE 3 — PYTEST FIXTURES:
Use a pytest fixture for the browser and page setup:

    import pytest
    from playwright.sync_api import sync_playwright

    @pytest.fixture(scope="session")
    def browser():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # headless=False so you see it
            yield browser
            browser.close()

    @pytest.fixture
    def page(browser):
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()

RULE 4 — COMMENTS:
Add a comment above every test explaining what it verifies.

RULE 5 — ASSERTIONS:
Use playwright's expect() for assertions:
    from playwright.sync_api import expect
    expect(page.locator("h1")).to_contain_text("Dashboard")

RULE 6 — AUTOMATE SCENARIOS WHICH FEELS MUST FOR THE MODULE
Write a separate pytest test function for EVERY scenario in the test cases provided.
Try not to skip any scenarios unless looks redudant or one covers as part of another, based on that write all test functions.
Name each function clearly: test_TC001_description, test_TC002_description etc.

RULE 7 — IMPORTABLE dotenv:
Add at the very top of the file:
    from dotenv import load_dotenv
    load_dotenv()

RULE 8 — CLASS ASSERTIONS: Never use to_have_class() with a plain string 
for multi-class elements. Always use re.compile() for partial class matching: 
expect(el).to_have_class(re.compile(r'class-name')). 
Prefer asserting on visible text over CSS classes whenever possible.

RULE 9 — ASSERTIONS MUST MATCH ACTUAL APP BEHAVIOUR:
When asserting error messages, use to_contain_text() with a SHORT substring
not the full exact string. Example:
    WRONG: expect(el).to_contain_text('Username and Password do not match any user')
    RIGHT: expect(el).to_contain_text('do not match')
Short substrings are resilient to prefix changes like 'Epic sadface: ' etc.
Always use the shortest unique meaningful substring of the expected message by which it can be derived that what it is trying to say and prefer short substring as there can be scenarios where UI displayed error and BTS could be different


OUTPUT: Write ONLY the Python code.
No explanation before or after.
No markdown code fences (no ```python).
Start directly with the imports."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}]
    )

    script = response.content[0].text.strip()

    # Clean up markdown fences if Claude adds them despite instructions
    if script.startswith("```"):
        lines = script.split("\n")
        # Remove first line (```python or ```) and last line (```)
        lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        script = "\n".join(lines)

    # Make sure output folder exists
    os.makedirs("tests/generated", exist_ok=True)
    filepath = f"tests/generated/test_{card_id}.py"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"   Script saved to: {filepath}")
    return filepath