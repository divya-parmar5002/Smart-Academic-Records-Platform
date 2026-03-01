from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import engine
from app.db import models
from app.routers import auth
from app.routers import attendence
from app.routers import admin

# Create database tables (if they don't exist)
models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Smart Attendance System API",
    description="Backend API for managing authentication and attendance",
    version="1.0.0"
)


# CORS (Important if frontend is separate like Next.js / React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(auth.router)
app.include_router(attendence.router, prefix="/attendance", tags=["Attendance"])


@app.get("/", tags=["Root"])
def root():
    return {"message": "Smart Attendance System API Running 🚀"}


#Register Routers
from app.routers import teacher, student

app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(admin.router)