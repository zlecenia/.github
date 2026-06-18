#!/usr/bin/env python3
"""Install trigger-org-sync workflow into all local repos for a GitHub organization."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

TEMPLATE = (Path(__file__).resolve().parent.parent / "templates" / "trigger-org-sync.yml").read_text(
    encoding="utf-8"
)


def git_repos(org_root: Path) -> list[Path]:
    repos = []
    for child in sorted(org_root.iterdir()):
        if child.name == ".github":
            continue
        if child.is_dir() and (child / ".git").exists():
            repos.append(child)
    return repos


def ensure_trigger(repo: Path, org: str, dry_run: bool, no_push: bool) -> str:
    workflow_dir = repo / ".github" / "workflows"
    workflow_path = workflow_dir / "trigger-org-sync.yml"
    content = TEMPLATE.replace("__ORG__", org)
    if workflow_path.exists() and workflow_path.read_text(encoding="utf-8") == content:
        return "unchanged"
    if dry_run:
        return "would_write"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(content, encoding="utf-8")

    subprocess.run(["git", "add", str(workflow_path)], cwd=repo, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
    if not status.stdout.strip():
        return "unchanged"
    subprocess.run(
        ["git", "commit", "-m", "ci: add org metadata sync trigger workflow"],
        cwd=repo,
        check=True,
    )
    if no_push:
        return "committed"
    push = subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
    if push.returncode != 0:
        return f"push_failed: {(push.stderr or push.stdout)[:120]}"
    return "pushed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", required=True)
    parser.add_argument("--github-root", default=str(Path.home() / "github"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-push", action="store_true", help="Commit locally but do not git push")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    org_root = Path(args.github_root) / args.org
    if not org_root.is_dir():
        raise SystemExit(f"Missing org folder: {org_root}")

    repos = git_repos(org_root)
    if args.limit:
        repos = repos[: args.limit]

    stats: dict[str, int] = {}
    for repo in repos:
        result = ensure_trigger(repo, args.org, args.dry_run, args.no_push)
        stats[result] = stats.get(result, 0) + 1
        print(f"{repo.name}: {result}")

    print("SUMMARY", stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
