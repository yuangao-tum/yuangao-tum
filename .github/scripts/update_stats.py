#!/usr/bin/env python3
"""Refresh the stats block in README.md between the STATS markers.

The repo list is derived from the shields.io star badges already present in the
README, so adding a paper to Selected Work automatically adds it to the totals.
Aborts without writing if any API call fails, so a transient outage can never
publish a wrong number.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

README = "README.md"
START = "<!-- STATS:START -->"
END = "<!-- STATS:END -->"
BADGE = re.compile(r"img\.shields\.io/github/stars/([\w.-]+)/([\w.-]+)")

USER = os.environ.get("USER_LOGIN") or os.environ.get("USER") or "yuangao-tum"
TOKEN = os.environ.get("GH_TOKEN", "")


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-profile-stats",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    readme = open(README, encoding="utf-8").read()

    repos = list(dict.fromkeys(BADGE.findall(readme)))
    if not repos:
        sys.exit("No star badges found in README — refusing to write an empty total.")

    try:
        stars = sum(api(f"/repos/{o}/{r}")["stargazers_count"] for o, r in repos)
        user = api(f"/users/{USER}")
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError) as e:
        sys.exit(f"GitHub API failed ({e}) — leaving README untouched.")

    block = (
        f"{START}\n"
        '<p align="center">\n'
        f"  <b>★ {stars}</b> stars across project repos"
        f" &nbsp;·&nbsp; <b>{user['followers']}</b> followers"
        f" &nbsp;·&nbsp; <b>{user['public_repos']}</b> public repos\n"
        "</p>\n"
        f"{END}"
    )

    if START not in readme or END not in readme:
        sys.exit("STATS markers missing from README.")

    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END), lambda _: block, readme, flags=re.S
    )
    if updated != readme:
        open(README, "w", encoding="utf-8").write(updated)
        print(f"Updated: {stars} stars across {len(repos)} repos.")
    else:
        print(f"Unchanged: {stars} stars across {len(repos)} repos.")


if __name__ == "__main__":
    main()
