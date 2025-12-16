import json
from pathlib import Path
import streamlit as st

DEFAULT_LATEST = Path("garam_core/reports/latest.json")

def load_report(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    st.set_page_config(page_title="GaramUI - Reports", layout="wide")
    st.title("GaramUI — Reports")

    path_str = st.text_input("latest.json path", value=str(DEFAULT_LATEST))
    path = Path(path_str)

    if not path.exists():
        st.error(f"File not found: {path}")
        return

    report = load_report(path)
    summary = report.get("summary", {})
    meta = report.get("meta", {})
    kpis = summary.get("kpis", {}) or {}
    checks = report.get("checks", []) or []

    col1, col2, col3 = st.columns([2,2,3])
    with col1:
        st.metric("Status", summary.get("status"))
        st.caption(summary.get("headline", ""))
    with col2:
        st.metric("Trades", kpis.get("trades"))
        st.metric("Win Rate", f"{(kpis.get('win_rate') or 0):.2%}")
    with col3:
        st.write("Meta")
        st.json({
            "run_id": meta.get("run_id"),
            "timestamp_utc": meta.get("timestamp_utc"),
            "mode": meta.get("mode"),
            "git": meta.get("git", {}),
            "data": meta.get("data", {}),
        })

    st.divider()

    st.subheader("Checks")
    # Table-friendly view
    table = []
    for c in checks:
        metrics = c.get("metrics", {}) or {}
        # pick 2 representative metrics
        m_keys = list(metrics.keys())[:2]
        m_preview = ", ".join([f"{k}={metrics[k]}" for k in m_keys]) if m_keys else ""
        table.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "status": c.get("status"),
            "severity": c.get("severity"),
            "metrics_preview": m_preview,
            "evidence_n": len(c.get("evidence_paths", []) or []),
            "logs_n": len(c.get("log_paths", []) or []),
            "tags": ", ".join(c.get("tags", []) or []),
        })

    st.dataframe(table, use_container_width=True)

    st.subheader("Details")
    ids = [c.get("id") for c in checks]
    sel = st.selectbox("Select check", ids, index=0 if ids else None)
    if sel:
        c = next((x for x in checks if x.get("id") == sel), None)
        if c:
            st.markdown(f"### {c.get('id')} — {c.get('name')}")
            st.write({"status": c.get("status"), "severity": c.get("severity")})
            st.markdown("#### Metrics")
            st.json(c.get("metrics", {}))
            st.markdown("#### Notes")
            st.write(c.get("notes", []))
            st.markdown("#### Evidence")
            st.write(c.get("evidence_paths", []))
            st.markdown("#### Logs")
            st.write(c.get("log_paths", []))

if __name__ == "__main__":
    main()
