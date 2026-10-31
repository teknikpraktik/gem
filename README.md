# GEM / REGIONAL_SEK

A rules-based signal monitor for Swedish investors. **It does not trade and gives no investment advice.**

| Part | Path | Runs on |
|---|---|---|
| Research engine (backtests, data catalogue, reproducibility, reports) | `research/` | GitHub Actions (`.github/workflows/gem-phase2-research.yml`) |
| NAV publication observer (observation only) | `research/src/gem/navobserver.py` | GitHub Actions (`.github/workflows/nav-observer.yml`, results on branch `ci/nav-observer`) |
| PWA + live API + monthly signal job | `web/` | Vercel |

Research results: `research/reports/phase2_report.md`, `research/reports/phase2b_live_report.md`.
Web app and deployment: [`web/README.md`](web/README.md).
