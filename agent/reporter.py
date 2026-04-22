"""
reporter.py
Formats rich Jira Wiki Markup comments for Story2Test pipeline results.
Jira Wiki Markup renders: panels, code blocks, colors, bold, tables, icons.
"""

from datetime import datetime


def _color(text: str, color: str) -> str:
    """Wrap text in Jira color macro."""
    return f"{{color:{color}}}{text}{{color}}"


def _panel(title: str, content: str, panel_type: str = "info") -> str:
    """
    Jira panel macro — renders as a colored box.
    Types: info (blue), note (yellow), warning (red), success (green)
    """
    return (
        f"{{panel:title={title}|borderStyle=solid|borderColor=#ccc"
        f"|titleBGColor={'#E6F3FF' if panel_type == 'info' else '#EAF5EA' if panel_type == 'success' else '#FFF8E6' if panel_type == 'note' else '#FFECEC'}"
        f"|bgColor={'#F5FAFF' if panel_type == 'info' else '#F5FFF5' if panel_type == 'success' else '#FFFDF0' if panel_type == 'note' else '#FFF5F5'}}}\n"
        f"{content}\n"
        f"{{panel}}"
    )


def _code_block(content: str, language: str = "none") -> str:
    """Jira code block macro."""
    return f"{{code:language={language}|borderStyle=solid}}\n{content}\n{{code}}"


def _table(rows: list[tuple]) -> str:
    """
    Build a Jira wiki table.
    First row = header. Each tuple = one row of cells.
    """
    lines = []
    for i, row in enumerate(rows):
        if i == 0:
            lines.append("|| " + " || ".join(row) + " ||")
        else:
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_trello_report(
    run_result: dict,
    diagnosis: str,
    tc_filepath: str,
    script_path: str,
    issue_name: str,
) -> str:
    """
    Build a rich Jira Wiki Markup comment with full pipeline results.
    Called build_trello_report to keep backward compatibility with orchestrator.py.
    """

    ts      = run_result.get("timestamp", datetime.now().isoformat())[:19]
    summ    = run_result.get("test_summary", {})
    passed  = summ.get("passed", 0)
    failed  = summ.get("failed", 0)
    errors  = summ.get("error", 0)
    total   = passed + failed + errors
    success = run_result["success"]

    lines = []

    # ── Header ───────────────────────────────────────────────
    if success:
        lines.append(_color("h2. ✅ Story2Test — All Tests Passed", "#006644"))
    else:
        lines.append(_color("h2. ❌ Story2Test — Tests Failed", "#AE2A19"))

    lines.append("")
    lines.append(f"*Story:* {issue_name}")
    lines.append(f"*Run at:* {ts}")
    lines.append("")

    # ── Results summary table ─────────────────────────────────
    lines.append("h3. Test Results Summary")
    lines.append("")
    lines.append(_table([
        ("Metric", "Value"),
        ("Total Tests",  _color(str(total),  "#0052CC")),
        ("Passed",       _color(str(passed), "#006644") if passed > 0 else str(passed)),
        ("Failed",       _color(str(failed), "#AE2A19") if failed > 0 else str(failed)),
        ("Errors",       _color(str(errors), "#AE2A19") if errors > 0 else str(errors)),
        ("Status",       _color("PASSED ✅", "#006644") if success else _color("FAILED ❌", "#AE2A19")),
    ]))
    lines.append("")

    # ── Pytest output ─────────────────────────────────────────
    stdout = run_result.get("stdout", "").strip()
    if stdout:
        excerpt = stdout[-2000:] if len(stdout) > 2000 else stdout
        lines.append("h3. Pytest Output")
        lines.append(_code_block(excerpt, language="none"))
        lines.append("")

    # ── AI failure diagnosis ──────────────────────────────────
    if not success and diagnosis:
        lines.append(
            _panel(
                title="🔍 AI Failure Diagnosis",
                content=diagnosis,
                panel_type="warning"
            )
        )
        lines.append("")

        stderr = run_result.get("stderr", "").strip()
        if stderr:
            err_excerpt = stderr[-800:] if len(stderr) > 800 else stderr
            lines.append("h3. Raw Error")
            lines.append(_code_block(err_excerpt))
            lines.append("")

    # ── Artifacts ─────────────────────────────────────────────
    lines.append("h3. Artifacts")
    lines.append(_table([
        ("File", "Path"),
        ("Test Cases",        f"{{monospace}}{tc_filepath}{{monospace}}"),
        ("Automation Script", f"{{monospace}}{script_path}{{monospace}}"),
    ]))
    lines.append("")

    # ── Footer ────────────────────────────────────────────────
    lines.append("----")
    lines.append(
        _color("_Automated by Story2Test Agent — AI-powered QA Pipeline_", "#626F86")
    )

    return "\n".join(lines)


def build_requirements_comment(parsed: dict) -> str:
    """
    Rich comment for when requirements are successfully parsed.
    Called from orchestrator after Step 1.
    """
    lines = []

    lines.append(_color("h2. 📋 Story2Test — Requirements Parsed", "#0052CC"))
    lines.append("")

    # Summary panel
    lines.append(
        _panel(
            title="Feature Summary",
            content=parsed["summary"],
            panel_type="info"
        )
    )
    lines.append("")

    # Requirements list
    lines.append("h3. Requirements Identified")
    for req in parsed["requirements"]:
        lines.append(f"* {req}")
    lines.append("")

    # Test scenarios table
    lines.append("h3. Test Scenarios Planned")
    rows = [("ID", "Title", "Type")]
    for s in parsed["test_scenarios"]:
        icon = {"happy_path": "✅", "negative": "❌", "edge": "⚠️"}.get(s["type"], "•")
        rows.append((
            _color(s["id"], "#0052CC"),
            s["title"],
            f"{icon} {s['type']}"
        ))
    lines.append(_table(rows))
    lines.append("")

    lines.append("----")
    lines.append(_color("_Generating detailed test cases next..._", "#626F86"))

    return "\n".join(lines)


def build_blocker_comment(missing_info: list) -> str:
    """Rich comment for when critical information is missing."""
    lines = []

    lines.append(_color("h2. 🚫 Story2Test — Blocked", "#AE2A19"))
    lines.append("")

    content = "The following critical information is missing and must be added before testing can proceed:\n\n"
    for item in missing_info:
        content += f"* {_color(item, '#AE2A19')}\n"

    lines.append(
        _panel(
            title="⛔ Missing Information",
            content=content,
            panel_type="error"
        )
    )
    lines.append("")
    lines.append("*Action required:* Update this issue with the missing details.")
    lines.append("The Story2Test agent will automatically retry on the next check.")
    lines.append("")
    lines.append("----")
    lines.append(_color("_Automated by Story2Test Agent_", "#626F86"))

    return "\n".join(lines)