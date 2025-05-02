from pydantic import BaseModel
from datetime import datetime

class ScheduleQuoteDto(BaseModel):
    """DTO for scheduling a quote."""
    name: str
    gmail: str
    date: datetime