from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import User, Subject, SubjectAssignment,AttendanceSession, Student, Attendance
from app.core.dependencies import require_role
from app.schemas.attendance_schema import MarkAttendanceRequest

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# ==============================
# 1️⃣ Get Assigned Subjects
# ==============================
@router.get("/subjects")
def get_assigned_subjects(
    department_id: int,
    year_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    subjects = db.query(Subject).join(SubjectAssignment).filter(
        SubjectAssignment.teacher_id == current_user.id,
        SubjectAssignment.section_id == section_id,
        Subject.department_id == department_id,
        Subject.year_id == year_id
    ).all()

    if not subjects:
        raise HTTPException(status_code=404, detail="No subjects assigned")

    return subjects


# ==============================
# 2️⃣ Get Students List
# ==============================
@router.get("/students")
def get_students(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    students = db.query(Student).filter(
        Student.section_id == section_id
    ).all()

    if not students:
        raise HTTPException(status_code=404, detail="No students found")

    return students


# ==============================
# 3️⃣ Create Session
# ==============================
@router.post("/create-session")
def create_session(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    # 🔒 Validate subject assignment
    assignment = db.query(SubjectAssignment).filter(
        SubjectAssignment.teacher_id == current_user.id,
        SubjectAssignment.subject_id == subject_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=403, detail="Subject not assigned to you")

    new_session = SubjectAssignment(
        subject_id=subject_id,
        teacher_id=current_user.id,
        session_date=datetime.utcnow().date(),
        start_time=datetime.utcnow(),
        is_active=True
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "message": "Session created successfully",
        "session_id": new_session.id
    }


# ==============================
# 4️⃣ Mark Attendance (Bulk)
# ==============================
@router.post("/mark-attendance")
def mark_attendance(
    data: MarkAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == data.session_id,
        AttendanceSession.teacher_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session already closed")

    for item in data.attendance:

        # 🔒 Duplicate Protection
        existing = db.query(Attendance).filter(
            Attendance.session_id == data.session_id,
            Attendance.student_id == item.student_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Attendance already marked for student {item.student_id}"
            )

        record = Attendance(
            session_id=data.session_id,
            student_id=item.student_id,
            status=item.status,
            marked_at=datetime.utcnow()
        )
        db.add(record)

    session.is_active = False
    session.end_time = datetime.utcnow()

    db.commit()

    return {"message": "Attendance saved successfully"}


# ==============================
# 5️⃣ Edit Attendance
# ==============================
@router.put("/edit-attendance")
def edit_attendance(
    session_id: int,
    student_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    attendance = db.query(Attendance).filter(
        Attendance.session_id == session_id,
        Attendance.student_id == student_id
    ).first()

    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    attendance.status = status
    db.commit()

    return {"message": "Attendance updated successfully"}


# ==============================
# 6️⃣ Teacher History
# ==============================
@router.get("/history")
def teacher_history(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("teacher"))
):

    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.subject_id == subject_id,
        AttendanceSession.teacher_id == current_user.id
    ).all()

    if not sessions:
        raise HTTPException(status_code=404, detail="No sessions found")

    result = []

    for s in sessions:
        total = db.query(Attendance).filter(
            Attendance.session_id == s.id
        ).count()

        present = db.query(Attendance).filter(
            Attendance.session_id == s.id,
            Attendance.status == "present"
        ).count()

        result.append({
            "date": s.session_date,
            "total_students": total,
            "present": present,
            "absent": total - present
        })

    return result