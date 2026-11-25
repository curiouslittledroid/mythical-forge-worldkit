#!/usr/bin/env python3
"""Check every internal link in the built site (roadmap Step 16).

    python3 tools/site_link_check.py              # checks site/dist
    python3 tools/site_link_check.py --dist DIR

Exit code 1 if any internal href/src points at a file that does not exist. External links are
not fetched: this checks the site's own plumbing, not the web.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
SKIP_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")


def targets(path: Path) -> set[str]:
    """Links in the markup, ignoring anything inside a script or a stylesheet."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {html.unescape(m) for m in LINK_RE.findall(BLOCK_RE.sub("", text))}


def resolve(url: str, dist: Path) -> bool:
    url = url.split("#", 1)[0].split("?", 1)[0]
    if not url or url in ("/", ""):
        return (dist / "index.html").exists()
    rel = url.lstrip("/")
    candidate = dist / rel
    if candidate.is_dir():
        return (candidate / "index.html").exists()
    if candidate.is_file():
        return True
    return (dist / rel / "index.html").exists()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Check internal links in the built site.")
    ap.add_argument("--dist", type=Path, default=Path(__file__).resolve().parent.parent / "site" / "dist")
    ap.add_argument("--list", action="store_true", help="list every dead link")
    args = ap.parse_args(argv)

    if not args.dist.exists():
        print(f"no build at {args.dist}; run `npm run build` first", file=sys.stderr)
        return 1

    pages = sorted(args.dist.rglob("*.html"))
    dead: list[tuple[str, str]] = []
    checked = 0
    for page in pages:
        for url in targets(page):
            if url.startswith(SKIP_PREFIXES):
                continue
            checked += 1
            if not resolve(url, args.dist):
                dead.append((page.relative_to(args.dist).as_posix(), url))

    print(f"{len(pages)} pages, {checked} internal links, {len(dead)} dead")
    if dead:
        if args.list:
            for page, url in dead[:200]:
                print(f"  {page} -> {url}")
        else:
            for page, url in dead[:10]:
                print(f"  {page} -> {url}")
            if len(dead) > 10:
                print(f"  … and {len(dead) - 10} more (--list)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
