#!/usr/bin/env bash
# Deploy org-sync toolkit to all GitHub organizations under ~/github/*
set -euo pipefail

GITHUB_ROOT="${GITHUB_ROOT:-$HOME/github}"
SOURCE="${GITHUB_ROOT}/semcod/.github"
ORGS=(semcod wronai maskservice oqlos tellmesh markpact zlecenia stream-ware)

if [[ ! -d "$SOURCE/org-sync" ]]; then
  echo "Missing source toolkit: $SOURCE/org-sync" >&2
  exit 1
fi

for org in "${ORGS[@]}"; do
  target="${GITHUB_ROOT}/${org}/.github"
  echo "=== $org ==="

  if [[ ! -d "$target/.git" ]]; then
    mkdir -p "$target"
    if gh api "repos/${org}/.github" >/dev/null 2>&1; then
      git clone "git@github.com:${org}/.github.git" "$target"
    else
      echo "Creating ${org}/.github on GitHub"
      gh repo create "${org}/.github" --public --description "Organization profile and metadata automation"
      git clone "git@github.com:${org}/.github.git" "$target"
    fi
  fi

  mkdir -p "$target/profile" "$target/.github/workflows"
  rsync -a --delete \
    --exclude 'config/orgs/' \
    "$SOURCE/org-sync/" "$target/org-sync/"
  mkdir -p "$target/org-sync/config/orgs"
  if [[ "$(realpath "$SOURCE")" != "$(realpath "$target")" ]]; then
    if [[ -f "$SOURCE/org-sync/config/orgs/${org}.yaml" ]]; then
      cp "$SOURCE/org-sync/config/orgs/${org}.yaml" "$target/org-sync/config/orgs/${org}.yaml"
    else
      cat >"$target/org-sync/config/orgs/${org}.yaml" <<EOF
org: ${org}
tagline: "Projects in the ${org} GitHub organization."
homepage_base: https://${org}.github.io
default_topics:
  - ${org}
EOF
    fi
  fi
  if [[ "$(realpath "$SOURCE")" != "$(realpath "$target")" ]]; then
    cp "$SOURCE/.github/workflows/org-metadata-sync.yml" "$target/.github/workflows/org-metadata-sync.yml"
  fi

  git -C "$target" add -A
  if git -C "$target" diff --cached --quiet; then
    echo "No changes for $org/.github"
  else
    git -C "$target" commit -m "ci: add org-sync automation for metadata and profile README"
    git -C "$target" push -u origin main || git -C "$target" push -u origin HEAD:main
  fi
done

echo "Done. Set organization secret ORG_SYNC_PAT on each org, then run bootstrap_triggers.py per org."
