"""
Formats a rich Trello comment with the full pipeline results.
"""

from datetime import datetime


def build_trello_report(
    run_result: dict,
    diagnosis: str,
    tc_filepath: str,
    script_path: str,
    card_name: str,
) -> str:
    """Build a formatted Markdown comment for the Trello card."""

    ts  = run_result.get("timestamp", datetime.now().isoformat())[:19]
    summ = run_result.get("test_summary", {})

    passed  = summ.get("passed", 0)
    failed  = summ.get("failed", 0)
    errors  = summ.get("error", 0)
    total   = passed + failed + errors

    if run_result["success"]:
        header = "## ✅ QA Agent — All Tests Passed"
        status_line = f"**{passed}/{total} tests passed**"
    else:
        header = "## ❌ QA Agent — Tests Failed"
        status_line = (
            f"**{passed} passed · {failed} failed · {errors} errors** "
            f"(out of {total} total)"
        )

    lines = [
        header,
        "",
        f"**Story:** {card_name}",
        f"**Run at:** {ts}",
        f"**Result:** {status_line}",
        "",
    ]

    # Show pytest output (last 1500 chars to avoid Trello comment length limits)
    stdout = run_result.get("stdout", "").strip()
    if stdout:
        excerpt = stdout[-1500:] if len(stdout) > 1500 else stdout
        lines += [
            "### Pytest Output",
            "```",
            excerpt,
            "```",
            "",
        ]

    # Show AI diagnosis only on failure
    if not run_result["success"] and diagnosis:
        lines += [
            "### 🔍 AI Failure Diagnosis",
            diagnosis,
            "",
        ]

        stderr = run_result.get("stderr", "").strip()
        if stderr:
            err_excerpt = stderr[-500:] if len(stderr) > 500 else stderr
            lines += [
                "### Raw Error",
                "```",
                err_excerpt,
                "```",
                "",
            ]

    lines += [
        "---",
        f"*Test cases: `{tc_filepath}`*",
        f"*Script: `{script_path}`*",
        f"*Automated by QA Agent Pipeline*",
    ]

    return "\n".join(lines)