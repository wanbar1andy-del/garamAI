"""
GARAM Report v1 - JSON -> Markdown renderer
- markdownlint(MD022/MD032) 규칙 준수: 헤딩/리스트 주변에 빈 줄 포함
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

def _bullet_list(items: list[str]) -> str:
    if not items:
        return "- (none)"
    return "\n".join([f"- {x}" for x in items])

def _checks_section(checks: list[dict[str, Any]]) -> str:
    blocks = []
    for c in checks:
        lines = []
        lines.append(f"### {c.get('id')} — {c.get('name')}")
        lines.append("")
        lines.append(f"- Status: **{c.get('status')}** (severity={c.get('severity')})")
        metrics = c.get("metrics", {}) or {}
        if metrics:
            lines.append("")
            lines.append("**Metrics**")
            lines.append("")
            for k, v in metrics.items():
                lines.append(f"- `{k}`: {v}")
        notes = c.get("notes", []) or []
        if notes:
            lines.append("")
            lines.append("**Notes**")
            lines.append("")
            lines.append(_bullet_list([str(x) for x in notes]))
        ev = c.get("evidence_paths", []) or []
        if ev:
            lines.append("")
            lines.append("**Evidence**")
            lines.append("")
            lines.append(_bullet_list(ev))
        lg = c.get("log_paths", []) or []
        if lg:
            lines.append("")
            lines.append("**Logs**")
            lines.append("")
            lines.append(_bullet_list(lg))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)

def render_markdown(report: Dict[str, Any]) -> str:
    meta = report.get("meta", {})
    summary = report.get("summary", {})
    kpis = summary.get("kpis", {}) or {}
    key_points = summary.get("key_points", []) or []
    checks = report.get("checks", []) or []

    key_points_md = _bullet_list([str(x) for x in key_points])

    md = f"""# {summary.get('headline', '(no headline)')}

## Meta

- Run ID: `{meta.get('run_id')}`
- Timestamp (UTC): `{meta.get('timestamp_utc')}`
- Mode: `{meta.get('mode')}`
- Git: `{meta.get('git', {}).get('commit')}` ({meta.get('git', {}).get('branch')}) dirty={meta.get('git', {}).get('dirty')}
- Data: `{meta.get('data', {}).get('universe')}` / `{meta.get('data', {}).get('timeframe')}` / {meta.get('data', {}).get('from')} → {meta.get('data', {}).get('to')}

## Summary

- Status: **{summary.get('status')}**
- KPIs: trades={kpis.get('trades')}, win_rate={kpis.get('win_rate'):.2%}, pnl={kpis.get('pnl')}, mdd={kpis.get('mdd'):.2%}, slippage_bps_est={kpis.get('slippage_bps_est')}

## Key Points

{key_points_md}

## Checks

{_checks_section(checks)}
"""
    return md

def main(json_path: str, md_path: str | None = None) -> Path:
    jp = Path(json_path)
    report = json.loads(jp.read_text(encoding="utf-8"))
    md = render_markdown(report)

    out = Path(md_path) if md_path else jp.with_suffix(".md")
    out.write_text(md, encoding="utf-8")
    return out

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("json_path")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    out = main(args.json_path, args.out)
    print(str(out))
