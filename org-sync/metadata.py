"""Extract repository descriptions and infer GitHub topics."""

from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

BOILERPLATE = re.compile(
    r"(this directory contains|generated on |when you run `code2llm|## 📁|^\| |git clone <|^<!-- generated)",
    re.I,
)


def run_gh(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check)


def clean_md(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`\"]", "", text)
    text = re.sub(r"\s+# noqa:.*", "", text)
    return re.sub(r"\s+", " ", text).strip()[:350]


def pyproject_meta(path: Path | None) -> tuple[str | None, list[str]]:
    if not path:
        return None, []
    ppt = path / "pyproject.toml"
    if not ppt.exists():
        return None, []
    data = tomllib.loads(ppt.read_text(encoding="utf-8"))
    proj = data.get("project", {})
    keywords = proj.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [keywords]
    return proj.get("description"), [str(k).lower() for k in keywords]


def readme_summary(path: Path | None) -> str | None:
    if not path:
        return None
    readme = path / "README.md"
    if not readme.exists():
        return None
    text = readme.read_text(encoding="utf-8", errors="ignore")
    if "---" in text:
        for line in text.split("---", 1)[1].splitlines():
            s = clean_md(line.strip())
            if len(s) > 50 and not s.startswith("|") and not BOILERPLATE.search(s):
                return s
    for line in text.splitlines():
        s = clean_md(line.strip())
        if len(s) > 50 and not line.strip().startswith("#"):
            return s
    return None


def remote_pyproject_desc(org: str, name: str) -> tuple[str | None, list[str]]:
    proc = run_gh(["api", f"repos/{org}/{name}/contents/pyproject.toml", "--jq", ".content"], check=False)
    if proc.returncode != 0:
        return None, []
    try:
        raw = base64.b64decode(proc.stdout.strip())
        data = tomllib.loads(raw.decode("utf-8"))
        proj = data.get("project", {})
        keywords = proj.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [keywords]
        return proj.get("description"), [str(k).lower() for k in keywords]
    except Exception:
        return None, []


def remote_package_json_desc(org: str, name: str) -> str | None:
    proc = run_gh(["api", f"repos/{org}/{name}/contents/package.json", "--jq", ".content"], check=False)
    if proc.returncode != 0:
        return None
    try:
        pkg = json.loads(base64.b64decode(proc.stdout.strip()).decode())
        return pkg.get("description")
    except Exception:
        return None


def infer_topics(org: str, name: str, desc: str, keywords: list[str], defaults: list[str]) -> list[str]:
    topics = list(defaults)
    text = f"{name} {desc}".lower()
    rules = [
        ("mcp", "mcp"),
        ("llm", "llm"),
        ("nlp", "nlp"),
        ("docker", "docker"),
        ("cli", "cli"),
        ("markdown", "markdown"),
        ("git", "git"),
        ("test", "testing"),
        ("benchmark", "benchmark"),
        ("intent", "intent"),
        ("refactor", "refactoring"),
        ("api", "api"),
        ("firmware", "firmware"),
        ("kvm", "kvm"),
    ]
    for needle, topic in rules:
        if needle in text and topic not in topics:
            topics.append(topic)
    for k in keywords[:8]:
        t = re.sub(r"[^a-z0-9\-]", "-", k.lower())
        t = re.sub(r"-+", "-", t).strip("-")
        if 2 < len(t) < 35 and t not in topics:
            topics.append(t)
    out: list[str] = []
    for t in topics:
        if t not in out:
            out.append(t)
    return out[:12]


def extract_description(
    org: str,
    name: str,
    local_root: Path | None,
    profile_desc: dict[str, str] | None = None,
) -> tuple[str, list[str]]:
    key = name.lower()
    if profile_desc and key in profile_desc:
        return clean_md(profile_desc[key]), []

    local = local_root / name if local_root else None
    if local and not local.exists():
        for child in local_root.iterdir() if local_root and local_root.exists() else []:
            if child.name.lower() == key and child.is_dir():
                local = child
                break

    desc, keywords = pyproject_meta(local)
    if desc:
        return clean_md(desc), keywords
    rd = readme_summary(local)
    if rd:
        return rd, keywords

    desc, keywords = remote_pyproject_desc(org, name)
    if desc:
        return clean_md(desc), keywords
    desc = remote_package_json_desc(org, name)
    if desc:
        return clean_md(desc), keywords
    return clean_md(name.replace("-", " ").title()), keywords
