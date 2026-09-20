# Releasing `sha-claim` to PyPI

## One-time setup (Trusted Publishing — no tokens)

1. Sign in at https://pypi.org → **Your projects → Publishing → Add a new pending publisher**:
   - PyPI project name: `sha-claim`
   - Owner: `kahdichienja` · Repository: `rocket`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
2. In GitHub → repo **Settings → Environments → New environment** named `pypi`
   (optionally add yourself as a required reviewer so a tag push waits for your approval).

## Every release

```bash
# 1. bump version in pyproject.toml AND src/sha_claim/__init__.py; add a CHANGELOG section
# 2. make check                      # ruff, mypy, import-linter, pytest
git commit -am "release 0.1.0"
git push origin main
git tag v0.1.0 && git push origin v0.1.0   # → .github/workflows/publish.yml builds, checks, publishes
```

The workflow refuses to publish if the tag and `pyproject.toml` version disagree.

## Manual fallback (API token)

```bash
python -m build && twine check dist/*
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-… twine upload dist/*
```
Use a token scoped to the project after the first upload; never commit it.

## Consumers

After publishing, NaCare's `requirements.txt` becomes simply `sha-claim==0.1.2`.
