"""GitHub Pages helpers: enable site and landing page template."""

from __future__ import annotations

import json
import subprocess

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} · {org}</title>
  <meta name="description" content="{desc}">
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1220; color: #e5e7eb; }}
    main {{ max-width: 760px; margin: 0 auto; padding: 3rem 1.25rem; }}
    h1 {{ font-size: 2rem; margin: 0 0 0.75rem; }}
    p {{ line-height: 1.6; color: #cbd5e1; }}
    .links {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1.5rem; }}
    a {{ color: #93c5fd; text-decoration: none; border: 1px solid #334155; padding: 0.55rem 0.9rem; border-radius: 0.5rem; }}
    .badge {{ display: inline-block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <main>
    <div class="badge">{org} ecosystem</div>
    <h1>{name}</h1>
    <p>{desc}</p>
    <div class="links">
      <a href="project/">Project docs</a>
      <a href="README.md">README</a>
      <a href="https://github.com/{org}/{name}">GitHub</a>
    </div>
  </main>
</body>
</html>
"""


def run_gh(args: list[str], *, check: bool = False, input_data: str | None = None):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check, input=input_data)


def has_pages(org: str, name: str) -> bool:
    return run_gh(["api", f"repos/{org}/{name}/pages", "-q", ".status"], check=False).returncode == 0


def enable_pages(org: str, name: str, path: str = "/") -> str:
    body = json.dumps({"build_type": "legacy", "source": {"branch": "main", "path": path}})
    proc = run_gh(
        ["api", "--method", "POST", f"repos/{org}/{name}/pages", "--input", "-"],
        input_data=body,
    )
    if proc.returncode == 0:
        return "created"
    if "already exists" in (proc.stdout + proc.stderr).lower():
        put = run_gh(
            ["api", "--method", "PUT", f"repos/{org}/{name}/pages", "--input", "-"],
            input_data=body,
        )
        return "updated" if put.returncode == 0 else "put_failed"
    if "does not support github pages" in (proc.stdout + proc.stderr).lower():
        return "private_or_plan"
    return "failed"


def landing_html(org: str, name: str, desc: str) -> str:
    safe = desc.replace('"', "'")
    return LANDING_HTML.format(org=org, name=name, desc=safe)
