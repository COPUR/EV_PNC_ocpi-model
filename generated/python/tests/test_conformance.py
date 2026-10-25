"""The schema, the generated pydantic models and the fixtures must agree.

Spec examples (CC BY-ND, not copied into this repo) are read from OCPI_SPEC_DIR, a checkout of
COPUR/ocpi at the commit in tools/ocpi-spec-pin.json. Without it only the local fixtures run.
"""

import json
import os
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from ev_pnc_ocpi_model import events, ocpi, parse_event

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "schema"
EXAMPLES = REPO / "examples"
SPEC = os.environ.get("OCPI_SPEC_DIR")

ocpi_schema = json.loads((SCHEMA / "ocpi.schema.json").read_text())
events_schema = json.loads((SCHEMA / "events.schema.json").read_text())
registry = Registry().with_resources(
    [
        ("ocpi.schema.json", Resource.from_contents(ocpi_schema)),
        (ocpi_schema["$id"], Resource.from_contents(ocpi_schema)),
        ("events.schema.json", Resource.from_contents(events_schema)),
        (events_schema["$id"], Resource.from_contents(events_schema)),
    ]
)


def validator(file: str, name: str) -> Draft202012Validator:
    doc = ocpi_schema if file == "ocpi" else events_schema
    return Draft202012Validator({"$ref": f"#/$defs/{name}", "$defs": doc["$defs"]}, registry=registry)


def camel(kebab: str) -> str:
    return "".join(p.capitalize() for p in kebab.split("-"))


EVENT_FIXTURES = sorted((EXAMPLES / "events").glob("*.json"))
OCPI_FIXTURES = {"session.json": "Session", "cdr-with-extension.json": "CDR"}

# Spec examples (mapping: file prefix -> definition) and the ones that disagree with the spec's own tables.
SPEC_PREFIXES = [
    ("cdr_example", "CDR"),
    ("session_example", "Session"),
    ("tariff_", "Tariff"),
    ("token_example", "Token"),
    ("token_put", "Token"),
    ("location_example", "Location"),
    ("credentials_example", "Credentials"),
]
SPEC_KNOWN_BAD = {
    "cdr_example.json": "tariffs[0] has no tax_included, which Tariff requires",
    "tariff_put_example.json": "no last_updated, which Tariff requires",
    "location_example.json": "EVSE.parking holds plain ids, but EVSEParking is an object",
    "location_example_parking_garage_opening_hours.json": "EVSE.parking holds plain ids, but EVSEParking is an object",
}


def spec_examples():
    if not SPEC:
        return []
    out = []
    for prefix, name in SPEC_PREFIXES:
        for f in sorted((Path(SPEC) / "examples").glob(f"{prefix}*.json")):
            out.append(pytest.param(f, name, id=f.name))
    return out


@pytest.mark.parametrize("path", EVENT_FIXTURES, ids=lambda p: p.stem)
def test_event_fixture_validates_and_round_trips(path):
    data = json.loads(path.read_text())
    name = camel(path.stem)
    assert not list(validator("events", name).iter_errors(data))
    model = parse_event(data)
    assert type(model).__name__ == name
    assert model.model_dump(mode="json", exclude_none=True) == data


@pytest.mark.parametrize("fixture,name", OCPI_FIXTURES.items())
def test_ocpi_fixture_validates_and_round_trips(fixture, name):
    data = json.loads((EXAMPLES / "ocpi" / fixture).read_text())
    assert not list(validator("ocpi", name).iter_errors(data))
    model = getattr(ocpi, name).model_validate(data)
    assert model.model_dump(mode="json", exclude_none=True) == data


def test_event_type_must_match_the_model():
    data = json.loads((EXAMPLES / "events" / "session-started.json").read_text())
    data["event_type"] = "SessionEnded"
    # discriminator picks SessionEnded, whose body is the same shape: it must not be mistaken for SessionStarted
    assert isinstance(parse_event(data), events.SessionEnded)
    data["event_type"] = "Nope"
    with pytest.raises(Exception):
        parse_event(data)


def test_unknown_extension_namespace_is_kept_and_bad_one_rejected():
    data = json.loads((EXAMPLES / "ocpi" / "session.json").read_text())
    data["extensions"] = {"Bad-Name": {}}
    assert list(validator("ocpi", "Session").iter_errors(data))
    data["extensions"] = {"gireve": {"anything": 1}}
    assert not list(validator("ocpi", "Session").iter_errors(data))


@pytest.mark.skipif(not SPEC, reason="OCPI_SPEC_DIR not set")
@pytest.mark.parametrize("path,name", spec_examples())
def test_spec_example(path, name):
    data = json.loads(path.read_text())
    errors = list(validator("ocpi", name).iter_errors(data))
    if path.name in SPEC_KNOWN_BAD:
        assert errors, f"{path.name} now conforms; remove it from SPEC_KNOWN_BAD ({SPEC_KNOWN_BAD[path.name]})"
        return
    assert not errors, errors[0].message
    getattr(ocpi, name).model_validate(data)
