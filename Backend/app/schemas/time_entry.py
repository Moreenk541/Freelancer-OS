
"""
Time entry schemas.
 
Two usage patterns:
 
  1. Live timer
       POST /time/start  → TimeEntryStart  (start_time, task_id)
       PUT  /time/stop/{id} → TimeEntryStop (end_time)
       Service computes duration = end_time - start_time in seconds.
 
  2. Manual entry
       POST /time/manual → TimeEntryManual (start_time + end_time together)
       Service validates end > start and computes duration immediately.
 
TimeEntryOut  — response for both patterns
TimeEntryUpdate — edit description or correct timestamps after the fact
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, model_validator

class TimeEntryStart(BaseModel):
    task_id: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = Field(None, max_length=5000)

class TimeEntryStop(BaseModel):
    end_time: datetime = Field(default_factory=datetime.utcnow)


class TimeEntryManual(BaseModel):
    task_id:     int
    start_time:  datetime
    end_time:    datetime
    description: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "TimeEntryManual":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class TimeEntryUpdate(BaseModel):
    """
    PATCH /time/{id} — correct a logged entry.
    If both start and end are updated, duration is recomputed in the service.
    """
    start_time:  Optional[datetime] = None
    end_time:    Optional[datetime] = None
    description: Optional[str]      = Field(None, max_length=1000)
 
 
class TimeEntryOut(BaseModel):
    """
    Time entry response.
 
    duration        — raw seconds (null if timer is still running)
    duration_hours  — decimal hours, computed property on the ORM model
    end_time=null   — means the timer is currently running
    """
    id:             int
    task_id:        int
    freelancer_id:  int
    start_time:     datetime
    end_time:       Optional[datetime] = None
    duration:       Optional[float]    = None
    duration_hours: float              = 0.0
    description:    Optional[str]      = None
    created_at:     datetime
 
    model_config = {"from_attributes": True}
 
    

