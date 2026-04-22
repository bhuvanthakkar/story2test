"""
reporter.py
Formats rich Jira Wiki Markup comments for Story2Test pipeline results.
"""

from datetime import datetime
import re


def _color(text: str, color: str) -> str:
    return f"{{color:{color}}}{text}{{color}}"


def _panel(title: str, content: str, panel_type: str = "info") -> str:
    colors = {
        "info":    ("#E6F3FF", "#F5FAFF"),
        "success": ("#EAF5EA", "#F5FFF5"),
        "note":    ("#FFF8E6", "#FFFDF0"),
        "error":   ("#FFECEC", "#FFF5F5"),
        "warning": ("#FFF8E6", "#FFFDF0"),
    }
    title_bg, bg = colors.get(panel_type, colors["info"])
    return (
        f"{{panel:title={title}|borderStyle=solid|borderColor=#ccc"
        f"|titleBGColor={title_bg}|bgColor={bg}}}\n"
        f"{content}\n"
        f"{{panel}}"
    )


def _code_block(content: str, language: str = "none") -> str:
    return f"{{code:language={language}|borderStyle=solid}}\n{content}\n{{code}}"


def _table(rows: list[tuple]) -> str:
    lines = []
    for i, row in enumerate(rows):
        if i == 0:
            lines.append("|| " + " || ".join(str(c) for c in row) + " ||")
        else:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _clean_diagnosis(text: str) -> str:
    """
    Strip markdown/numbered list formatting from Claude's diagnosis output
    and convert to clean Jira Wiki Markup.
    Claude sometimes returns markdown despite being told not to —
    this normalises it into Jira-friendly plain formatting.
    """
    # Remove markdown bold (**text**) → Jira bold (*text*)
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

    # Remove markdown code fences (```lang ... ```) → Jira code block
    text = re.sub(
        r'```(?:\w+)?\n(.*?)```',
        lambda m: _code_block(m.group(1).strip()),
        text,
        flags=re.DOTALL
    )

    # Remove inline markdown code (`text`) → Jira monospace {{text}}
    text = re.sub(r'`([^`]+)`', r'{{\1}}', text)

    # Clean up excessive nested numbering like "1.\n   1.\n      1."
    # These come from Claude's markdown list rendering
    text = re.sub(r'^\s*\d+\.\s+\d+\.\s+\d+\.\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s{3,}\d+\.\s+', '# ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s{1,2}\d+\.\s+', '# ', text, flags=re.MULTILINE)

    # Remove leading whitespace/indentation artifacts
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        else:
            lines.append('')

    # Collapse 3+ consecutive blank lines into one
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))

    return result.strip()


def build_trello_report(
    run_result: dict,
    diagnosis: str,
    tc_filepath: str,
    script_path: str,
    issue_name: str,
) -> str:
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
        ("Metric",       "Value"),
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
        lines.append(_code_block(excerpt))
        lines.append("")

    # ── AI failure diagnosis ──────────────────────────────────
    if not success and diagnosis:
        clean = _clean_diagnosis(diagnosis)
        lines.append(
            _panel(
                title="🔍 AI Failure Diagnosis",
                content=clean,
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
        ("File",               "Path"),
        ("Test Cases",         f"{tc_filepath}"),
        ("Automation Script",  f"{script_path}"),
    ]))
    lines.append("")

    # ── Footer ────────────────────────────────────────────────
    lines.append("----")
    lines.append(
        _color(
            "_Automated by Story2Test Agent — AI-powered QA Pipeline_",
            "#626F86"
        )
    )

    return "\n".join(lines)


def build_requirements_comment(parsed: dict) -> str:
    lines = []

    lines.append(_color("h2. 📋 Story2Test — Requirements Parsed", "#0052CC"))
    lines.append("")

    lines.append(
        _panel(
            title="Feature Summary",
            content=parsed["summary"],
            panel_type="info"
        )
    )
    lines.append("")

    lines.append("h3. Requirements Identified")
    lines.append("")
    for req in parsed["requirements"]:
        lines.append(f"* {req}")
    lines.append("")

    lines.append("h3. Test Scenarios Planned")
    lines.append("")
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
    lines = []

    lines.append(_color("h2. 🚫 Story2Test — Blocked", "#AE2A19"))
    lines.append("")

    content = "*The following critical information is missing:*\n\n"
    for item in missing_info:
        content += f"* {_color(item, '#AE2A19')}\n"
    content += "\nPlease update this issue and the agent will retry automatically."

    lines.append(
        _panel(
            title="⛔ Missing Information",
            content=content,
            panel_type="error"
        )
    )
    lines.append("")
    lines.append("----")
    lines.append(_color("_Automated by Story2Test Agent_", "#626F86"))

    return "\n".join(lines)