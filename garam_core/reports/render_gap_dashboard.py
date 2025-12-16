# garam_core/reports/render_gap_dashboard.py
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
import html


def md_to_basic_html(md: str) -> str:
    """
    Minimal Markdown -> HTML renderer:
      - headers (#, ##, ###)
      - tables (pipe tables) as <pre> (safe & deterministic)
      - code fences ``` -> <pre><code>
      - bullet lines -> <ul><li>
    Keeps it dependency-free.
    """
    lines = md.splitlines()
    out = []
    in_code = False
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        if line.strip().startswith("```"):
            close_ul()
            if not in_code:
                in_code = True
                out.append("<pre><code>")
            else:
                in_code = False
                out.append("</code></pre>")
            continue

        if in_code:
            out.append(html.escape(line))
            continue

        # headers
        if line.startswith("### "):
            close_ul()
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_ul()
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            close_ul()
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
            continue

        # bullets
        if line.strip().startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html.escape(line.strip()[2:])}</li>")
            continue
        else:
            close_ul()

        # tables: keep as pre (stable)
        if "|" in line and line.strip().startswith("|"):
            out.append(f"<pre>{html.escape(line)}</pre>")
            continue

        # paragraphs
        if line.strip() == "":
            out.append("<br>")
        else:
            out.append(f"<p>{html.escape(line)}</p>")

    close_ul()
    return "\n".join(out)


def render_dashboard(md_path: Path, out_path: Path) -> None:
    md = md_path.read_text(encoding="utf-8", errors="replace")
    body = md_to_basic_html(md)

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GAP Dashboard</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1,h2,h3 {{ margin-top: 20px; }}
pre {{ background:#f6f6f6; padding:12px; overflow:auto; }}
code {{ font-family: Consolas, monospace; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")


def main():
    project_root = Path(__file__).resolve().parents[2]
    # Adjust for module run vs direct run
    # If run as module (garam_core.reports.render...), file is inside reports
    reports_dir = project_root / "reports"

    # fallback search
    if not reports_dir.exists() or not list(reports_dir.glob("GAP_Health_Report_*.md")):
        # try directory of this script (garam_core/reports)
        here = Path(__file__).resolve()
        reports_dir = here.parent
        if not reports_dir.exists():
             print(f"[WARN] No reports dir found at {project_root}/reports or {here.parent}")
             return

    md_files = sorted(reports_dir.glob("GAP_Health_Report_*.md"), reverse=True)
    if not md_files:
        print(f"[WARN] No GAP markdown reports found in: {reports_dir}")
        return

    latest = md_files[0]
    out = reports_dir / "GAP_Dashboard_latest.html"
    render_dashboard(latest, out)
    print(f"[OK] Dashboard written: {out}")
    print(f"Source: {latest}")


if __name__ == "__main__":
    main()
