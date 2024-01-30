from uuid import UUID

from pydantic import BaseModel, Field


class Rating(BaseModel):
    film_id: UUID = Field()
    rating: float = Field(max=10, min=0)


class Review(BaseModel):
    film_id: UUID = Field()
    review_text: str = Field(max_length=5000)
