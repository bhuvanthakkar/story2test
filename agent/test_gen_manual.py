from requirement_parser import parse_requirements
from test_cases_generator import generate_test_cases

# Step 1: Parse a card
parsed = parse_requirements(
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

# Step 2: Generate test cases from the parsed result
filepath, content = generate_test_cases(parsed, card_id="TEST001")

if filepath:
    print(f"\nSaved to: {filepath}")
    print("\nFirst 500 chars of output:")
    print(content[:500])
else:
    print(f"\nBLOCKED:\n{content}")