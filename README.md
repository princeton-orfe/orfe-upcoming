# ORFE Upcoming

Automated pipeline that fetches a department ICS feed, applies configurable transformation, and publishes a stable JSON file as a GitHub Release asset.

## Features

* Hourly + manual workflow (cron + `workflow_dispatch`)
* ICS fetching with SHA256 change detection
* Configurable field mapping and transformation
* Title enrichment from event pages
* Content enrichment (optional)
* Raw details extraction (optional)
* Failure streak tracking with issue creation
* JSON schema validation
* Unit tests and regression testing

## Usage

### Consuming JSON

```js
fetch('https://github.com/princeton-orfe/orfe-upcoming/releases/latest/download/events.json')
	.then(r => r.json())
	.then(events => console.log(events));
```

### Release Assets

**Production** (`latest`): `https://github.com/princeton-orfe/orfe-upcoming/releases/latest/download/events.json`
- Triggers: Scheduled (hourly), manual, pushes to `main`
- Purpose: Stable production feed

**Development** (`dev`): `https://github.com/princeton-orfe/orfe-upcoming/releases/dev/download/events.json`
- Triggers: Pushes to `dev-asset`
- Purpose: Testing environment

### Local Development

Generate JSON locally:
```bash
python -m src.main --ics-url "https://example.com/calendar.ics" --output events.json
```

With enrichment:
```bash
ENRICH_TITLES=1 python -m src.main --ics-url "$ICS_URL" --limit 2 --print-only
```

Validate output:
```bash
python tools/validate_json.py --schema schema/events.schema.json --data events.json
```

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ICS_URL` | string | — | Upstream ICS feed URL |
| `OUTPUT_FILE` | string | `events.json` | Output filename |
| `REPO_VARIABLE` | string | `default` | Variable for `manipulate_data` |
| `TARGET_TZ` | string | `America/New_York` | Target timezone |
| `ENRICH_TITLES` | bool | `false` | Enable title scraping |
| `ENRICH_OVERWRITE` | bool | `false` | Overwrite existing titles |
| `ENRICH_DEBUG` | bool | `false` | Verbose enrichment logging |
| `FALLBACK_PREPEND_TEXT` | string | — | Prefix for speaker fallback titles |
| `ENRICH_CONTENT` | bool | `false` | Enable content scraping |
| `ENRICH_CONTENT_OVERWRITE` | bool | `false` | Overwrite existing content |
| `ENRICH_CONTENT_FORMAT` | enum | `text` | Content format: `text`, `markdown`, `html` |
| `ENRICH_RAW_DETAILS` | bool | `false` | Enable raw HTML extraction |
| `ENRICH_RAW_DETAILS_OVERWRITE` | bool | `false` | Overwrite existing raw details |
| `ENRICH_RAW_EXTRACTS` | bool | `true` | Enable abstract/bio extraction |
| `ENRICH_RAW_EXTRACTS_OVERWRITE` | bool | `false` | Overwrite existing extracts |
| `BOT_BYPASS_HEADER_VALUE` | string | `1` | Bot bypass header value |

### CLI Flags

| Flag | Description |
|------|-------------|
| `--ics-url URL` | Override ICS URL |
| `--output FILE` | Output filename |
| `--config FILE` | JSON config file |
| `--print-only` | Print to stdout |
| `--limit N` | Limit events |
| `--enrich-titles` | Enable title enrichment |
| `--enrich-overwrite` | Overwrite existing titles |
| `--enrich-content` | Enable content enrichment |
| `--enrich-content-overwrite` | Overwrite existing content |
| `--enrich-raw-details` | Enable raw details extraction |
| `--enrich-raw-details-overwrite` | Overwrite existing raw details |
| `--enrich-raw-extracts` | Enable abstract/bio extraction |

### GitHub Actions

| Input | Workflow | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `force` | ICS to JSON | boolean | `false` | Force regeneration |
| `enrich_titles` | ICS to JSON | boolean | `true` | Enable title enrichment |

## Schema

Output is a JSON array of event objects validated against `schema/events.schema.json` (Draft-07).

**Required fields:**
- `guid`: Unique ID from ICS UID
- `startTime`/`endTime`: Formatted as `YYYY-MM-DDTHH:mm:ss`
- `urlRef`: Event page URL
- `location`: Object with `name`, `id`, `detail`
- `title`, `cancelled`, `bannerImage`, `itemType`: Strings

**Optional fields:**
- `series`: Comma-joined categories
- `speaker`: Event speaker/title
- `content`: Description text
- `rawEventDetails`: Inner HTML fragment
- `rawExtractAbstract`/`rawExtractBio`: Extracted content

## Development

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

### Testing

Tests cover:
- ICS retrieval and transformation
- Title, content, and raw details enrichment
- JSON schema validation
- Regression testing with examples

### Examples

Folder: `examples/`
- `sample_input.example.ics`: Curated ICS slice
- `sample_output.expected.json`: Expected JSON subset

Update examples after changes:
```bash
python -m src.main --ics-url file://$PWD/examples/sample_input.example.ics --print-only > /tmp/new.json
# Edit /tmp/new.json to keep representative subset
mv /tmp/new.json examples/sample_output.expected.json
pytest tests/test_transform.py::test_example_files_roundtrip -q
```

### Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for enriched local validation and CI details.

### Future Enhancements

* Additional enrichment (images, speaker bios)
* Text normalization (HTML entities, Unicode)
* Config-driven filters (series allowlists)
* Structured logging and metrics

