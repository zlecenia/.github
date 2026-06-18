# Org metadata sync

Automated GitHub organization maintenance:

- repository **description**
- **homepage** (`https://<org>.github.io/<repo>/`)
- **topics**
- **GitHub Pages** (public repos)
- organization **profile README** (`profile/README.md`)

## Triggers

1. Any member repo push to `main`/`master` dispatches `org-repo-changed` to `<org>/.github`
2. Scheduled backstop every 6 hours
3. Manual `workflow_dispatch`

## Secrets

Set organization secret **`ORG_SYNC_PAT`** (fine-grained or classic PAT):

- `repo` (all org repos)
- `admin:org` (edit repo metadata)
- `workflow` (dispatch from child repos)

## Local run

```bash
cd org-sync
pip install -r requirements.txt
GH_TOKEN=... python sync.py --org semcod
python sync.py --org semcod --repository goal --dry-run
```

## Bootstrap child repo trigger

```bash
python scripts/bootstrap_triggers.py --org semcod --github-root ~/github
```
