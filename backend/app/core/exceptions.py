from fastapi import Request
from fastapi.responses import JSONResponse


class MentorCFOException(Exception):
    def __init__(self, error: str, message: str, status_code: int = 400):
        self.error = error
        self.message = message
        self.status_code = status_code


class CaseNotFoundError(MentorCFOException):
    def __init__(self):
        super().__init__("CASE_NOT_FOUND", "Nenhum caso encontrado com o ID informado", 404)


class InvalidStateTransitionError(MentorCFOException):
    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            "INVALID_STATE_TRANSITION",
            f"Transição inválida: {from_state} → {to_state}",
            409,
        )


class InsufficientAssumptionsError(MentorCFOException):
    def __init__(self, count: int):
        super().__init__(
            "INSUFFICIENT_ASSUMPTIONS",
            f"São necessárias no mínimo 3 premissas financeiras. Fornecidas: {count}",
            400,
        )


class InsufficientRisksError(MentorCFOException):
    def __init__(self, count: int):
        super().__init__(
            "INSUFFICIENT_RISKS",
            f"São necessários no mínimo 3 riscos financeiros. Fornecidos: {count}",
            400,
        )


class UnauthorizedError(MentorCFOException):
    def __init__(self):
        super().__init__("UNAUTHORIZED", "Token JWT inválido ou expirado", 401)


async def mentor_exception_handler(request: Request, exc: MentorCFOException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )
