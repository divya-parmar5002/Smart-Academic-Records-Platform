from pydantic import BaseModel
from typing import List

class AttendanceItem(BaseModel):
    student_id: int
    status: str  # present / absent


class MarkAttendanceRequest(BaseModel):
    session_id: int
    attendance: List[AttendanceItem]