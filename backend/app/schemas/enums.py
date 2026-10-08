from enum import Enum


class SourceType(str, Enum):
    TICKET = "ticket"
    EMAIL = "email"


class Channel(str, Enum):
    VOICE = "voice"
    CHAT = "chat"
    EMAIL = "email"


class ContentFormat(str, Enum):
    TEXT = "text"
    HTML = "html"


class Language(str, Enum):
    ENGLISH = "english"
    HINGLISH = "hinglish"


class Vertical(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    FLIGHT = "flight"
    EKYC = "ekyc"
    SHIPMENT = "shipment"
    HR = "hr"


class RagMode(str, Enum):
    HYBRID = "hybrid"
    DENSE = "dense"
    SPARSE = "sparse"


class ChurnRiskClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AiSuggestionOutcome(str, Enum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    OVERRIDE = "OVERRIDE"
    REJECT = "REJECT"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    NONE = "NONE"


class LlmProvider(str, Enum):
    GROQ = "groq"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class UserRole(str, Enum):
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    DIRECTOR = "director"


class ErrorCode(str, Enum):
    BAD_REQUEST = "BAD_REQUEST"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    DUPLICATE_TICKET = "DUPLICATE_TICKET"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VECTOR_STORE_UNAVAILABLE = "VECTOR_STORE_UNAVAILABLE"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    SERVICE_OVERLOADED = "SERVICE_OVERLOADED"
