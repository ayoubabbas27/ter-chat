from pydantic import BaseModel, Field

class GorgiasChatOutput(BaseModel):
    message: str
    code: str

class GorgiasUserOutput(BaseModel):
    message: str
    code_lines: list[str]


class GorgiasIntentExtractionOutput(BaseModel):
    confidence: float = Field(ge=0.0, le=1.0)
    intents: list[str] = Field(min_length=1)