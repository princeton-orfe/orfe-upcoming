SHELL := /bin/bash

# Default output file
OUTPUT ?= events.json
SCHEMA := schema/events.schema.json

.PHONY: help install gen gen-enriched gen-raw gen-enriched-raw validate validate-enriched example-gen example-validate example-validate-enriched example-validate-raw example-validate-enriched-raw

help:
	@echo "Targets:"
	@echo "  install                  - pip install -r requirements.txt"
	@echo "  gen                      - generate $(OUTPUT) from $$ICS_URL"
	@echo "  gen-enriched             - generate with --enrich-titles (includes fallback)"
	@echo "  gen-raw                  - generate with --enrich-raw-details"
	@echo "  gen-enriched-raw         - generate with both title and raw details enrichment"
	@echo "  validate                 - validate $(OUTPUT) against $(SCHEMA)"
	@echo "  validate-enriched        - gen-enriched then validate"
	@echo "  example-gen              - generate /tmp/events.json from examples/sample_input.example.ics"
	@echo "  example-validate         - validate /tmp/events.json"
	@echo "  example-validate-raw     - example-gen with raw details then validate"
	@echo "  example-validate-enriched-raw - example-gen with titles+raw details then validate"

install:
	pip install -r requirements.txt

# Generate from ICS_URL into $(OUTPUT)
gen:
	@if [ -z "$$ICS_URL" ]; then echo "ICS_URL is not set" >&2; exit 1; fi
	python -m src.main --ics-url "$$ICS_URL" --output "$(OUTPUT)"

# Generate enriched (subtitle scraping + fallback) from ICS_URL into $(OUTPUT)
gen-enriched:
	@if [ -z "$$ICS_URL" ]; then echo "ICS_URL is not set" >&2; exit 1; fi
	python -m src.main --ics-url "$$ICS_URL" --output "$(OUTPUT)" --enrich-titles

gen-raw:
	@if [ -z "$$ICS_URL" ]; then echo "ICS_URL is not set" >&2; exit 1; fi
	python -m src.main --ics-url "$$ICS_URL" --output "$(OUTPUT)" --enrich-raw-details

gen-enriched-raw:
	@if [ -z "$$ICS_URL" ]; then echo "ICS_URL is not set" >&2; exit 1; fi
	python -m src.main --ics-url "$$ICS_URL" --output "$(OUTPUT)" --enrich-titles --enrich-raw-details

validate:
	python tools/validate_json.py --schema "$(SCHEMA)" --data "$(OUTPUT)"

validate-enriched: gen-enriched validate

example-gen:
	python -m src.main --ics-url "$(PWD)/examples/sample_input.example.ics" --output /tmp/events.json

example-validate:
	python tools/validate_json.py --schema "$(SCHEMA)" --data /tmp/events.json

example-validate-enriched:
	python -m src.main --ics-url "$(PWD)/examples/sample_input.example.ics" --output /tmp/events.json --enrich-titles
	python tools/validate_json.py --schema "$(SCHEMA)" --data /tmp/events.json

example-validate-raw:
	python -m src.main --ics-url "$(PWD)/examples/sample_input.example.ics" --output /tmp/events.json --enrich-raw-details
	python tools/validate_json.py --schema "$(SCHEMA)" --data /tmp/events.json

example-validate-enriched-raw:
	python -m src.main --ics-url "$(PWD)/examples/sample_input.example.ics" --output /tmp/events.json --enrich-titles --enrich-raw-details
	python tools/validate_json.py --schema "$(SCHEMA)" --data /tmp/events.json
