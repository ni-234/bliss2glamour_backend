from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_helper import get_current_user, user_required, admin_required
from ..database import crud
from ..database.database import async_get_db
from ..database.models import User
from ..database.schemas import (
    CreateQuizSchema,
    QuizDetails,
    StartQuizRequest,
    SubmitQuizRequest,
)

router = APIRouter(tags=["QUIZ"])


@router.get("/get_quiz/{lesson_id}")
async def get_quiz(
    lesson_id: int,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz = await crud.get_quiz_by_lesson_id(db, lesson_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
        )
    return QuizDetails(
        id=quiz.id,
        name=quiz.name,
        lesson_id=quiz.lesson_id,
        quiz_json=quiz.quiz_json,
        duration=quiz.duration,
    )


@router.get("/quiz_results/{quiz_id}")
async def get_quiz_results(
    quiz_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz_result = await crud.get_existing_quiz_result(db, current_user.id, quiz_id)
    if not quiz_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz result not found"
        )
    return quiz_result


@router.get("/quiz_results_by_uid/{quiz_id}/{user_id}")
async def get_quiz_results_by_uid(
    quiz_id: int,
    user_id: int,
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz_result = await crud.get_existing_quiz_result(db, user_id, quiz_id)
    if not quiz_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz result not found"
        )
    return quiz_result


@router.post("/start_quiz")
async def start_quiz(
    quiz_data: StartQuizRequest,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz_result = await crud.start_quiz(db, quiz_data.lesson_id, quiz_data.user_id)
    if not quiz_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz result not found"
        )
    return quiz_result


@router.post("/submit_quiz")
async def submit_quiz(
    quiz_data: SubmitQuizRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz_result = await crud.submit_quiz(db, quiz_data, current_user.id)
    if not quiz_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz result not found"
        )
    return quiz_result


@router.post("/create_quiz")
async def create_quiz(
    cqs: CreateQuizSchema,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    quiz_create = await crud.create_quiz(db, cqs)
    if not quiz_create:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not Created"
        )
    return quiz_create
