from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import MentorCFOException, mentor_exception_handler
from app.core.config import settings

app = FastAPI(
    title="CFO Mentor API",
    description="Governança cognitiva decisória para CFOs — Mentor C-Level",
    version="2.0.0",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(MentorCFOException, mentor_exception_handler)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "mentor-cfo", "version": "2.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Mentor C-Level CFO API", "docs": "/docs"}
