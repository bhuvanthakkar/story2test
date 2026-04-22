"""
jira_client.py
Replaces trello_reader.py for Story2Test.
Same function signatures — orchestrator.py changes are minimal.
"""

import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

JIRA_DOMAIN      = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL       = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN   = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")


def _get_client() -> JIRA:
    """Return an authenticated Jira Cloud client."""
    if not all([JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise EnvironmentError(
            "Missing Jira credentials in .env\n"
            "Required: JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN"
        )
    return JIRA(
        server=f"https://{JIRA_DOMAIN}",
        basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
    )


def get_issues_in_status(status: str = "TO-DO") -> list[dict]:
    """
    Fetch all issues in the project with the given status.
    Equivalent to get_cards_in_list() from trello_reader.

    Returns list of dicts with keys: id, key, name, desc, url
    """
    jira = _get_client()

    jql = (
        f'project = "{JIRA_PROJECT_KEY}" '
        f'AND status = "{status}" '
        f'ORDER BY created ASC'
    )

    issues = jira.search_issues(jql, maxResults=50, fields="summary,description,status")

    result = []
    for issue in issues:
        result.append({
            "id":   issue.id,
            "key":  issue.key,                          # e.g. S2T-1
            "name": issue.fields.summary,               # story title
            "desc": issue.fields.description or "",     # story description
            "url":  f"https://{JIRA_DOMAIN}/browse/{issue.key}",
        })

    return result


def post_comment(issue_key: str, text: str) -> None:
    """
    Post a comment on a Jira issue.
    Equivalent to post_comment() from trello_reader.
    """
    jira = _get_client()
    jira.add_comment(issue_key, text)
    print(f"   💬 Comment posted to {issue_key}")


def move_card(issue_key: str, target_status: str) -> None:
    """
    Move a Jira issue to a different status via transition.
    Kept the same name as trello_reader so orchestrator.py needs zero changes.

    Jira uses transitions — we find the one that leads to target status.
    """
    jira = _get_client()
    transitions = jira.transitions(issue_key)

    match = next(
        (t for t in transitions
         if t["to"]["name"].lower() == target_status.lower()),
        None
    )

    if not match:
        available = [t["to"]["name"] for t in transitions]
        print(
            f"   ⚠️  Cannot move {issue_key} to '{target_status}'. "
            f"Available: {available}"
        )
        return

    jira.transition_issue(issue_key, match["id"])
    print(f"   ➡️  {issue_key} moved to '{target_status}'")


def add_label(issue_key: str, label: str) -> None:
    """Add a label to a Jira issue — useful for filtering agent-processed issues."""
    jira = _get_client()
    issue = jira.issue(issue_key)
    existing = list(issue.fields.labels or [])
    if label not in existing:
        existing.append(label)
        issue.update(fields={"labels": existing})
        print(f"   🏷  Label '{label}' added to {issue_key}")