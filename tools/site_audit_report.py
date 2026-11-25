#!/usr/bin/env python3
"""Render the publish audit as markdown for a human to read (roadmap Step 16).

    python3 tools/site_audit_report.py             # markdown, for the job summary or a terminal
    python3 tools/site_audit_report.py --strict    # exit 1 on a link or audit failure

`--strict` fails on what is unambiguously a bug (unresolved or ambiguous links). Everything else
— keyword hits, design citations, flattened links — is a reading list, not a gate.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

AUDIT = Path(__file__).resolve().parent.parent / "site" / "audit" / "latest.json"


def render(audit: dict) -> str:
    flat = Counter(f["reason"] for f in audit.get("flattened_links", []))
    out = ["## Publish audit", ""]
    out.append(
        f"**{audit['pages']} pages · {audit['sections']} sections · {audit['words']:,} words · "
        f"{audit.get('links', 0):,} links** — rebuilt {audit['generated']}"
    )
    out.append("")
    out.append("| Check | Count |")
    out.append("|---|---|")
    out.append(f"| Unresolved links | **{len(audit['unresolved_links'])}** |")
    out.append(f"| Ambiguous links | **{len(audit['ambiguous_links'])}** |")
    out.append("| Flattened links | "
               + (", ".join(f"{k} {v}" for k, v in sorted(flat.items())) or "0") + " |")
    out.append(f"| Notes not published | {len(audit['skipped_notes'])} |")
    out.append(f"| Earned/sealed sections dropped | {len(audit['dropped_sections'])} |")
    out.append(f"| Lines dropped inside layered sections | {len(audit['dropped_lines'])} |")
    out.append(f"| Engine fields dropped | {len(audit['design_fields'])} |")
    out.append(f"| Design citations scrubbed | {len(audit['internal_references'])} |")
    out.append(f"| Pages without a standfirst | {len(audit['pages_without_summary'])} |")
    out.append(f"| Accounts quoted (testimony) | {len(audit.get('testimony', []))} |")
    out.append("")

    accounts = audit.get("testimony", [])
    if accounts:
        out.append(f"### Testimony ({len(accounts)}) — read for voice, not for leaks")
        out.append("")
        for a in accounts:
            teller = a.get("teller") or "unattributed"
            year = f", CY {a['taken']}" if a.get("taken") else ", **undated**"
            where = f" (volume: {a['collected_on']})" if a.get("collected_on") else ""
            out.append(f"- **{a['page']}** — {teller}{year}{where}")
        unplaced = audit.get("testimony_unplaced", [])
        if unplaced:
            out.append("")
            out.append(f"**Outside every volume ({len(unplaced)}):** "
                       + ", ".join(f"{u['page']} (CY {u['taken']})" for u in unplaced))
        out.append("")

    hits = audit.get("keyword_hits", [])
    out.append(f"### Keyword hits ({len(hits)}) — read these")
    out.append("")
    if hits:
        for hit in hits:
            out.append(f"- `{hit['term']}` in **{hit['page']}**")
    else:
        out.append("None.")
    out.append("")

    refs = audit.get("internal_references", [])
    out.append(f"### Design citations in lore prose ({len(refs)}) — fix at source")
    out.append("")
    if refs:
        for ref in refs:
            out.append(f"- `{ref['note']}` — {ref['text']}")
    else:
        out.append("None.")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Report the publish audit.")
    ap.add_argument("--audit", type=Path, default=AUDIT)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)

    if not args.audit.exists():
        print(f"no audit at {args.audit}: run tools/site_export.py first", file=sys.stderr)
        return 1
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    print(render(audit))

    if args.strict:
        bad = len(audit["unresolved_links"]) + len(audit["ambiguous_links"])
        if bad:
            print(f"\n{bad} broken link(s): fix them before deploying.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
