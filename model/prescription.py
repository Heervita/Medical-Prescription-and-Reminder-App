from pydantic import BaseModel
from typing import Optional, List

class PrescriptionCreate(BaseModel):
    title: str
    doctor_name: Optional[str] = None
    date: str  # YYYY-MM-DD
