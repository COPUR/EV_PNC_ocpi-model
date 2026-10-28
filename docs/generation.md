# How the model is built

```
OCPI spec (COPUR/ocpi @ pinned commit)
   └─ tools/ocpi_to_schema.py ──▶ schema/ocpi.schema.json   (generated)
schema/events.schema.json                                    (hand-written, references the above)
   ├─ tools/gen_python.sh ──▶ generated/python/ev_pnc_ocpi_model/   (pydantic v2)
   └─ tools/gen_kotlin.py ──▶ generated/kotlin/.../ocpimodel/       (kotlinx.serialization)
```

`make generate` rebuilds everything, `make check` fails if a generated file is stale, `make test` runs both language test suites. CI runs all three against a checkout of the pinned spec commit.

## Rules

- Never hand-edit `schema/ocpi.schema.json` or anything under `generated/*/src` or `ev_pnc_ocpi_model/`. Change the tool, the pin or `events.schema.json`.
- **Licence.** The OCPI text is CC BY-ND 4.0. The extractor copies names, types, lengths, cardinalities and enum values, not descriptions, notes or examples, and each definition carries `x-ocpi-spec` pointing to the spec file. The spec's example files are read from the pinned checkout at test time, not copied. Counsel should confirm this reading (card P0-04).
- **Cardinality.** `1` and `+` are required, `?` and `*` optional. Optional fields may be absent; an explicit `null` is accepted by the generated types but not by the schema.
- **Open enums** (connector type, token type, and so on) are plain strings. Known values are listed under `examples` in the schema.
- **Dates** stay strings matching the OCPI pattern (a trailing `Z` is optional in OCPI). Events always carry `Z`.
- **Extensions.** Hub-specific data without a canonical field goes under `extensions.<namespace>` on CDR, Session or Token. When two services need the same extension field it moves into the model by ADR.
- **Spec examples that disagree with the spec's own tables** are listed with reasons in `generated/python/tests/test_conformance.py` (`SPEC_KNOWN_BAD`); the test fails when one of them starts to conform, so the list cannot go stale.

## Adding an event

1. Add the definition to `schema/events.schema.json` as `allOf: [EventEnvelope, {...}]` with an `event_type` const equal to its name.
2. Add it to the `DomainEvent` union in `tools/gen_python.sh`.
3. Add `examples/events/<kebab-name>.json` and the matching line in `ConformanceTest.kt`.
4. `make generate && make check && make test`, then an ADR and a CHANGELOG line.
