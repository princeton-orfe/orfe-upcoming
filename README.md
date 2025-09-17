# ORFE Upcoming

Automated pipeline that fetches a department ICS feed, applies a configurable transformation, and publishes a stable JSON file as a GitHub Release asset ( `releases/latest/download/events.json` ). Scheduled + manual CI. Includes change detection, failure tracking, configurable field mapping, and examples for regression testing.

## Current Features
* Hourly + manual workflow (cron + `workflow_dispatch`).
* Fetches ICS from repository variable `ICS_URL`.
* SHA256 change detection of raw ICS body, skips run if unchanged.
* Transformation layer (`src/transform.py`) for:
	- Field mapping (UID -> guid, DTSTART/DTEND -> startTime/endTime, URL -> urlRef, CATEGORIES -> series, SUMMARY -> speaker, DESCRIPTION -> content)
	- Category joining (order-insensitive comparisons in tests)
	- Speaker / description escaping (commas or semicolons)
	- Newline representation modes: `space`, `literal_r`, `newline`
	- Timezone normalization (default `America/New_York`)
	- Location heuristic splitting: `"DETAIL - NAME"` → `{"name": name, "detail": detail}` (with relaxed test tolerance for reversed cases)
	- Static placeholders (`title`, `cancelled`, `bannerImage`, `itemType` - hardcoded)
* Failure streak persistence (`.ci/failure-streak`) with automatic issue creation after 3 consecutive failures.
* Release asset publishing (always overwrites a single `events.json` under the `latest` release tag) ensuring a stable URL:  
	`https://github.com/<owner>/<repo>/releases/latest/download/events.json`
* Local iteration flags in `src.main` for testing:
	- `--config` (JSON config file for transform overrides)
	- `--print-only` (stdout instead of writing file)
	- `--limit N` (truncate output list for quick inspection)
	- `--ics-url` (override env / repo variable when iterating locally)
* Real-world examples under `examples/` with a tolerant regression test.
* Unit tests: fetch, transform logic, sample round‑trip, config behaviors.
* Title enrichment (optional) scraping each event detail page's `<div class="event-subtitle">` into `title` when enabled.
* Content enrichment (scaffolding) to populate `content` from the event page body (disabled by default; ICS DESCRIPTION remains the fallback unless you enable it).
* Overwrite mode (env `ENRICH_OVERWRITE=1`) to replace existing titles instead of only filling empty ones.
* Enrichment debug logging via `ENRICH_DEBUG=1` showing fetch/skip/overwrite decisions.
* Title fallback (when enrichment is enabled): after scraping, any event with a missing/blank/"TBD" title will be filled from its `speaker` field so no event is left without a meaningful title (if a speaker exists).

## Example Workflow (End-to-End)

1. Set a repository variable `ICS_URL` (Settings → Variables → New variable) pointing to the upstream `.ics` feed.
2. (Optional) Adjust transform behavior with an optional `transform_config.json` (copy from `transform_config.example.json` and tweak).
3. Trigger the workflow manually (Actions → "ICS to JSON" → Run) or wait for the hourly cron.
4. If the ICS content changed (hash differs), the workflow:
	 - Installs deps & runs tests
	 - Generates `events.json`
	 - Publishes / updates the `latest` release and uploads `events.json` (non-zipped)
	 - Resets failure streak
5. If unchanged, it exits early after a lightweight hash step.
6. On failure, it increments the failure streak and after 3 consecutive failures opens (or updates) a tracking issue.
7. Clients consume the JSON at the stable release asset URL.

### Consuming the JSON
Example (JavaScript):
```js
fetch('https://github.com/princeton-orfe/orfe-upcoming/releases/latest/download/events.json')
	.then(r => r.json())
	.then(events => console.log(events));
```

### Local Generation / Iteration
```bash
python -m src.main --ics-url "https://orfe.princeton.edu/feeds/events/upcoming.ics" \
	--print-only --limit 3
```

With a config file:
```bash
python -m src.main --ics-url "$ICS_URL" --config transform_config.json --print-only
```

Write to disk:
```bash
python -m src.main --ics-url "$ICS_URL" --output events.json
```

Enrich titles (fill blanks only):
```bash
ENRICH_TITLES=1 python -m src.main --ics-url "$ICS_URL" --limit 2 --print-only
```

Force overwrite existing titles:
```bash
ENRICH_TITLES=1 ENRICH_OVERWRITE=1 python -m src.main --ics-url "$ICS_URL" --limit 2 --print-only
```

Verbose enrichment debugging:
```bash
ENRICH_TITLES=1 ENRICH_DEBUG=1 python -m src.main --ics-url "$ICS_URL" --limit 1 --print-only
```

Enrich content (disabled by default):
```bash
# fill only when content is empty
ENRICH_CONTENT=1 python -m src.main --ics-url "$ICS_URL" --limit 2 --print-only

# force overwrite existing content
ENRICH_CONTENT=1 ENRICH_CONTENT_OVERWRITE=1 python -m src.main --ics-url "$ICS_URL" --limit 2 --print-only
```

Content format options:
```bash
# Default is plain text with paragraph breaks
ENRICH_CONTENT=1 ENRICH_CONTENT_FORMAT=text python -m src.main --ics-url "$ICS_URL" --limit 1 --print-only

# Emit Markdown (requires optional dependency: markdownify)
pip install markdownify
ENRICH_CONTENT=1 ENRICH_CONTENT_FORMAT=markdown python -m src.main --ics-url "$ICS_URL" --limit 1 --print-only

# Emit sanitized inner HTML fragment
ENRICH_CONTENT=1 ENRICH_CONTENT_FORMAT=html python -m src.main --ics-url "$ICS_URL" --limit 1 --print-only
```

Extraction details:
- The scraper prioritizes a container like `<div class="events-detail-main">` (or `event-details-main`) that includes a header with class `.details` and then grabs the following content block (e.g., `.tex2jax_process` / `.field__item`).
- If that structure isn't found, it falls back to common containers like `.event-description`, `.event-body`, `.field--name-body`, `#content-body`, or `<article>`.
- Scripts and styles are removed. For text/markdown modes, whitespace is normalized, preserving paragraph breaks.

### Title Fallback Details

When `ENRICH_TITLES` (or `--enrich-titles`) is enabled, the pipeline first tries to scrape
each event detail page for a subtitle and store it in `title`. After scraping, a
post-processing step ensures there are no blank titles left:

- Titles that are empty/whitespace or equal to "TBD" (case-insensitive) are considered missing.
- Missing titles are filled from the event's `speaker` field if it exists.
- This fallback does not overwrite meaningful non-empty titles unless you explicitly pass `--enrich-overwrite` or set `ENRICH_OVERWRITE=1` (which affects scraping, not the fallback default).

This guarantees that, when enrichment is turned on, events won’t be published with blank or "TBD" titles if a speaker is available.

### Local Files and file:// URLs

The CLI supports fetching from:

- http(s) URLs
- `file://` URLs
- bare local paths (absolute or relative)

Example:

```bash
python -m src.main --ics-url "$PWD/examples/sample_input.example.ics" --print-only
```

### Examples
Folder: `examples/`
* `sample_input.example.ics` – curated real-world slice of the feed.
* `sample_output.expected.json` – expected core subset for regression.

Test `test_example_files_roundtrip` verifies that every GUID listed in the expected file appears in generated output and that invariant fields match (allowing:
* Additional events (produced superset)
* Category order differences (compared as a set)
* Location name/detail heuristic swaps

To update expected output after intentional transform changes:
```bash
python -m src.main --ics-url file://$PWD/examples/sample_input.example.ics --print-only \
	> /tmp/new.json
# Manually edit /tmp/new.json keeping only desired representative subset, then:
mv /tmp/new.json examples/sample_output.expected.json
pytest tests/test_transform.py::test_example_files_roundtrip -q
```

### Regenerating From Example Quickly (Helper One-Liner)
```bash
python - <<'PY'
from pathlib import Path; from ics import Calendar; from src.transform import transform_calendar, TransformConfig
ics = Path('examples/sample_input.example.ics').read_text()
data = transform_calendar(Calendar(ics), TransformConfig(represent_newlines_as='literal_r'))
import json; print(json.dumps(data, indent=2))
PY
```

You can then curate / reduce that JSON before committing to keep the fixture concise.

### Local generation
```bash
python -m src.main --ics-url "https://example.com/calendar.ics" --repo-variable sample --output events.json
```
Then inspect the file:
```bash
cat events.json | head
```

## Possible Next Enhancements
* Additional enrichment (images, room normalization, speaker bio extraction).
* Additional text normalization (HTML entities, Unicode punctuation mapping).
* Config-driven inclusion/exclusion filters (e.g., series allowlist).
* Expose transform settings via env variables for GitHub UI override.
* Structured logging & metrics (e.g., event count trend, skip reason) printed in CI.

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
 - Title enrichment (skip vs fill) and overwrite behavior (`test_enrich_titles`, `test_enrich_overwrite`).

## Data Manipulation Stub
`manipulate_data(calendar, variable)` remains a hook for future bespoke filtering / enrichment beyond the generic transform.

Iterate locally with `--print-only` before committing.

## Configuration reference (env vars and inputs)

These environment variables and workflow inputs control behavior at runtime.

### Core runtime

| Name | Scope | Type | Default | Purpose |
|------|-------|------|---------|---------|
| `ICS_URL` | CLI/CI | string | — | Upstream ICS feed URL. Supports http(s), `file://`, or local paths. |
| `OUTPUT_FILE` | CLI/CI | string | `events.json` | Output JSON filename. |
| `REPO_VARIABLE` | CLI/CI | string | `default` | Arbitrary variable passed to `manipulate_data` (currently unused). |

### Enrichment and fallback

| Name | Scope | Type | Default | Purpose |
|------|-------|------|---------|---------|
| `ENRICH_TITLES` | CLI/CI | bool | `false` (manual CLI), `true` (scheduled CI, manual workflow default) | Enable subtitle scraping to populate `title` from each event detail page. |
| `ENRICH_OVERWRITE` | CLI/CI | bool | `false` | When enriching, overwrite non-empty `title` values instead of only filling blanks. |
| `ENRICH_DEBUG` | CLI/CI | bool | `false` | Verbose enrichment logging (fetch/skip/overwrite decisions). |
| `FALLBACK_PREPEND_TEXT` | CLI/CI | string | — | Prefix template for titles filled from `speaker`. Supports `{series}` placeholder; missing keys render empty and whitespace is collapsed. Max length: 128 chars. Example: `A {series} Talk by` → `A Optimization Seminar Talk by Alice`. |
| `BOT_BYPASS_HEADER_VALUE` | CLI/CI | string | `1` | Value sent as `x-wdsoit-bot-bypass` header during enrichment requests. |
| `ENRICH_CONTENT` | CLI/CI | bool | `false` | Enable content scraping from the event page into `content` (fallback stays as ICS `DESCRIPTION` if not overwritten). |
| `ENRICH_CONTENT_OVERWRITE` | CLI/CI | bool | `false` | Overwrite non-empty `content` when enriching. |
| `ENRICH_CONTENT_FORMAT` | CLI/CI | enum | `text` | Output format for scraped content: `text` (plain), `markdown` (requires `markdownify`), or `html` (inner fragment). |

Boolean envs accept: `1,true,yes,on` (case-insensitive) for true.

### Transform parameters

| Name | Scope | Type | Default | Purpose |
|------|-------|------|---------|---------|
| `TARGET_TZ` | CLI/CI | string | `America/New_York` | Target timezone for datetime normalization. |

You can also provide a JSON config file via `--config` (copy from `transform_config.example.json`) to override mappings, placeholders, masks, etc.

### GitHub Actions inputs (manual/scheduled)

| Name | Workflow | Type | Default | Purpose |
|------|----------|------|---------|---------|
| `force` | `ICS to JSON` | input | `false` | Force regeneration even if ICS content hash is unchanged. |
| `enrich_titles` | `ICS to JSON`, `ICS Manual Test` | input | `true` | Toggle enrichment on manual runs (scheduled runs always enrich). |

CLI flags mirror the envs: `--enrich-titles`, `--enrich-overwrite`, `--enrich-content`, and `--enrich-content-overwrite`.

