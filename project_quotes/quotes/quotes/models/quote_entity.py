from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional
#from bson import ObjectId
from datetime import datetime

class ScheduleEntityType(Enum):
    """Enum for schedule entity types."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DONE = "done" 

class QuoteEntity(BaseModel):
    """Base class for schedule entities."""
    id: int = Field(default =None) #, alias="_id")
    name: str
    gmail: str
    date: datetime
    type: ScheduleEntityType = ScheduleEntityType.ACTIVE

    # model_config = ConfigDict(
    #     arbitrary_types_allowed=True,
    #     json_encoders={ObjectId: str},
    # )