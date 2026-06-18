"""Generate organization profile README (profile/README.md)."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from config import OrgConfig

# Optional per-repo category hints (extend over time per org).
CATEGORY_HINTS: dict[str, str] = {
    "code2llm": "Code Analysis",
    "code2logic": "Code Analysis",
    "koru": "Automation",
    "goal": "Developer Tools",
    "planfile": "Automation",
    "pyqual": "Quality",
    "nlp2cmd": "NLP & Voice",
    "curllm": "LLM & Agents",
    "prellm": "LLM & Agents",
    "mcp": "DevOps",
    "doql": "Quality",
    "testql": "Testing",
}


def _lang(repo: dict) -> str:
    lang = repo.get("primaryLanguage") or {}
    return (lang.get("name") if isinstance(lang, dict) else None) or "—"


def _short_desc(desc: str | None, fallback: str) -> str:
    text = (desc or fallback or "").strip()
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    text = re.sub(r"\s+", " ", text)
    if len(text) > 140:
        text = text[:137].rsplit(" ", 1)[0] + "…"
    return text or fallback


def generate_profile_markdown(org_cfg: OrgConfig, repos: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for repo in sorted(repos, key=lambda r: r["name"].lower()):
        name = repo["name"]
        if name == ".github":
            continue
        cat = CATEGORY_HINTS.get(name.lower()) or CATEGORY_HINTS.get(name) or "Projects"
        grouped[cat].append(repo)

    lines = [
        f"# {org_cfg.org if org_cfg.org != 'semcod' else 'Semcod'}",
        "",
        f"[![Organization](https://img.shields.io/badge/GitHub-{org_cfg.org}-black.svg)](https://github.com/{org_cfg.org})",
        f"[![Projects](https://img.shields.io/badge/projects-{len(repos)}-blue.svg)](https://github.com/{org_cfg.org}?tab=repositories)",
        '[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)',
        "",
        org_cfg.tagline,
        "",
        "---",
        "",
        "## Projekty",
        "",
    ]

    for cat in sorted(grouped.keys()):
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| Projekt | Opis | Język |")
        lines.append("|---------|------|-------|")
        for repo in grouped[cat]:
            name = repo["name"]
            desc = _short_desc(repo.get("description"), "Project in the organization ecosystem.")
            homepage = repo.get("homepageUrl") or f"{org_cfg.homepage_base}/{name}/"
            lines.append(f"| [{name}]({homepage}) | {desc} | {_lang(repo)} |")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Statystyki",
            "",
            f"- **Łącznie projektów**: {len([r for r in repos if r['name'] != '.github'])}",
            f"- **Strony projektów**: `{org_cfg.homepage_base}/<repo>/`",
            "",
            f"_Ostatnia aktualizacja: {date.today().isoformat()}_",
            "",
        ]
    )
    return "\n".join(lines)
