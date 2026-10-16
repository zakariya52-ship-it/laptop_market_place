"""Backend health endpoint."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, bool | str]:
    """Report API availability and whether the model is loaded."""
    model_loaded = getattr(request.app.state, "model", None) is not None
    return {"status": "ok", "model_loaded": model_loaded}