from fastapi import HTTPException, status

class PlatformException(Exception):
    """Base exception for the Sales Intelligence Platform"""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class DatabaseError(PlatformException):
    """Raised when a database operation fails"""
    pass

class MilvusError(PlatformException):
    """Raised when a Milvus database operation fails"""
    pass

class LLMTimeoutError(PlatformException):
    """Raised when an LLM API request times out"""
    pass

class ValidationError(PlatformException):
    """Raised when data validation fails"""
    pass

# HTTP HTTPExceptions for FastAPI router
class CredentialsException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
