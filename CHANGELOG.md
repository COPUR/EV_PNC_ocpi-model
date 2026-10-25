# Changelog

Versioning is semver. Adding a definition, an optional field or an event is a minor version. Removing or retyping anything, or making an optional field required, is a major version with a migration note. Changes need an ADR in EV_PNC_docs.

## 0.1.0 (unreleased)

First cut, card M-01.

- `schema/ocpi.schema.json`: Credentials, Locations (Location, EVSE, Connector, Parking), Tariffs, Tokens, Sessions, CDRs and Commands, extracted from the OCPI 2.3.0 spec at the commit in `tools/ocpi-spec-pin.json`. Structure only, no spec text (CC BY-ND 4.0).
- `Extensions` slot (`extensions.<namespace>`) on CDR, Session and Token for fields with no canonical home.
- `schema/events.schema.json`: TokenAuthorizeRequested, TokenAuthorizeDecided, SessionStarted, SessionUpdated, SessionEnded, CdrReceived, GrantChanged.
- Generated pydantic v2 models (`generated/python`) and kotlinx.serialization types (`generated/kotlin`), both tested against the same fixtures and the spec's own examples.
- Not yet: Go and Swift types, the error model, ID and time-zone conventions, Hub Client Info and Payments modules.
