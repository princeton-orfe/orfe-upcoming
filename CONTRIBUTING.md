# Contributing

Thanks for your interest in contributing! This project transforms an ICS feed into a validated JSON feed and publishes it as a release asset. Below are quick guidelines to get you productive fast.

## Dev setup

- Python 3.11+
- Create/activate a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run tests

```bash
pytest -q
```

All tests should pass locally before you open a PR.

## Generate and validate JSON (enriched flow)

The CI enforces schema validation after generating the JSON. To reproduce the full pipeline locally—including subtitle enrichment and post-processing fallback—use the provided Make targets:

- Install deps (once):
  ```bash
  make install
  ```
- Enrich and validate from your ICS URL:
  ```bash
  ICS_URL="https://example.com/calendar.ics" make gen-enriched validate
  ```
- Validate a previously generated file:
  ```bash
  make validate
  ```
- Use the example ICS (with enrichment + fallback) and validate:
  ```bash
  make example-validate-enriched
  ```

Under the hood, enrichment writes `title` from the event page subtitle when available; any remaining blank/TBD titles are filled from the `speaker` field (fallback). Validation is performed against `schema/events.schema.json` using `tools/validate_json.py`.

## Schema

- The schema for the output is in `schema/events.schema.json` (JSON Schema draft-07).
- If you change the output structure, update the schema to match and ensure validation passes:
  ```bash
  python tools/validate_json.py --schema schema/events.schema.json --data events.json
  ```
- Keep the README “Schema” section accurate when adjusting fields.

## CI

- Pull requests run unit tests and, on generation jobs, validate the produced JSON against the schema.
- The scheduled/push workflows also perform validation before publishing release assets.

## Style

- Prefer small, focused PRs.
- Include/adjust tests when changing behavior.
- Avoid breaking the output contract unless coordinated; if necessary, document the change in the README and bump consumers accordingly.

## Questions

Open an issue if something’s unclear or you need guidance. We appreciate improvements to docs and examples as well!