# Repository Guidelines

## Project Structure & Module Organization
- Root Python scripts: step-wise pipeline named with numeric prefixes (e.g., `1_fetching_news.py` → `4_news_summary_pdf.py`, `5_podcast_summary.py`, `6_sellside_highlights.py`, `7_generate_email.py`, `10_two_week_summary.py`).
- PDFs are produced in step 4 (`4_news_summary_pdf.py`); no separate `pdfreport/` module in this repo.
- `prompt/`: LLM prompt assets.  `data/` and `output/`: inputs and generated artifacts (git-ignored).
- `parameters.py` and `apikey.py`: runtime configuration and API keys (keep local; do not commit secrets).

## Build, Test, and Development Commands
- Create env and install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -U pip && pip install -r requirements.txt`
- Run core ingestion/summarization locally (typical flow):
  - `python 1_fetching_news.py && python 2_md_to_article_summary.py && python 3_article_to_overall_summary.py && python 4_news_summary_pdf.py`
- Generate PDFs / weekly deliverables:
  - PDFs: `python 4_news_summary_pdf.py`
  - Two-week summary: `python 10_two_week_summary.py`
- Automation helpers (adjust paths in scripts first):
  - `bash script/get_urls_to_md.sh` and `bash script/md_to_summary.sh`

## Coding Style & Naming Conventions
- Python, PEP 8, 4-space indentation; prefer type hints and module-level docstrings.
- Filenames and functions: `snake_case`; constants: `UPPER_SNAKE_CASE`.
- New pipeline steps: keep numeric prefix + short action, e.g., `8_generate_images.py`.
- Optional formatters: `black` and `isort` (run locally if installed).

## Testing Guidelines
- Framework: `pytest` (add to `requirements.txt` if contributing tests).
- Location: `tests/`; files as `test_*.py`; mirror module paths where possible.
- Run: `pytest -q` (aim for fast, deterministic tests; avoid network where possible).

## Commit & Pull Request Guidelines
- Commit messages: imperative mood; concise summary line. Prefer Conventional Commits where practical (`feat:`, `fix:`, `refactor:`). Example: `fix(email): correct double colon in headers`.
- PRs: brief description of intent, “how to test” steps, linked issues, and sample output paths (e.g., `output/…`). Include screenshots for visual changes.

## Security & Configuration Tips
- Never commit API keys or personal data. Keep secrets in `apikey.py` or a local `.env`; `.gitignore` already excludes common artifacts.
- Review `parameters.py` date logic and any absolute paths in `script/` before running in a new environment.
