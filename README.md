# ORFE Upcoming

This project fetches an ICS (calendar) file, manipulates the event data according to repository variables, and writes a reformatted `events.json` artifact. The GitHub Action (manual trigger for now) generates and uploads the JSON so it can be consumed by clients (e.g. GitHub Pages, another site build, or direct artifact download). No web server is required.

## Features
- Fetches ICS calendar data from a configurable URL
- Manipulates and reformats event data (customizable)
- Outputs a static `events.json` file (no runtime server required)
- Includes unit tests for ICS retrieval, data manipulation, and JSON accessibility
- Github Action workflow for automation

## Usage
1. Add repository (or org) secrets `ICS_URL` and `REPO_VARIABLE` (optional) in GitHub.
2. Manually trigger the workflow: Actions > "ICS to JSON" > Run workflow.
3. After it completes, download the `events-json` artifact; it contains `events.json`.
4. (Optional) Commit `events.json` to a `gh-pages` branch or serve via another pipeline.

### Local generation
```bash
python -m src.main --ics-url "https://example.com/calendar.ics" --repo-variable sample --output events.json
```
Then inspect the file:
```bash
cat events.json | head
```

## Future Improvements
- Add `schedule:` trigger (e.g. cron: '0 * * * *')
- Implement custom data manipulation logic inside `manipulate_data()`
- Publish to GitHub Pages automatically

## Getting Started (Local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m src.main --ics-url "https://example.com/calendar.ics"
```

## Tests
Tests cover:
- ICS retrieval (mocked HTTP)
- Placeholder manipulation pass-through
- JSON generation to a file

## Data Manipulation Stub
The function `manipulate_data(calendar, variable)` is intentionally unimplemented so custom filtering / augmentation logic can be added later.
