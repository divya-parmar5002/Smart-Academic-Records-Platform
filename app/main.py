from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth
from app.routers import attendance
from app.routers import admin
from app.routers import teacher
from app.routers import student

from app.core.redis import test_redis_connection

app = FastAPI(
    title="Smart Attendance System API",
    description="Backend API for managing authentication and attendance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Smart Attendance System API Running 🚀"}

@app.on_event("startup")
async def startup_event():
    test_redis_connection()