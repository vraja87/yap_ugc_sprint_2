from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ViewMessage(BaseModel):
    film_id: UUID = Field(default_factory=uuid4)
    value: str


class EventMessage(ViewMessage):
    event_type: int
