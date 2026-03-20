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
    def __init__(self, from_state: str = "", to_state: str = "", *, message: str = ""):
        msg = message or f"Transição inválida: {from_state} → {to_state}"
        super().__init__(
            "INVALID_STATE_TRANSITION",
            msg,
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


class HeuristicNotFoundError(MentorCFOException):
    def __init__(self):
        super().__init__("HEURISTIC_NOT_FOUND", "Nenhuma heurística encontrada com o ID informado", 404)


class DocumentNotFoundError(MentorCFOException):
    def __init__(self):
        super().__init__("DOCUMENT_NOT_FOUND", "Nenhum documento encontrado com o ID informado", 404)


class DocumentExtractionError(MentorCFOException):
    def __init__(self, detail: str = ""):
        msg = "Falha ao extrair texto do documento"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__("DOCUMENT_EXTRACTION_ERROR", msg, 422)


class DocumentTooLargeError(MentorCFOException):
    def __init__(self, size_bytes: int):
        super().__init__(
            "DOCUMENT_TOO_LARGE",
            f"Arquivo excede o limite de 10 MB. Tamanho: {size_bytes / (1024 * 1024):.1f} MB",
            413,
        )


class UnsupportedFileTypeError(MentorCFOException):
    def __init__(self, file_type: str):
        super().__init__(
            "UNSUPPORTED_FILE_TYPE",
            f"Tipo de arquivo não suportado: {file_type}. Tipos aceitos: pdf, docx, txt, xlsx, xls, pptx, csv, md",
            415,
        )


class DocumentIrrelevantError(MentorCFOException):
    def __init__(self, reason: str):
        super().__init__(
            "DOCUMENT_IRRELEVANT",
            f"Documento não é relevante para o domínio financeiro selecionado: {reason}",
            422,
        )


class DocumentRelevanceBorderlineError(MentorCFOException):
    def __init__(self, reason: str):
        super().__init__(
            "DOCUMENT_RELEVANCE_BORDERLINE",
            f"Relevância do documento é incerta: {reason}",
            409,
        )


async def mentor_exception_handler(request: Request, exc: MentorCFOException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )
