from pydantic import BaseModel


class AiQueryRequest(BaseModel):
    query: str
