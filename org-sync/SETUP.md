# Org-sync setup

## 1. Organization secret (required)

Create a PAT with scopes: `repo`, `admin:org`, `workflow`.

```bash
gh auth refresh -h github.com -s admin:org,repo,workflow
gh secret set ORG_SYNC_PAT --org semcod --body "$(gh auth token)"
```

Repeat for: `wronai`, `maskservice`, `oqlos`, `tellmesh`, `markpact`, `zlecenia`, `stream-ware`.

The same secret name **`ORG_SYNC_PAT`** must exist at **organization** level (inherited by all repos).

## 2. Central workflow

Repo **`<org>/.github`** contains:

- `.github/workflows/org-metadata-sync.yml` — sync job
- `org-sync/sync.py` — metadata + profile generator
- `profile/README.md` — generated org landing (like [wronai](https://github.com/wronai))

Triggers:

| Event | Action |
|-------|--------|
| Push to any member repo `main`/`master` | `repository_dispatch` → sync that repo + refresh profile |
| Cron `17 */6 * * *` | Full org backstop sync |
| `workflow_dispatch` | Manual full or single-repo sync |

## 3. Member repo trigger

Each repo has `.github/workflows/trigger-org-sync.yml` (bootstrapped).

Install / refresh:

```bash
python3 ~/github/semcod/.github/org-sync/scripts/bootstrap_triggers.py --org semcod --github-root ~/github
bash ~/github/semcod/.github/org-sync/scripts/bootstrap_all_orgs.sh
```

## 4. Deploy toolkit to all orgs

```bash
bash ~/github/semcod/.github/org-sync/scripts/deploy_to_orgs.sh
```

## 5. Manual sync

```bash
cd ~/github/semcod/.github/org-sync
pip install -r requirements.txt
python sync.py --org semcod
python sync.py --org wronai --repository goal
```

## Organizations covered

`semcod`, `wronai`, `maskservice`, `oqlos`, `tellmesh`, `markpact`, `zlecenia`, `stream-ware`

Each maps to `~/github/<org>/*` locally.
