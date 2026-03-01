from pydantic import BaseModel
from typing import List

class AttendanceSummaryItem(BaseModel):
    subject: str
    total_classes: int
    attended: int
    percentage: float

class StudentDashboardResponse(BaseModel):
    subjects: List[AttendanceSummaryItem]
    overall_percentage: float