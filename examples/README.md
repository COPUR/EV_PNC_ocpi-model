# Examples

Hand-written fixtures with fictional identifiers (`TR` / `ZZZ` is a placeholder party, not the platform's provider ID, which is still to be obtained under card TR-03).

- `events/` one file per canonical event; the file name is the kebab-case event name.
- `ocpi/` OCPI objects, including a CDR that carries an `extensions.oicp` slot.

The OCPI spec's own examples are not copied here (CC BY-ND 4.0). The conformance tests read them from a checkout of the spec at the pinned commit when `OCPI_SPEC_DIR` is set; CI does that.
