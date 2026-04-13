from requirement_parser import parse_requirements
import json

# Test 1: A good story (should NOT have blockers)
print("=" * 60)
print("TEST 1: Good story with enough info")
print("=" * 60)

result = parse_requirements(
    card_name="User Login Feature",
    card_description="""
    As a user, I want to log in to the application using my email and password.

    Acceptance Criteria:
    - Valid email + password should redirect to the dashboard
    - Invalid credentials should show error message "Invalid email or password"
    - Empty fields should show "This field is required"
    - Forgot Password link should be visible on the login page

    App URL: https://practice.expandtesting.com/login
    Test email: practice@expandtesting.com
    Test password: SuperSecretPassword123
    """
)

print(json.dumps(result, indent=2))
print(f"\nhas_blockers: {result['has_blockers']}")
print(f"Scenarios found: {len(result['test_scenarios'])}")

# Test 2: A vague story (should HAVE blockers)
print("\n" + "=" * 60)
print("TEST 2: Vague story — should detect blockers")
print("=" * 60)

result2 = parse_requirements(
    card_name="Fix the payment page",
    card_description="The payment page is broken, please fix and test it."
)

print(json.dumps(result2, indent=2))
print(f"\nhas_blockers: {result2['has_blockers']}")
print(f"Missing info: {result2['missing_info']}")