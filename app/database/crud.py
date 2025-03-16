from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .schemas import (
    CreateQuizSchema,
    GetAllUsersSchema,
    Lesson,
    LessonWithQuiz,
    QuizDetails,
    User,
    SubmitQuizRequest,
)
from ..utils.score_cal import calculate_quiz_score


async def insert_user(db: AsyncSession, username: str, hashed_password: str):
    """Insert a new user into the database"""
    db_user = models.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)


async def get_user_by_username(session: AsyncSession, username: str):
    """Get a user by its username"""
    try:
        statement = select(models.User).filter(models.User.username == username)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def create_user(
    session: AsyncSession,
    username: str,
    first_name: str,
    last_name: str,
    hashed_password: str,
):
    """Create a new user"""
    check_user = await get_user_by_username(session, username)
    if check_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    try:
        db_user = models.User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password,
        )
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return GetAllUsersSchema(
            id=db_user.id,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            is_active=db_user.is_active,
            role=db_user.role,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_user_by_id(session: AsyncSession, id: int):
    """Get a user by its id"""
    try:
        statement = select(models.User).filter(models.User.id == id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def create_default_admin_user(
    session: AsyncSession,
    username: str,
    first_name: str,
    last_name: str,
    hashed_password: str,
):
    """Create a default admin user"""
    user = await get_user_by_username(session, username)
    if user:
        return
    db_user = models.User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)


async def get_all_inactive_users(session: AsyncSession) -> List[GetAllUsersSchema]:
    """Get all inactive users from the database"""
    statement = select(models.User).filter(~models.User.is_active)
    result = await session.execute(statement)
    users = result.scalars().all()
    return [
        GetAllUsersSchema(
            id=user.id, username=user.username, is_active=user.is_active, role=user.role
        )
        for user in users
    ]


async def get_all_users(session: AsyncSession) -> List[GetAllUsersSchema]:
    """Get all users from the database without role and hashed_password"""
    statement = select(models.User)
    result = await session.execute(statement)
    users = result.scalars().all()
    return [
        GetAllUsersSchema(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            role=user.role,
        )
        for user in users
    ]


def update_user(
    session: AsyncSession,
    user_id: int,
    first_name: Optional[str],
    last_name: Optional[str],
    hashed_password: Optional[str],
):
    """Update a user in the database"""
    db_user = get_user_by_id(session, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    try:
        if first_name:
            db_user.first_name = first_name
        if last_name:
            db_user.last_name = last_name
        if hashed_password:
            db_user.hashed_password = hashed_password
        session.commit()
        session.refresh(db_user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def update_active_status(session: AsyncSession, user_id: int, status: bool):
    """Activate a user in the database"""
    check_user = await get_user_by_id(session, user_id)
    if not check_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if check_user.is_active == status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
        )
    if check_user.role == "admin" and not status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate admin user",
        )
    try:
        check_user.is_active = status
        await session.commit()
        await session.refresh(check_user)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def delete_user(session: AsyncSession, user_id: int, current_user: User):
    db_user = await get_user_by_id(session, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if db_user.id == current_user.id and current_user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself"
        )
    try:
        await session.delete(db_user)
        await session.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def insert_token_blacklist(
    session: AsyncSession, token: str, expires_at: datetime
):
    """Insert a token into the blacklist"""
    try:
        db_token = models.TokenBlacklist(token=token, expires_at=expires_at)
        session.add(db_token)
        await session.commit()
        await session.refresh(db_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_token_blacklist(session: AsyncSession, token: str):
    """Get a token from the blacklist"""
    try:
        statement = select(models.TokenBlacklist).filter(
            models.TokenBlacklist.token == token
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def insert_lesson(
    session: AsyncSession,
    name: str,
    thumbnail_image: str,
    theory_file: str,
    practical_file: Optional[str],
    consultation_sheet: Optional[str],
) -> int:
    """Insert a new lesson into the database"""
    try:
        db_lesson = models.Lesson(
            name=name,
            thumbnail_image=thumbnail_image,
            theory_file=theory_file,
            practical_file=practical_file,
            consultation_sheet=consultation_sheet,
        )
        session.add(db_lesson)
        await session.commit()
        await session.refresh(db_lesson)
        return db_lesson.id
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_all_lessons(session: AsyncSession) -> List[Lesson]:
    """Get all lessons from the database"""
    try:
        statement = select(models.Lesson)
        result = await session.execute(statement)
        lessons = result.scalars().all()
        return [
            Lesson(
                id=lesson.id,
                name=lesson.name,
                thumbnail_image=lesson.thumbnail_image,
                theory_file=lesson.theory_file,
                practical_file=lesson.practical_file,
                consultation_sheet=lesson.consultation_sheet,
            )
            for lesson in lessons
        ]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_lesson_by_id(session: AsyncSession, id: int):
    """Get a lesson by its id"""
    try:
        statement = select(models.Lesson).filter(models.Lesson.id == id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_lesson_by_id_with_quiz(session: AsyncSession, id: int):
    """Get a lesson by its id with quiz"""
    try:
        statement = select(models.Lesson).filter(models.Lesson.id == id)
        result = await session.execute(statement)
        lesson = result.scalar_one_or_none()
        if not lesson:
            return None
        quiz = await get_quiz_by_lesson_id(session, id)
        return LessonWithQuiz(
            id=lesson.id,
            name=lesson.name,
            thumbnail_image=lesson.thumbnail_image,
            theory_file=lesson.theory_file,
            practical_file=lesson.practical_file,
            consultation_sheet=lesson.consultation_sheet,
            quiz=QuizDetails(
                id=quiz.id,
                name=quiz.name,
                lesson_id=quiz.lesson_id,
                duration=quiz.duration,
            ),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def delete_lesson(session: AsyncSession, lesson_id: int):
    """Delete a lesson from the database"""
    db_lesson = await get_lesson_by_id(session, lesson_id)
    if not db_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    try:
        await session.delete(db_lesson)
        await session.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def update_lesson(
    session: AsyncSession,
    id: int,
    name: Optional[str],
    thumbnail_image: Optional[str],
    theory_file: Optional[str],
    practical_file: Optional[str],
    consultation_sheet: Optional[str],
):
    """Update a lesson in the database"""
    db_lesson = await get_lesson_by_id(session, id)
    if not db_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    try:
        db_lesson.name = name
        if thumbnail_image:
            db_lesson.thumbnail_image = thumbnail_image
        if theory_file:
            db_lesson.theory_file = theory_file
        if practical_file:
            db_lesson.practical_file = practical_file
        if consultation_sheet:
            db_lesson.consultation_sheet = consultation_sheet
        await session.commit()
        await session.refresh(db_lesson)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_max_lesson_id(session: AsyncSession):
    try:
        result = await session.execute(func.max(models.Lesson.id))
        id = result.scalar()
        if not id:
            return 1
        return id + 1
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_quiz_by_lesson_id(session: AsyncSession, lesson_id: int):
    try:
        statement = select(models.Quiz).filter(models.Quiz.lesson_id == lesson_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_quiz_by_id(session: AsyncSession, quiz_id: int):
    try:
        statement = select(models.Quiz).filter(models.Quiz.id == quiz_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def get_existing_quiz_result(session: AsyncSession, user_id: int, quiz_id: int):
    try:
        statement = select(models.QuizResult).filter(
            and_(
                models.QuizResult.user_id == user_id,
                models.QuizResult.quiz_id == quiz_id,
            )
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def start_quiz(db: AsyncSession, lesson_id: int, user_id: int):
    try:
        quiz = await get_quiz_by_lesson_id(db, lesson_id)
        if not quiz:
            raise HTTPException(
                status_code=404, detail="Quiz not found for this lesson"
            )
        existing_result = await get_existing_quiz_result(db, user_id, quiz.id)
        if existing_result and existing_result.end_time:
            raise HTTPException(
                status_code=400, detail="Quiz has already been completed"
            )
        if existing_result and not existing_result.end_time:
            return existing_result

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def submit_quiz(
    session: AsyncSession, quiz_data: SubmitQuizRequest, user_id: int
):
    try:
        quiz = await get_quiz_by_id(session, quiz_data.quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        quiz_score = calculate_quiz_score(quiz_data, quiz)
        quiz_result = models.QuizResult(
            score=quiz_score,
            user_id=user_id,
            quiz_id=quiz_data.quiz_id,
            start_time=quiz_data.start_time,
            end_time=quiz_data.end_time,
            submitted_answers=str(quiz_data.submitted_answers),
        )
        session.add(quiz_result)
        await session.commit()
        await session.refresh(quiz_result)
        return quiz_result
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )


async def create_quiz(session: AsyncSession, quiz: CreateQuizSchema):
    db_lesson = await get_lesson_by_id(session, quiz.lesson_id)
    if not db_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    db_quiz = await get_quiz_by_lesson_id(session, quiz.lesson_id)
    if db_quiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz already exists"
        )
    try:
        quiz = models.Quiz(
            name=quiz.name,
            lesson_id=quiz.lesson_id,
            quiz_json=str(quiz.quiz_json),
            quiz_answers=str(quiz.quiz_answers),
            duration=quiz.duration,
        )
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)
        return quiz
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error"
        )
