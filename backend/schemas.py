from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User request to generate project content")
    model: str | None = Field(default="llama-3.1-8b-instant")


class GenerateResponse(BaseModel):
    result: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
