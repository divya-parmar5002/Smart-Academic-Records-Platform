from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User, UserRoleEnum, SubjectAssignment
from app.schemas.user_schema import LoginRequest, CreateUserRequest, AssignSubjectRequest
from app.core.security import get_password_hash, verify_password
from app.schemas.user_schema import LoginRequest, CreateUserRequest, AssignSubjectRequest
from app.schemas.attendance_schema import MarkAttendanceRequest
from app.dependencies.auth_dependency import admin_required

router = APIRouter(prefix="/admin", tags=["Admin"],dependencies=[Depends(admin_required)])


# 🔐 Admin Login
@router.post("/login")
def admin_login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid email")

    if user.role != UserRoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not an admin")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Wrong password")

    return {"message": "Admin login successful"}


# 👨‍🏫 Create Teacher
@router.post("/create-teacher")
def create_teacher(data: CreateUserRequest, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_teacher = User(
        email=data.email,
        password=hash_password(data.password),
        role=UserRoleEnum.teacher
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    return {"message": "Teacher created successfully"}


# 📚 Assign Subject
@router.post("/assign-subject")
def assign_subject(data: AssignSubjectRequest, db: Session = Depends(get_db)):

    teacher = db.query(User).filter(
        User.user_id == data.teacher_id,
        User.role == UserRoleEnum.teacher
    ).first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    assignment = SubjectAssignment(
        subject_id=data.subject_id,
        teacher_id=data.teacher_id,
        year=data.year,
        semester=data.semester,
        section=data.section
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {"message": "Subject assigned successfully"}


# 📊 View All Assignments
@router.get("/assignments")
def get_all_assignments(db: Session = Depends(get_db)):
    return db.query(SubjectAssignment).all()