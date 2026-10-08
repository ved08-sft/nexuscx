from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict
from app.schemas.enums import ErrorCode


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    loc: List[Union[str, int]]
    msg: str
    type: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    code: ErrorCode
    message: str
    request_id: str
    details: Optional[List[ErrorDetail]] = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    error: ErrorBody
