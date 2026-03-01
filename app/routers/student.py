from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import (
    User,
    Student,
    Subject,
    Teacher,
    AttendanceSession,
    Attendance
)
from app.core.dependencies import require_role
from app.schemas.response_schema import (
    StudentDashboardResponse,
    AttendanceSummaryItem
)

router = APIRouter(prefix="/student", tags=["Student"])


# =====================================
# 📊 Student Attendance Dashboard
# =====================================
@router.get("/attendance-summary", response_model=StudentDashboardResponse)
def attendance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student"))
):

    # 1️⃣ Get Student Profile
    profile = db.query(Student).filter(
        Student.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found"
        )

    # 2️⃣ Get Subjects Assigned To Student Section
    subjects = db.query(Subject).join(Teacher).filter(
        Teacher.section_id == profile.section_id,
        Subject.department_id == profile.department_id,
        Subject.year_id == profile.year_id,
        Teacher.is_active == True
    ).distinct().all()

    if not subjects:
        raise HTTPException(
            status_code=404,
            detail="No subjects found for this student"
        )

    response = []
    total_all = 0
    present_all = 0

    # 3️⃣ Loop Through Subjects
    for subject in subjects:

        # Only ACTIVE sessions
        total_classes = db.query(func.count(AttendanceSession.id)).filter(
            AttendanceSession.subject_id == subject.id,
            AttendanceSession.section_id == profile.section_id,
            AttendanceSession.is_active == True
        ).scalar()

        # Count Present Attendance
        attended = db.query(func.count(Attendance.id)).join(SessionModel).filter(
            Attendance.student_id == current_user.id,
            AttendanceSession.subject_id == subject.id,
            AttendanceSession.section_id == profile.section_id,
            Attendance.status == "present",
            AttendanceSession.is_active == True
        ).scalar()

        total_classes = total_classes or 0
        attended = attended or 0

        percentage = (
            (attended / total_classes) * 100
            if total_classes > 0 else 0
        )

        total_all += total_classes
        present_all += attended

        response.append(
            AttendanceSummaryItem(
                subject=subject.subject_name,
                total_classes=total_classes,
                attended=attended,
                percentage=round(percentage, 2)
            )
        )

    # 4️⃣ Overall Percentage
    overall_percentage = (
        (present_all / total_all) * 100
        if total_all > 0 else 0
    )

    return StudentDashboardResponse(
        subjects=response,
        overall_percentage=round(overall_percentage, 2)
    )