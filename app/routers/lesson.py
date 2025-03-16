from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_helper import admin_required, user_required
from ..database import crud
from ..database.database import async_get_db
from ..database.schemas import Lesson
from ..utils.file_operations import (
    save_lesson_files,
    get_lesson_file_path,
    delete_lesson_files,
    delete_lesson_dir,
)

router = APIRouter(tags=["LESSON"])


@router.get("/all", response_model=List[Lesson])
async def get_all_lessons(
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await crud.get_all_lessons(db)


@router.get("/get/{lesson_id}", response_model=Lesson)
async def get_lesson(
    lesson_id: int,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    lesson = await crud.get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )
    return Lesson(
        id=lesson.id,
        name=lesson.name,
        thumbnail_image=lesson.thumbnail_image,
        theory_file=lesson.theory_file,
        practical_file=lesson.practical_file,
        consultation_sheet=lesson.consultation_sheet,
    )


@router.post("/create")
async def create_lesson(
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    name: Annotated[str, Form()],
    thumbnail_image: Annotated[UploadFile, File()],
    theory_file: Annotated[UploadFile, File()],
    practical_file: Annotated[Optional[UploadFile], File()] = None,
    consultation_sheet: Annotated[Optional[UploadFile], File()] = None,
):
    files = [thumbnail_image, theory_file]
    if practical_file:
        files.append(practical_file)
    if consultation_sheet:
        files.append(consultation_sheet)
    next_lesson_id = await crud.get_max_lesson_id(db)
    lesson_id = await crud.insert_lesson(
        db,
        name,
        get_lesson_file_path(next_lesson_id, thumbnail_image.filename),
        get_lesson_file_path(next_lesson_id, theory_file.filename),
        (
            get_lesson_file_path(next_lesson_id, practical_file.filename)
            if practical_file
            else None
        ),
        (
            get_lesson_file_path(next_lesson_id, consultation_sheet.filename)
            if consultation_sheet
            else None
        ),
    )
    await save_lesson_files(lesson_id, files)
    return {"message": "Lesson created successfully"}


@router.patch("/update/{lesson_id}")
async def update_lesson(
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    lesson_id: int,
    name: Annotated[str, Form()],
    thumbnail_image: Annotated[UploadFile, File()],
    theory_file: Annotated[UploadFile, File()],
    practical_file: Annotated[Optional[UploadFile], File()] = None,
    consultation_sheet: Annotated[Optional[UploadFile], File()] = None,
):
    delete_files = []
    save_files = []
    lesson = await crud.get_lesson_by_id(db, lesson_id)
    if lesson:
        if thumbnail_image:
            save_files.append(thumbnail_image)
            delete_files.append(lesson.thumbnail_image)
        if theory_file:
            save_files.append(theory_file)
            delete_files.append(lesson.theory_file)
        if practical_file:
            save_files.append(practical_file)
            delete_files.append(lesson.practical_file)
        if consultation_sheet:
            save_files.append(consultation_sheet)
            delete_files.append(lesson.consultation_sheet)
        await delete_lesson_files(delete_files)
    await crud.update_lesson(
        db,
        lesson_id,
        name,
        get_lesson_file_path(lesson_id, thumbnail_image.filename),
        get_lesson_file_path(lesson_id, theory_file.filename),
        (
            get_lesson_file_path(lesson_id, practical_file.filename)
            if practical_file
            else None
        ),
        (
            get_lesson_file_path(lesson_id, consultation_sheet.filename)
            if consultation_sheet
            else None
        ),
    )
    await save_lesson_files(lesson_id, save_files)
    return {"message": "Lesson updated successfully"}


@router.delete("/delete/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    await crud.delete_lesson(db, lesson_id)
    await delete_lesson_dir(lesson_id)
    return {"message": "Lesson deleted successfully"}
