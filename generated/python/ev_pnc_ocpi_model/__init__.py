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
