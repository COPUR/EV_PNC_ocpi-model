#!/usr/bin/env python3
"""Extract OCPI class, enum and OpenEnum tables from the OCPI AsciiDoc spec into JSON Schema.

The spec (https://github.com/COPUR/ocpi, a mirror of ocpi/ocpi) is the source; the output
`schema/ocpi.schema.json` is generated and not edited by hand. Hand-written parts of the
model (events, extensions) live in their own files and reference these definitions.

    python3 tools/ocpi_to_schema.py --spec ../ocpi            # rewrite schema/ocpi.schema.json
    python3 tools/ocpi_to_schema.py --spec ../ocpi --check    # fail if the file would change

Only the modules listed in ROOTS are exported, plus every definition they reference.

Licence note: the OCPI text is CC BY-ND 4.0 (EVRoaming Foundation). This tool therefore
copies structure only (names, types, lengths, cardinalities, enum values), never the
descriptions, notes or examples. Each definition points to its spec file instead.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "tools" / "ocpi-spec-pin.json"
OUT = ROOT / "schema" / "ocpi.schema.json"

MODULE_FILES = [
    "types",
    "credentials",
    "mod_locations",
    "mod_tariffs",
    "mod_tokens",
    "mod_sessions",
    "mod_cdrs",
    "mod_commands",
    "mod_charging_profiles",  # referenced from Sessions and Commands
]
# Top-level objects the platform exchanges; everything they reference is exported too.
ROOTS = [
    "Credentials",
    "Location",
    "EVSE",
    "Connector",
    "Tariff",
    "Token",
    "AuthorizationInfo",
    "Session",
    "ChargingPreferences",
    "CDR",
    "CancelReservation",
    "CommandResponse",
    "CommandResult",
    "ReserveNow",
    "StartSession",
    "StopSession",
    "UnlockConnector",
]

HEADING = re.compile(
    r"^(?P<eq>={3,6}) (?P<raw>.+?)\s*$",
    re.M,
)
KIND = re.compile(r"^_?(?P<name>[A-Za-z ]+?)_?\s+_?(?P<kind>Object|object|class|enum|OpenEnum)_?$")
XREF = re.compile(r"<<[^,>]*,([^>]*)>>")
CELL_SPLIT = re.compile(r"(?<!\\)\|")

SCALARS = {
    "string": {"type": "string"},
    "int": {"type": "integer"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
}
CISTRING_PATTERN = r"^[\x20-\x7e]*$"
STRING_PATTERN = r"^[^\x00-\x1f\x7f]*$"  # printable UTF-8, no control characters
DATETIME_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$"


def clean(text: str) -> str:
    text = XREF.sub(r"\1", text)
    text = re.sub(r"\[\[[^\]]*\]\]\s*", "", text)
    text = text.replace(" +\n", " ").replace("+\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def cells(table: str) -> list[str]:
    parts = CELL_SPLIT.split(table)
    return [p.strip() for p in parts[1:]]


def first_table(body: str) -> tuple[str, int] | None:
    """First table in a section: its text and its column count (from the [cols=...] line)."""
    m = re.search(r'^(?:\[cols="([^"]*)"[^\]]*\]\s*\n)?\|===\s*\n(.*?)^\|===', body, re.M | re.S)
    if not m:
        return None
    cols = m[1].count(",") + 1 if m[1] else 0
    return m[2], cols


def parse_modules(spec: Path) -> dict[str, dict]:
    defs: dict[str, dict] = {}
    for module in MODULE_FILES:
        text = (spec / f"{module}.asciidoc").read_text()
        heads = list(HEADING.finditer(text))
        for i, h in enumerate(heads):
            k = KIND.match(h["raw"])
            if not k:
                continue
            name = k["name"].replace(" ", "")
            body = text[h.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            found = first_table(body)
            if found is None:
                continue
            table, ncols = found
            kind = k["kind"].lower()
            cs = cells(table)
            if kind in ("object", "class"):
                if cs[:2] != ["Property", "Type"]:
                    continue
                if ncols != 4:
                    sys.exit(f"{module}: {name}: expected 4 columns, found {ncols}")
                rows = [cs[j : j + 4] for j in range(4, len(cs), 4)]
                if any(len(r) != 4 for r in rows):
                    sys.exit(f"{module}: {name}: table is not 4 columns wide")
                defs[name] = {"kind": "class", "module": module, "rows": rows, "doc": body}
            else:
                if cs[0] != "Value":
                    continue
                width = ncols or 2
                if len(cs) % width:
                    sys.exit(f"{module}: {name}: {len(cs)} cells do not fill {width} columns")
                rows = [cs[j : j + width] for j in range(width, len(cs), width)]
                defs[name] = {"kind": kind, "module": module, "rows": rows, "doc": body}
    return defs


def type_schema(cell: str, known: set[str]) -> tuple[dict, str | None]:
    """Return (schema fragment, referenced definition name or None)."""
    text = XREF.sub(r"\1", cell).strip()
    m = re.match(r"^([A-Za-z0-9_]+)\s*(?:[(\[](\d+)[)\]]?)?$", text)
    if not m:
        sys.exit(f"cannot parse type cell {cell!r}")
    base, length = m[1], int(m[2]) if m[2] else None
    if base.lower() in SCALARS:
        base = base.lower()
    if base == "CiString":
        s = {"type": "string", "pattern": CISTRING_PATTERN, "x-ocpi-case-insensitive": True}
        if length:
            s["maxLength"] = length
        return s, None
    if base == "string":
        s = {"type": "string", "pattern": STRING_PATTERN}
        if length:
            s["maxLength"] = length
        return s, None
    if base in SCALARS:
        return dict(SCALARS[base]), None
    if base == "DateTime":
        return {"type": "string", "pattern": DATETIME_PATTERN, "x-ocpi-type": "DateTime"}, None
    if base == "URL":
        return {"type": "string", "maxLength": 255, "format": "uri"}, None
    if base in known:
        return {"$ref": f"#/$defs/{base}"}, base
    sys.exit(f"unknown type {base!r} in cell {cell!r}")


def build_class(name: str, d: dict, known: set[str]) -> tuple[dict, set[str]]:
    props, required, refs = {}, [], set()
    for prop, typ, card, desc in d["rows"]:
        prop = re.sub(r"\[\[[^\]]*\]\]\s*", "", prop).strip()
        card = card.strip()
        if card not in {"1", "?", "*", "+"}:
            sys.exit(f"{name}.{prop}: unexpected cardinality {card!r}")
        frag, ref = type_schema(typ, known)
        if ref:
            refs.add(ref)
        if card in ("*", "+"):
            frag = {"type": "array", "items": frag, **({"minItems": 1} if card == "+" else {})}
        props[prop] = frag
        if card in ("1", "+"):
            required.append(prop)
    schema = {"title": name, "type": "object"}
    schema["properties"] = props
    if required:
        schema["required"] = required
    schema["x-ocpi-spec"] = f"{d['module']}.asciidoc"
    return schema, refs


def build_enum(name: str, d: dict) -> dict:
    values = [re.sub(r"\s+", "", clean(r[0])).strip("`") for r in d["rows"]]
    if d["kind"] == "openenum":
        s = {"title": name, "type": "string", "x-ocpi-open-enum": True, "examples": values}
    else:
        s = {"title": name, "type": "string", "enum": values}
    s["x-ocpi-spec"] = f"{d['module']}.asciidoc"
    return s


# Fields with no canonical home (ADR-0001), for example OICP signed metering details, live under
# `extensions.<namespace>` on these objects. See Extensions below.
EXTENSION_SLOTS = ("CDR", "Session", "Token")
EXTENSIONS = {
    "title": "Extensions",
    "type": "object",
    "description": "Vendor or hub specific data with no canonical field, keyed by a lower-case namespace such as oicp or gireve. Producers add, consumers ignore namespaces they do not know. Anything used by two services moves into the model by ADR.",
    "propertyNames": {"pattern": "^[a-z][a-z0-9_]{1,31}$"},
    "additionalProperties": {"type": "object"},
    "x-ocpi-spec": "none (EV_PNC extension)",
}


def generate(spec: Path, pin: dict) -> dict:
    parsed = parse_modules(spec)
    known = set(parsed)
    out: dict[str, dict] = {}
    todo = list(ROOTS)
    for r in ROOTS:
        if r not in parsed:
            sys.exit(f"root definition {r} not found in the spec")
    while todo:
        name = todo.pop()
        if name in out:
            continue
        d = parsed[name]
        if d["kind"] == "class":
            schema, refs = build_class(name, d, known)
        else:
            schema, refs = build_enum(name, d), set()
        out[name] = schema
        todo.extend(r for r in refs if r not in out)
    for slot in EXTENSION_SLOTS:
        out[slot]["properties"]["extensions"] = {"$ref": "#/$defs/Extensions"}
    out["Extensions"] = EXTENSIONS
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/COPUR/EV_PNC_ocpi-model/schema/ocpi.schema.json",
        "title": "OCPI 2.3.0 canonical model (generated)",
        "description": "Structure extracted from the OCPI 2.3.0 spec (CC BY-ND 4.0, EVRoaming Foundation) by tools/ocpi_to_schema.py; no spec text is copied. Do not edit.",
        "x-ocpi-source": pin,
        "$defs": {k: out[k] for k in sorted(out)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, required=True, help="checkout of the OCPI spec at the pinned commit")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pin = json.loads(PIN_FILE.read_text())
    text = json.dumps(generate(args.spec, pin), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print(f"{OUT.relative_to(ROOT)} differs from a fresh build; run tools/ocpi_to_schema.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
