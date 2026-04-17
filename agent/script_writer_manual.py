from requirement_parser import parse_requirements
from test_cases_generator import generate_test_cases
from automation_script_writer import write_playwright_script

# Parse
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

# Generate test cases
tc_filepath, tc_content = generate_test_cases(parsed, "TEST002")

# Write Playwright script
script_path = write_playwright_script(parsed, tc_content, "TEST002")

print(f"\nScript written to: {script_path}")
print("\nOpening the file so you can read it...")

# Print the first 60 lines of the generated script
with open(script_path) as f:
    lines = f.readlines()
    for i, line in enumerate(lines[:60], 1):
        print(f"{i:3}  {line}", end="")