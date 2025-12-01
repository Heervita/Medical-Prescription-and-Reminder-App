from pydantic import BaseModel
from typing import List

class MedicineCreate(BaseModel):
    prescription_id: str
    name: str
    dosage: str
    frequency: int
    times: List[str]  # ["08:00", "14:00"]
    start_date: str
    end_date: str
