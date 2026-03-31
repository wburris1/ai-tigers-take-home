import os

from google import genai
from google.genai import errors as genai_errors
from fastapi import APIRouter, Depends, HTTPException

from deps import get_current_user
from models.ai_query import AiQueryRequest

router = APIRouter(prefix="/api", tags=["ai"])


@router.post("/ai-request")
def ai_request(
    body: AiQueryRequest,
    _user: dict = Depends(get_current_user),
):
    """Send `query` to Google Gemini via the GenAI SDK (see Gemini API quickstart)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured",
        )
    model = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=body.query,
        )
    except genai_errors.APIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(exc),
                "code": exc.code,
                "details": exc.details,
            },
        ) from exc

    text = response.text
    if text is None:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned no text in the response",
        )

    return {"text": text, "model": model}
