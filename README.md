# ORFE Upcoming

Automated pipeline that fetches a department ICS feed, applies configurable transformation, and publishes a stable JSON file as a GitHub Release asset.

## Features

* Hourly + manual workflow (cron + `workflow_dispatch` + [orfe-upcoming-dispatcher](https://github.com/organizations/princeton-orfe/settings/apps/orfe-upcoming-dispatcher))
* ICS fetching with SHA256 change detection
* Configurable field mapping and transformation
* Title enrichment from event pages
* Content enrichment (optional)
* Raw details extraction (optional)
* Failure streak tracking with issue creation
* JSON schema validation
* Unit tests and regression testing

## Usage

### Release Assets

**Production** (`latest`): `https://github.com/princeton-orfe/orfe-upcoming/releases/latest/download/events.json`
- Triggers: Scheduled (hourly via cron + [orfe-upcoming-dispatcher](https://github.com/organizations/princeton-orfe/settings/apps/orfe-upcoming-dispatcher)), manual
- Purpose: Stable production feed

**Development** (`dev`): `https://github.com/princeton-orfe/orfe-upcoming/releases/dev/download/events.json`
- Triggers: Manual (workflow_dispatch on dev-asset branch)
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
Update examples after changes:
```bash
python -m src.main --ics-url file://$PWD/examples/sample_input.example.ics --print-only > /tmp/new.json
# Edit /tmp/new.json to keep representative subset
mv /tmp/new.json examples/sample_output.expected.json
pytest tests/test_transform.py::test_example_files_roundtrip -q
```

One-liners:
- Generate and validate from your ICS_URL
	```bash
	make install
	ICS_URL="https://example.com/calendar.ics" make gen-enriched validate
	```
- Validate a previously generated file
	```bash
	make validate
	```
- Use the example ICS and validate (with enrichment and fallback applied)
	```bash
	make example-validate-enriched
	```

Alternatively invoke the validator directly:
```bash
python tools/validate_json.py --schema schema/events.schema.json --data events.json
```

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
| `ENRICH_RAW_DETAILS` | CLI/CI | bool | `false` | Enable raw HTML scraping from the event page into `rawEventDetails` (inner HTML of `.events-detail-main` container). |
| `ENRICH_RAW_DETAILS_OVERWRITE` | CLI/CI | bool | `false` | Overwrite non-empty `rawEventDetails` when enriching. |
| `ENRICH_RAW_EXTRACTS` | CLI/CI | bool | `true` | Enable automatic extraction of `rawExtractAbstract` and `rawExtractBio` from `rawEventDetails` (requires raw details enrichment). |
| `ENRICH_RAW_EXTRACTS_OVERWRITE` | CLI/CI | bool | `false` | Overwrite existing `rawExtractAbstract`/`rawExtractBio` values when extracting. |

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
| `enrich_titles` | `ICS to JSON` | input | `true` | Toggle enrichment on manual runs (scheduled runs always enrich). |
| `enrich_raw_details` | `ICS to JSON` | input | `true` | Capture raw event details HTML on manual runs. |
| `replace_latest` | `ICS to JSON` | input | `false` | Replace the Latest Events release instead of creating a separate manual release. |

CLI flags mirror the envs: `--enrich-titles`, `--enrich-overwrite`, `--enrich-content`, `--enrich-content-overwrite`, `--enrich-raw-details`, `--enrich-raw-details-overwrite`, `--enrich-raw-extracts`.
>>>>>>> origin/main

