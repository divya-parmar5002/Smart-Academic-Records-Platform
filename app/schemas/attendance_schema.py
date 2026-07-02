from pydantic import BaseModel
from typing import List

class AttendanceItem(BaseModel):
    student_id: int
    status: str  # present / absent


class MarkAttendanceRequest(BaseModel):
    session_id: int
    attendance: List[AttendanceItem]

class AssignSubjectRequest(BaseModel):
    subject_id: int
    teacher_id: int
    year: int
    semester: int
    section: str