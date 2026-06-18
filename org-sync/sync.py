#!/usr/bin/env python3
"""Sync GitHub org metadata: descriptions, topics, homepages, Pages, profile README."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from config import load_org_config
from metadata import extract_description, infer_topics, run_gh
from pages import enable_pages, has_pages
from profile import generate_profile_markdown

GITHUB_ROOT = Path(os.environ.get("GITHUB_ROOT", str(Path.home() / "github")))


def list_org_repos(org: str) -> list[dict]:
    out = run_gh(
        ["repo", "list", org, "--limit", "1000", "--json", "name,description,homepageUrl,repositoryTopics,isPrivate,primaryLanguage"],
        check=True,
    )
    return json.loads(out.stdout)


def update_repo_metadata(org: str, name: str, desc: str, homepage: str, topics: list[str], dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] {org}/{name}: desc={desc[:60]}... home={homepage} topics={topics}")
        return

    cmd = ["repo", "edit", f"{org}/{name}", "--description", desc, "--homepage", homepage]
    for topic in topics:
        cmd.extend(["--add-topic", topic])

    proc = run_gh(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"repo edit failed for {org}/{name}: {proc.stderr or proc.stdout}")


def sync_repository(org_cfg, name: str, local_root: Path | None, dry_run: bool) -> dict:
    org = org_cfg.org
    homepage = f"{org_cfg.homepage_base}/{name}/"
    desc, keywords = extract_description(org, name, local_root)
    topics = infer_topics(org, name, desc, keywords, org_cfg.default_topics)

    update_repo_metadata(org, name, desc, homepage, topics, dry_run)

    pages_result = "skip"
    repo_meta = run_gh(["api", f"repos/{org}/{name}", "-q", "{name,isPrivate}"], check=True)
    is_private = json.loads(repo_meta.stdout).get("isPrivate", False)
    if not is_private and not dry_run:
        if not has_pages(org, name):
            pages_result = enable_pages(org, name, "/")

    return {"name": name, "description": desc, "homepageUrl": homepage, "topics": topics, "pages": pages_result}


def write_profile(org_cfg, repos: list[dict], profile_path: Path, dry_run: bool) -> bool:
    content = generate_profile_markdown(org_cfg, repos)
    if profile_path.exists() and profile_path.read_text(encoding="utf-8") == content:
        return False
    if dry_run:
        print(f"[dry-run] would update {profile_path}")
        return True
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(content, encoding="utf-8")
    return True


def commit_profile(repo_root: Path, dry_run: bool) -> None:
    if dry_run:
        return
    status = subprocess.run(["git", "status", "--porcelain", "profile/README.md"], cwd=repo_root, capture_output=True, text=True)
    if not status.stdout.strip():
        print("Profile README unchanged")
        return
    subprocess.run(["git", "add", "profile/README.md"], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "chore(org-sync): refresh organization profile README"],
        cwd=repo_root,
        check=True,
    )
    push = subprocess.run(["git", "push"], cwd=repo_root, capture_output=True, text=True)
    if push.returncode != 0:
        print(push.stderr or push.stdout, file=sys.stderr)
        raise RuntimeError("git push failed for profile README")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync GitHub organization metadata")
    parser.add_argument("--org", required=True, help="GitHub organization login")
    parser.add_argument("--repository", help="Sync single repo name (optional)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-profile", action="store_true")
    parser.add_argument("--github-root", default=str(GITHUB_ROOT))
    args = parser.parse_args()

    org_cfg = load_org_config(args.org)
    local_root = Path(args.github_root) / args.org
    org_dotgithub = Path(os.environ.get("ORG_DOTGITHUB_ROOT", local_root / ".github"))
    toolkit_root = Path(__file__).resolve().parent.parent
    # Always target the synced org's .github repo, not whichever checkout hosts sync.py.
    if org_dotgithub.exists() and (org_dotgithub / ".git").exists():
        dotgithub = org_dotgithub
    elif (toolkit_root / ".git").exists():
        dotgithub = toolkit_root
    else:
        dotgithub = org_dotgithub
    profile_path = dotgithub / "profile" / "README.md"

    repos = list_org_repos(org_cfg.org)
    targets = repos
    if args.repository:
        targets = [r for r in repos if r["name"].lower() == args.repository.lower()]
        if not targets:
            print(f"Repository not found in org: {args.repository}", file=sys.stderr)
            return 1

    updated: list[dict] = []
    for repo in targets:
        name = repo["name"]
        if name == ".github":
            continue
        try:
            result = sync_repository(org_cfg, name, local_root if local_root.exists() else None, args.dry_run)
            updated.append(result)
            print(f"OK {org_cfg.org}/{name}")
            time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {org_cfg.org}/{name}: {exc}", file=sys.stderr)

    if not args.skip_profile:
        fresh = list_org_repos(org_cfg.org)
        for item in updated:
            for repo in fresh:
                if repo["name"] == item["name"]:
                    repo["description"] = item["description"]
                    repo["homepageUrl"] = item["homepageUrl"]
        changed = write_profile(org_cfg, fresh, profile_path, args.dry_run)
        if changed and dotgithub.exists():
            commit_profile(dotgithub, args.dry_run)

    print(json.dumps({"org": org_cfg.org, "synced": len(updated), "dry_run": args.dry_run}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
