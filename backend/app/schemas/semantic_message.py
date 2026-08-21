from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class Position(BaseModel):
    latitude : float
    longitude : float

class SemanticMessage(BaseModel):
    vehicle_id : str
    event_type : Literal["hazard", "obstacle", "traffic", "emergency", "normal"]
    object_type : str
    confidence : float = Field(ge=0.0, le=1.0)
    risk_level : Literal["LOW","MEDIUM","HIGH","CRITICAL"]
    position : Position
    description : str
    recommendation : str
    timestamp : datetime