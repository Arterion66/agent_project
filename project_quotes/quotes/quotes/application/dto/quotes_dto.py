from pydantic import BaseModel, Field
from datetime import datetime

class QuoteDTO(BaseModel):
    """
    Data Transfer Object for Quote.
    """
    name: str = Field(..., description="Name of the person who scheduled the quote")
    gmail: str = Field(..., description="Email of the person who scheduled the quote")
    date: datetime = Field(..., description="Date and time of the quote in ISO format")