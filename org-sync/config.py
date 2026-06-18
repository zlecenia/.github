"""Load per-organization sync configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_ROOT = Path(__file__).resolve().parent / "config" / "orgs"


@dataclass
class OrgConfig:
    org: str
    tagline: str
    homepage_base: str
    default_topics: list[str] = field(default_factory=list)


def load_org_config(org: str) -> OrgConfig:
    path = CONFIG_ROOT / f"{org}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Missing org config: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return OrgConfig(
        org=data["org"],
        tagline=data["tagline"],
        homepage_base=data["homepage_base"].rstrip("/"),
        default_topics=list(data.get("default_topics") or []),
    )
