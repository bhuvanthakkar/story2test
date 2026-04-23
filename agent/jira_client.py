"""
jira_client.py
Replaces trello_reader.py for Story2Test.
Uses Jira REST API v3 directly via requests — library defaults to v2 which is deprecated.
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

JIRA_DOMAIN      = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL       = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN   = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

BASE_URL = f"https://{JIRA_DOMAIN}"


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def _headers() -> dict:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def _validate_env():
    missing = []
    for var in ["JIRA_DOMAIN", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        raise EnvironmentError(
            f"Missing Jira credentials in .env: {', '.join(missing)}"
        )


def get_issues_in_status(status: str = "TO-DO") -> list[dict]:
    """
    Fetch all issues in the project with the given status.
    Uses Jira REST API v3 /search/jql endpoint.
    Returns list of dicts with keys: id, key, name, desc, url
    """
    _validate_env()

    url = f"{BASE_URL}/rest/api/3/search/jql"

    jql = (
        f'project = "{JIRA_PROJECT_KEY}" '
        f'AND status = "{status}" '
        f'ORDER BY created ASC'
    )

    params = {
        "jql":        jql,
        "maxResults": 50,
        "fields":     "summary,description,status"
    }

    response = requests.get(
        url,
        headers=_headers(),
        auth=_auth(),
        params=params
    )
    response.raise_for_status()

    data   = response.json()
    issues = data.get("issues", [])

    result = []
    for issue in issues:
        fields = issue.get("fields", {})

        # Description in API v3 is Atlassian Document Format (ADF)
        # Extract plain text from it
        desc_raw = fields.get("description", None)
        desc     = _extract_text_from_adf(desc_raw)

        result.append({
            "id":   issue["id"],
            "key":  issue["key"],
            "name": fields.get("summary", "Untitled"),
            "desc": desc,
            "url":  f"{BASE_URL}/browse/{issue['key']}",
        })

    return result


def _extract_text_from_adf(adf: dict | None) -> str:
    """
    Jira API v3 returns description as Atlassian Document Format (ADF) — a nested JSON.
    This recursively extracts all plain text from it.
    """
    if not adf:
        return ""

    if isinstance(adf, str):
        return adf

    text_parts = []

    if isinstance(adf, dict):
        # If it's a text node, grab the text
        if adf.get("type") == "text":
            text_parts.append(adf.get("text", ""))

        # Recurse into content array
        for child in adf.get("content", []):
            child_text = _extract_text_from_adf(child)
            if child_text:
                text_parts.append(child_text)

        # Add newline after block-level nodes
        if adf.get("type") in ("paragraph", "heading", "bulletList",
                               "orderedList", "listItem", "codeBlock"):
            text_parts.append("\n")

    return "".join(text_parts).strip()


def post_comment(issue_key: str, text: str) -> None:
    """
    Post a plain text comment on a Jira issue using API v3.
    """
    _validate_env()

    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    # API v3 requires ADF format for comment body
    payload = {
        "body": {
            "type":    "doc",
            "version": 1,
            "content": [
                {
                    "type":    "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(
        url,
        headers=_headers(),
        auth=_auth(),
        json=payload
    )
    response.raise_for_status()
    print(f"   💬 Comment posted to {issue_key}")


def move_card(issue_key: str, target_status: str) -> None:
    """
    Move a Jira issue to a different status via transition.
    """
    _validate_env()

    # Get available transitions
    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    response = requests.get(url, headers=_headers(), auth=_auth())
    response.raise_for_status()

    transitions = response.json().get("transitions", [])

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

    # Apply the transition
    transition_url = f"{BASE_URL}/rest/api/3/issue/{issue_key}/transitions"
    payload = {"transition": {"id": match["id"]}}
    response = requests.post(
        transition_url,
        headers=_headers(),
        auth=_auth(),
        json=payload
    )
    response.raise_for_status()
    print(f"   ➡️  {issue_key} moved to '{target_status}'")


def add_label(issue_key: str, label: str) -> None:
    """Add a label to a Jira issue."""
    _validate_env()

    # First get existing labels
    url = f"{BASE_URL}/rest/api/3/issue/{issue_key}"
    response = requests.get(url, headers=_headers(), auth=_auth())
    response.raise_for_status()

    existing = response.json().get("fields", {}).get("labels", [])

    if label not in existing:
        existing.append(label)
        update_url = f"{BASE_URL}/rest/api/3/issue/{issue_key}"
        payload = {"fields": {"labels": existing}}
        response = requests.put(
            update_url,
            headers=_headers(),
            auth=_auth(),
            json=payload
        )
        response.raise_for_status()
        print(f"   🏷  Label '{label}' added to {issue_key}")