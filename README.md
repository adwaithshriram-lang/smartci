# SmartCI — Continuous Integration Lab

**Student:** Adwaith Shri Ram  
**USN:** 24BTRAO001  
**Coursework:** Smart Build-Cache Invalidation / CI practical

This repository contains a small Python shopping-cart application, pytest unit tests, and a GitHub Actions workflow that runs the tests on every push and pull request.

## Project structure

- `src/` — pricing, cart, and inventory modules
- `tests/` — pytest unit tests
- `scripts/`, `ml/`, `infra/`, `ansible/` — folders reserved for later lab activities
- `.github/workflows/ci.yml` — automated CI workflow

## Run locally

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

The Lab 2 exercise includes an intentionally failing test commit to demonstrate how GitHub Actions reports a CI failure, followed by a corrective commit.

## Assignment 4.2 — Smart Build-Cache Invalidation

Implementation notes and verified cache hit/miss results: [docs/Smart_Build_Cache_Invalidation.md](docs/Smart_Build_Cache_Invalidation.md).
