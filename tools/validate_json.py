#!/usr/bin/env python3
"""Validate produced events JSON against the repo schema.

Usage:
  python tools/validate_json.py --schema schema/events.schema.json --data events.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError


def _format_error(err: ValidationError) -> str:
    loc = "$" + "".join(f"[{repr(p)}]" if isinstance(p, int) else f".{p}" for p in err.path)
    schema_loc = "/".join(str(p) for p in err.schema_path)
    msg = err.message
    return f"path={loc} schema={schema_loc} error={msg}"


def validate(schema_path: Path, data_path: Path) -> int:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    data = json.loads(data_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(f"Validation failed for {data_path} against {schema_path}:")
        for e in errors[:50]:  # cap output
            print(" -", _format_error(e))
        if len(errors) > 50:
            print(f" ... and {len(errors) - 50} more errors")
        return 1
    print(f"Validation passed: {data_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate events JSON against schema")
    p.add_argument("--schema", required=True, help="Path to JSON Schema file")
    p.add_argument("--data", required=True, help="Path to events JSON file")
    ns = p.parse_args(argv)
    return validate(Path(ns.schema), Path(ns.data))


if __name__ == "__main__":
    sys.exit(main())
