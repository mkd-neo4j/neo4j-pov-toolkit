"""
FCA Handbook Loader Exceptions

Custom exception hierarchy for better error handling and recovery.
"""

from typing import Optional


class FCALoaderError(Exception):
    """Base exception for FCA loader errors"""
    pass


class FCAAPIError(FCALoaderError):
    """Base exception for FCA API-related errors"""
    pass


class TransientAPIError(FCAAPIError):
    """Temporary API error that may succeed on retry"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class PermanentAPIError(FCAAPIError):
    """Permanent API error that won't succeed on retry"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class DataValidationError(FCALoaderError):
    """Data validation or integrity error"""
    def __init__(self, message: str, entity_type: Optional[str] = None, entity_id: Optional[str] = None):
        super().__init__(message)
        self.entity_type = entity_type
        self.entity_id = entity_id


class Neo4jOperationError(FCALoaderError):
    """Neo4j operation error"""
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(message)
        self.query = query


class TemporalVersionError(FCALoaderError):
    """Error in temporal versioning logic"""
    def __init__(self, message: str, entity_type: Optional[str] = None, entity_id: Optional[str] = None):
        super().__init__(message)
        self.entity_type = entity_type
        self.entity_id = entity_id
