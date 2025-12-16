# scripts/ingest_fear_rss.py
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET
import pandas as pd
import yaml


def fetch(url: str, timeout: int = 15) -> bytes:
    req = Request(url, headers={"User-Agent": "garam-fear-rss/1.0"})
    with urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_rss(xml_bytes: bytes) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    items = []

    # RSS: channel/item
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()

        items.append({
            "title": title,
            "link": link,
            "pubDate_raw": pub,
            "description": desc,
        })

    # Atom fallback: entry
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall(".//a:entry", ns):
            title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = e.find("a:link", ns)
            link = (link_el.get("href") if link_el is not None else "").strip()
            updated = (e.findtext("a:updated", default="", namespaces=ns) or "").strip()
            summary = (e.findtext("a:summary", default="", namespaces=ns) or "").strip()
            items.append({
                "title": title,
                "link": link,
                "pubDate_raw": updated,
                "description": summary,
            })

    return items


def to_ts_kst(pub_raw: str) -> str:
    """
    Best-effort parse to KST ISO string.
    """
    # pandas can parse many RFC formats
    try:
        ts = pd.to_datetime(pub_raw, utc=True, errors="coerce")
        if pd.isna(ts):
            ts = pd.Timestamp.utcnow().tz_localize("UTC")
        ts = ts.tz_convert("Asia/Seoul")
        return ts.isoformat()
    except Exception:
        ts = pd.Timestamp.utcnow().tz_localize("UTC").tz_convert("Asia/Seoul")
        return ts.isoformat()


def main():
    project_root = Path(__file__).resolve().parents[1]
    cfg_path = project_root / "garam_core" / "config" / "rss_sources.yaml"
    data_root = (project_root / "GARAM_Data").resolve()  # 필요 시 paths.yaml과 맞추세요

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    sources = cfg.get("sources", [])

    out_dir = data_root / "raw" / "news" / "rss"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"rss_{pd.Timestamp.now().strftime('%Y%m%d')}.jsonl"

    seen = set()
    # 기존 파일이 있으면 중복 방지
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                obj = json.loads(line)
                key = (obj.get("link") or obj.get("title") or "")
                if key:
                    seen.add(key)
            except Exception:
                pass

    appended = 0
    with out_path.open("a", encoding="utf-8") as f:
        for s in sources:
            name = s["name"]
            url = s["url"]
            try:
                xmlb = fetch(url)
                items = parse_rss(xmlb)
                for it in items:
                    key = it.get("link") or it.get("title") or ""
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    rec = {
                        "provider": name,
                        "title": it.get("title", ""),
                        "link": it.get("link", ""),
                        "published_at": to_ts_kst(it.get("pubDate_raw", "")),
                        "description": it.get("description", ""),
                        "fetched_at": pd.Timestamp.now(tz="Asia/Seoul").isoformat(),
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    appended += 1
            except Exception as e:
                # 수집 실패는 기록만 하고 진행 (raw 수집단에서만 허용)
                err = {
                    "provider": name,
                    "error": f"{type(e).__name__}: {e}",
                    "fetched_at": pd.Timestamp.now(tz="Asia/Seoul").isoformat(),
                }
                f.write(json.dumps(err, ensure_ascii=False) + "\n")

    print(f"[OK] RSS ingested: {out_path} (appended={appended})")


if __name__ == "__main__":
    main()
