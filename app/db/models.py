from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    Enum,
    Time,
    DateTime,
    Boolean,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


# =========================
# USERS TABLE
# =========================

class UserRoleEnum(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String,
        nullable=True
    )

    role = Column(
        Enum(UserRoleEnum, name="user_role_enum"),
        nullable=False
    )

    email_verified = Column(
        Boolean,
        nullable=False,
        default=False
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    last_login = Column(
        DateTime(timezone=True),
        nullable=True
    )

    student = relationship(
        "Student",
        back_populates="user",
        uselist=False
    )

    teacher = relationship(
        "Teacher",
        back_populates="user",
        uselist=False
    )

# =========================
# DEPARTMENTS TABLE
# =========================

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String, unique=True, nullable=False)

    students = relationship("Student", back_populates="department")
    teachers = relationship("Teacher", back_populates="department")
    subjects = relationship("Subject", back_populates="department")


# =========================
# STUDENTS TABLE
# =========================

class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    enrollment_no = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="student")
    department = relationship("Department", back_populates="students")

    attendances = relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan"
    )


# =========================
# TEACHERS TABLE
# =========================

class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="teacher")
    department = relationship("Department", back_populates="teachers")

    subject_assignments = relationship(
        "SubjectAssignment",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )


# =========================
# SUBJECTS TABLE
# =========================

class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, index=True)
    subject_code = Column(String, unique=True, nullable=False)
    subject_name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"))

    department = relationship("Department", back_populates="subjects")

    subject_assignments = relationship(
        "SubjectAssignment",
        back_populates="subject",
        cascade="all, delete-orphan"
    )


# =========================
# SUBJECT ASSIGNMENTS TABLE
# =========================

class SubjectAssignment(Base):
    __tablename__ = "subject_assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)

    subject_id = Column(
        Integer,
        ForeignKey("subjects.subject_id", ondelete="CASCADE")
    )

    teacher_id = Column(
        Integer,
        ForeignKey("teachers.teacher_id", ondelete="CASCADE")
    )

    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String, nullable=False)

    subject = relationship("Subject", back_populates="subject_assignments")
    teacher = relationship("Teacher", back_populates="subject_assignments")

    attendance_sessions = relationship(
        "AttendanceSession",
        back_populates="subject_assignment",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            'subject_id',
            'teacher_id',
            'year',
            'semester',
            'section',
            name='unique_subject_assignment'
        ),
    )


# =========================
# ATTENDANCE SESSIONS TABLE
# =========================

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    session_id = Column(Integer, primary_key=True, index=True)

    assignment_id = Column(
        Integer,
        ForeignKey("subject_assignments.assignment_id", ondelete="CASCADE"),
        nullable=False
    )

    session_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subject_assignment = relationship(
        "SubjectAssignment",
        back_populates="attendance_sessions"
    )

    attendances = relationship(
        "Attendance",
        back_populates="attendance_session",
        cascade="all, delete-orphan"
    )


# =========================
# ATTENDANCE TABLE
# =========================

class AttendanceStatusEnum(str, enum.Enum):
    present = "present"
    absent = "absent"


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        Integer,
        ForeignKey("attendance_sessions.session_id", ondelete="CASCADE"),
        nullable=False
    )

    student_id = Column(
        Integer,
        ForeignKey("students.student_id", ondelete="CASCADE"),
        nullable=False
    )

    status = Column(
        Enum(AttendanceStatusEnum, name="attendance_status_enum"),
        nullable=False
    )

    marked_at = Column(DateTime(timezone=True), server_default=func.now())

    attendance_session = relationship(
        "AttendanceSession",
        back_populates="attendances"
    )

    student = relationship(
        "Student",
        back_populates="attendances"
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="unique_attendance_per_session"
        ),
    )