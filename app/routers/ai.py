from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_helper import (
    user_required,
)
from ..database.database import async_get_db
from ..ai.schema import Request
from ..ai.ai_helper import generate_completion
from ..utils.fastapi_globals import g

router = APIRouter(tags=["AI"])


@router.post("/chat")
async def chat(
    request: Request,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    protocol: str = Query("data"),
):
    messages = request.messages
    mList = [{"role": message.role, "content": message.content} for message in messages]
    pipe = g.qwen
    streaming_response = generate_completion(pipe, mList)
    response = StreamingResponse(streaming_response)
    response.headers["x-vercel-ai-data-stream"] = "v1"
    return response
