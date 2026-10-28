# EV_PNC_ocpi-model

Canonical OCPI 2.3.0-shaped model, domain events and error model shared by all EV_PNC_ services. Schema first; generated Java, Python, Go and TypeScript types. Seeded from COPUR/ocpi.

Part of the **EV_PNC** platform: a neutral eMSP integration layer for Turkey-first, Europe-ready Plug&Charge, navigation and payments. The platform is neither a CPO nor a payment institution.

> Plug in, charging starts, payment completes in the background.

## Scope

- Locations, Tariffs, Tokens, Sessions, CDRs, Commands, Credentials as JSON Schema / OpenAPI
- Canonical events: token-authorize requested/decided, session started/updated/ended, CDR received, grant changed
- Extension slots for fields with no canonical home (ADR-0001), e.g. OICP signed metering
- Error model and ID conventions (TR provider ID, Europe/Istanbul, +03:00)
- Changes only by ADR and semver; breaking change means a major version and a migration note

## Tech stack

JSON Schema, OpenAPI, code generation (Java, Python, Go, TypeScript)

## Packaging

- Published components: ocpi-model
- Depends on: nothing outside this repo
- Depended on by: EV_PNC_hub-gateway, EV_PNC_ocpi-emsp, EV_PNC_payments, EV_PNC_pilot-analytics, EV_PNC_planner, EV_PNC_plugcharge, EV_PNC_policy-engine, EV_PNC_pricing, EV_PNC_simulator, EV_PNC_telemetry
- Dependency rules: no cycles (ADP); depend towards more stable components (SDP); published `*-api` components hold abstractions, deployables hold concrete code (SAP). CI runs `tools/packaging_check.py --strict` from `EV_PNC_docs`.
- Owner: Architect agent · Wave 1 (now, before the 2026-12-07 gate) · Visibility: public

## Proposed layout

```
schema/
generated/{java,python,go,typescript}/
CHANGELOG.md
```

## Related

- Plan: `repo-plan/v2/README.md` (project files); consent repos: `EV_PnC_Consent_*` (`repo-plan/consent/README.md`)
- Docs: [EV_PNC_docs](https://github.com/COPUR/EV_PNC_docs)

## Status

Scaffold only. Not production ready.

## License

Apache-2.0 (proposed)
