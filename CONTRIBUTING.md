# Contributing

PRs welcome. Keep it clean.

## Workflow

1. Fork → branch → PR against `main`
2. Keep commits atomic and messages clear (`feat:`, `fix:`, `docs:`)
3. No secrets, keys, or credentials in commits — ever

## Adding a New Deployment Method

- Drop a new script in `scripts/deployment/`
- Document it in `README.md` under **Deployment Methods**
- Add a **Usage** block with CLI example

## Adding a VM Filter / Search Feature

- Extend `scripts/searchvm.sh` or `scripts/builddb.py`
- Keep the `vms.json` schema backward-compatible

## Security Reports

Don't open a public issue for vulnerabilities. DM me directly.
