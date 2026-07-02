"""Custom Exception Classes"""

class FileParsingError(Exception):
    """Raised when file parsing fails"""
    pass

class LLMProcessingError(Exception):
    """Raised when LLM API processing fails"""
    pass

class ValidationError(Exception):
    """Raised when validation fails"""
    pass
