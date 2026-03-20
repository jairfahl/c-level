from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.exceptions import MentorCFOException, mentor_exception_handler
from app.core.config import settings
from app.api.routers import cases_router, state_machine_router, audit_router, heuristics_router, admin_router, auth_router, knowledge_base_router

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    return JSONResponse(
        status_code=400,
        content={
            "error": "VALIDATION_ERROR",
            "message": first_error.get("msg", "Validation error"),
            "details": jsonable_encoder(errors),
        },
    )


app.include_router(auth_router, prefix="/v1")
app.include_router(cases_router, prefix="/v1")
app.include_router(state_machine_router, prefix="/v1")
app.include_router(audit_router, prefix="/v1")
app.include_router(heuristics_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(knowledge_base_router, prefix="/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "mentor-cfo", "version": "2.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Mentor C-Level CFO API", "docs": "/docs"}
