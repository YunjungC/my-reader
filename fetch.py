"""
내 리더 - 피드 수집기

feeds.yaml (+ 선택: feeds.opml) 에 있는 RSS/Atom 피드를 읽어
피드마다 최신 top_n 건만 골라 docs/data.json 으로 저장합니다.
docs/index.html 이 이 파일을 읽어 3단 화면으로 보여줍니다.

실행:  python fetch.py
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from calendar import timegm
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import feedparser
import requests
import yaml

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "feeds.yaml"
OPML = ROOT / "feeds.opml"
OUT = ROOT / "docs" / "data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; personal-rss-reader/1.0)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
}
TIMEOUT = 25


# ── 설정 읽기 ──────────────────────────────────────────────

def load_config() -> dict:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    cfg.setdefault("top_n", 10)
    cfg.setdefault("summary_chars", 220)
    feeds = [f for f in (cfg.get("feeds") or []) if f and f.get("url")]

    # Feeder 등에서 내보낸 OPML이 있으면 합칩니다.
    # 이름이나 주소가 feeds.yaml 과 같으면 yaml 쪽을 우선합니다.
    if OPML.exists():
        names = {f.get("name", "").strip().lower() for f in feeds}
        urls = {f["url"].strip() for f in feeds}
        for f in read_opml(OPML):
            if f["url"] in urls or f["name"].strip().lower() in names:
                continue
            feeds.append(f)
            urls.add(f["url"])
            names.add(f["name"].strip().lower())

    cfg["feeds"] = feeds
    return cfg


def read_opml(path: Path) -> list[dict]:
    out = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        print(f"[경고] feeds.opml 을 읽지 못했습니다: {e}", file=sys.stderr)
        return out
    for node in tree.iter("outline"):
        url = node.get("xmlUrl")
        if not url:
            continue
        out.append({
            "name": node.get("title") or node.get("text") or url,
            "url": url.strip(),
            "site": node.get("htmlUrl") or "",
        })
    return out


# ── 정리 도우미 ────────────────────────────────────────────

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean_text(raw: str | None) -> str:
    if not raw:
        return ""
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def truncate(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def unwrap_link(link: str) -> str:
    """구글 알리미 링크(google.com/url?...&url=진짜주소)를 원래 기사 주소로 풀어줍니다."""
    try:
        u = urlparse(link)
        if u.netloc.endswith("google.com") and u.path == "/url":
            q = parse_qs(u.query)
            if q.get("url"):
                return q["url"][0]
    except Exception:
        pass
    return link


def entry_time(e) -> float | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = e.get(key)
        if t:
            return float(timegm(t))
    return None


def feed_id(name: str, url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def item_id(link: str, title: str) -> str:
    return hashlib.sha1((link or title).encode("utf-8")).hexdigest()[:16]


# ── 수집 ──────────────────────────────────────────────────

def fetch_feed(f: dict, top_n: int, summary_chars: int) -> dict:
    resp = requests.get(f["url"], headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)

    if not parsed.entries and not parsed.version:
        raise ValueError("RSS/Atom 형식이 아닙니다 (사이트가 차단·오류 페이지를 돌려줬을 수 있음)")

    items = []
    for e in parsed.entries:
        title = clean_text(e.get("title")) or "(제목 없음)"
        link = unwrap_link(e.get("link") or "")
        summary_raw = e.get("summary") or ""
        if not summary_raw and e.get("content"):
            summary_raw = e["content"][0].get("value", "")
        summary = clean_text(summary_raw)

        # 구글 뉴스처럼 제목 끝에 " - 언론사" 가 붙는 경우 떼어서 출처로 씁니다.
        source = ""
        src = e.get("source")
        if isinstance(src, dict) and src.get("title"):
            source = src["title"].strip()
            if title.endswith(" - " + source):
                title = title[: -len(" - " + source)].rstrip()
        # 요약이 제목을 그대로 반복할 뿐이면 비웁니다.
        if summary and (summary in title or title.startswith(summary[:30])):
            summary = ""

        ts = entry_time(e)
        items.append({
            "id": item_id(link, title),
            "title": title,
            "link": link,
            "summary": truncate(summary, summary_chars),
            "source": source,
            "ts": int(ts) if ts else None,
        })

    items.sort(key=lambda x: x["ts"] or 0, reverse=True)
    site = f.get("site") or parsed.feed.get("link") or ""
    return {"site": site, "items": items[:top_n]}


def main() -> int:
    cfg = load_config()
    top_n, summary_chars = int(cfg["top_n"]), int(cfg["summary_chars"])

    previous = {}
    if OUT.exists():
        try:
            for pf in json.loads(OUT.read_text(encoding="utf-8")).get("feeds", []):
                previous[pf["id"]] = pf
        except Exception:
            pass

    now = int(time.time())
    result = []
    ok = 0
    for f in cfg["feeds"]:
        fid = feed_id(f.get("name", ""), f["url"])
        entry = {
            "id": fid,
            "name": f.get("name") or f["url"],
            "url": f["url"],
            "site": f.get("site", ""),
            "items": [],
            "error": None,
            "last_ok": None,
        }
        try:
            got = fetch_feed(f, top_n, summary_chars)
            entry.update(got)
            entry["last_ok"] = now
            ok += 1
            print(f"[ok]   {entry['name']} — {len(got['items'])}건")
        except Exception as ex:  # 한 피드가 실패해도 나머지는 계속
            msg = f"{type(ex).__name__}: {ex}"[:200]
            entry["error"] = msg
            prev = previous.get(fid)
            if prev:  # 직전에 받아둔 기사는 유지
                entry["items"] = prev.get("items", [])
                entry["last_ok"] = prev.get("last_ok")
                entry["site"] = entry["site"] or prev.get("site", "")
            print(f"[실패] {entry['name']} — {msg}", file=sys.stderr)
        result.append(entry)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"generated_at": now, "top_n": top_n, "feeds": result},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"\n{ok}/{len(result)}개 피드 갱신 → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
