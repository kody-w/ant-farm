#!/usr/bin/env python3
"""harvest_pheromones.py — snapshot ant-pheromone labeled issues as static data.

index.html's refreshPheromones() used to anonymously read labeled issues via
the GitHub issues API on every page load and every 30s poll thereafter
(cachedGhJson's localStorage fallback softens repeat visits but the live
call still fires first every time). This harvester makes that call here in
CI, on a schedule, and commits the result trimmed to the fields the page
reads, in the same per-issue shape the issues API returns for those fields.
Dropping a new pheromone still opens github.com/issues/new in a new tab —
that write path is untouched; only the read path moves off api.github.com.
Article XXIV (the Static Data Covenant, kody-w/RAR CONSTITUTION.md).

Non-fatal by design: an API problem leaves the existing snapshot untouched.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "state" / "pheromones.json"
REPO = "kody-w/ant-farm"
LABEL = "ant-pheromone"
SRC = f"https://api.github.com/repos/{REPO}/issues?labels={LABEL}&state=all&per_page=100"


def main():
    req = urllib.request.Request(SRC, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ant-farm-pheromone-harvester",
        **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
           if os.environ.get("GITHUB_TOKEN") else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            issues = json.load(r)
    except Exception as e:
        print(f"· upstream unreadable ({type(e).__name__}) — existing snapshot left untouched")
        return 0

    if not isinstance(issues, list):
        print("· unexpected response shape — existing snapshot left untouched")
        return 0

    snapshot = [
        {
            "number": i.get("number"),
            "html_url": i.get("html_url"),
            "created_at": i.get("created_at"),
            "body": i.get("body"),
        }
        for i in issues
        if isinstance(i, dict)
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, indent=1) + "\n")
    print(f"✓ {OUT.relative_to(ROOT)} — {len(snapshot)} {LABEL} issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
