from pydantic import BaseModel


class GorgiasChatOutput(BaseModel):
    message: str
    code: str


class GorgiasUserOutput(BaseModel):
    message: str
    code_lines: list[str]
