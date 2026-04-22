from requirement_parser import parse_requirements
import json

# Test 1: A good story (should NOT have blockers)
print("=" * 60)
print("TEST 1: Good story with enough info")
print("=" * 60)

result = parse_requirements(
    card_name="Login page | Username and password validation",
    card_description="""
    Valid credentials redirect to inventory  (/inventory).
    Wrong password shows: "Username and Password do not match any user"
    Empty fields show: "Username / Password is required"

    App URL: https://www.saucedemo.com/inventory.html
    Test Username : standard_user
    Test password: secret_sauce
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