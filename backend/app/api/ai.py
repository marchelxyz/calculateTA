from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.schemas import AiMindmapRequest, AiMindmapResponse, AiParseRequest, AiParseResponse
from app.services.ai_service import parse_prompt_to_mindmap, parse_prompt_with_ai

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/parse", response_model=AiParseResponse)
def parse_prompt(
    payload: AiParseRequest,
    session: Session = Depends(get_db_session),
) -> AiParseResponse:
    """Parse prompt into module suggestions."""

    return parse_prompt_with_ai(session, payload.prompt)


@router.post("/mindmap", response_model=AiMindmapResponse)
def build_mindmap(
    payload: AiMindmapRequest,
    session: Session = Depends(get_db_session),
) -> AiMindmapResponse:
    """Build AI mindmap graph from prompt."""

    return parse_prompt_to_mindmap(session, payload.prompt)
