"""Rewrite the auto-generated pull request block in README.md from the GitHub API.

Run by .github/workflows/update-readme.yml. Standard library only.
"""

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USER = "Manipal03"
LIMIT = 6
# Practice and tutorial repos are real activity but not signal for a reader.
SKIP_REPO = re.compile(r"demo|tutorial|test|activity-log", re.IGNORECASE)
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- prs:start -->", "<!-- prs:end -->"


def search(query):
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": 50}
    )
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
        items = json.load(resp)["items"]
    keep = []
    for item in items:
        repo = item["repository_url"].removeprefix("https://api.github.com/repos/")
        if not SKIP_REPO.search(repo):
            keep.append((repo, item))
    return keep[:LIMIT]


def rows(results, date_key):
    lines = ["| Date | Repository | Pull request |", "|---|---|---|"]
    for repo, item in results:
        title = item["title"].replace("|", "\\|")
        date = (item.get("pull_request", {}).get(date_key) or item["updated_at"])[:10]
        lines.append(f"| {date} | [{repo}](https://github.com/{repo}) | [{title}]({item['html_url']}) |")
    return lines


def build():
    merged = search(f"is:pr is:merged is:public author:{USER}")
    reviewed = search(f"is:pr is:public reviewed-by:{USER} -author:{USER}")

    out = ["**Merged**", ""]
    out += rows(merged, "merged_at") if merged else ["_No public merged pull requests yet._"]
    if reviewed:
        out += ["", "**Reviewed**", ""] + rows(reviewed, "merged_at")
    return "\n".join(out)


def main():
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new = pattern.sub(f"{START}\n{build()}\n{END}", text)
    if new != text:
        README.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    main()
