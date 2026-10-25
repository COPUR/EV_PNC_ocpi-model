#!/usr/bin/env bash
# Generate pydantic v2 models from schema/*.json into generated/python/ev_pnc_ocpi_model.
# Usage: tools/gen_python.sh [--check]
set -euo pipefail
cd "$(dirname "$0")/.."
PKG=generated/python/ev_pnc_ocpi_model
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
uvx --quiet --from "datamodel-code-generator==0.86.0" datamodel-codegen \
  --input schema --input-file-type jsonschema \
  --output-model-type pydantic_v2.BaseModel \
  --use-annotated --disable-timestamp --target-python-version 3.11 \
  --formatters ruff-format \
  --output "$TMP/pkg"
# stable, descriptive module names
rm -rf "$TMP/pkg/.ruff_cache"
mv "$TMP/pkg/ocpi_schema.py" "$TMP/pkg/ocpi.py"
mv "$TMP/pkg/events_schema.py" "$TMP/pkg/events.py"
rm -f "$TMP/pkg/__init__.py"
sed -i 's/from \. import ocpi_schema/from . import ocpi/; s/ocpi_schema\./ocpi./g' "$TMP/pkg/events.py"
cat > "$TMP/pkg/__init__.py" <<'PY'
"""Generated pydantic models for the EV_PNC canonical model. See schema/ at the repo root."""

from typing import Annotated

from pydantic import Field, TypeAdapter

from . import events, ocpi

DomainEvent = Annotated[
    events.TokenAuthorizeRequested
    | events.TokenAuthorizeDecided
    | events.SessionStarted
    | events.SessionUpdated
    | events.SessionEnded
    | events.CdrReceived
    | events.GrantChanged,
    Field(discriminator="event_type"),
]
_event_adapter: TypeAdapter[DomainEvent] = TypeAdapter(DomainEvent)


def parse_event(data: object) -> DomainEvent:
    """Validate a decoded JSON event and return the typed model chosen by `event_type`."""
    return _event_adapter.validate_python(data)


__all__ = ["DomainEvent", "events", "ocpi", "parse_event"]
PY
if [[ "${1:-}" == "--check" ]]; then
  diff -r "$TMP/pkg" "$PKG" -x __pycache__ -x py.typed >/dev/null || { echo "$PKG is out of date; run tools/gen_python.sh" >&2; exit 1; }
else
  mkdir -p "$PKG"
  find "$PKG" -maxdepth 1 -name '*.py' -delete
  cp "$TMP"/pkg/*.py "$PKG"/
  touch "$PKG/py.typed"
  echo "wrote $PKG"
fi
