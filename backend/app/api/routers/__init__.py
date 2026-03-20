"""API routers — exported for registration in main.py."""
from app.api.routers.financial_decision_cases import router as cases_router
from app.api.routers.state_machine import router as state_machine_router
from app.api.routers.audit import router as audit_router
from app.api.routers.heuristics import router as heuristics_router
from app.api.routers.admin import router as admin_router
from app.api.routers.auth import router as auth_router
from app.api.routers.knowledge_base import router as knowledge_base_router

__all__ = [
    "cases_router",
    "state_machine_router",
    "audit_router",
    "heuristics_router",
    "admin_router",
    "auth_router",
    "knowledge_base_router",
]
