#!/usr/bin/env bash
# Install trigger-org-sync.yml into all member repos for each GitHub org under ~/github/*
set -euo pipefail

GITHUB_ROOT="${GITHUB_ROOT:-$HOME/github}"
ORGS=(semcod wronai maskservice oqlos tellmesh markpact zlecenia stream-ware)
NO_PUSH="${NO_PUSH:-}"

for org in "${ORGS[@]}"; do
  root="${GITHUB_ROOT}/${org}"
  script="${root}/.github/org-sync/scripts/bootstrap_triggers.py"
  if [[ ! -f "$script" ]]; then
    echo "Skip $org (missing $script)" >&2
    continue
  fi
  echo "=== bootstrap triggers: $org ==="
  args=(--org "$org" --github-root "$GITHUB_ROOT")
  if [[ -n "$NO_PUSH" ]]; then
    args+=(--no-push)
  fi
  python3 "$script" "${args[@]}" || true
done
