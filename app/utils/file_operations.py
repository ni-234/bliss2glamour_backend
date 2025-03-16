import asyncio
from os import makedirs
from os.path import join
from shutil import rmtree

import aiofiles
from aiofiles.os import path, remove
from fastapi import UploadFile

from ..settings import settings

LESSONS_DIR = join("data", "lessons")


def get_lesson_file_path(lesson_id: int, file_name: str) -> str:
    return join(LESSONS_DIR, f"L_{lesson_id}", file_name).replace("\\", "/")


async def save_lesson_files(lesson_id: int, files: list[UploadFile]):
    LESSON_ROOT_DIR = join(settings.ROOT_DIR, "..", LESSONS_DIR, f"L_{lesson_id}")
    if not await path.exists(LESSON_ROOT_DIR):
        await asyncio.to_thread(makedirs, LESSON_ROOT_DIR)

    for file in files:
        file_path = join(
            settings.ROOT_DIR, "..", get_lesson_file_path(lesson_id, file.filename)
        )

        async with aiofiles.open(file_path, "wb") as f:
            file_content = await file.read()
            await f.write(file_content)


async def delete_lesson_files(files: list[str]):
    for file in files:
        file_path = join(settings.ROOT_DIR, "..", file)
        try:
            await remove(file_path)
        except FileNotFoundError:
            pass


async def delete_lesson_dir(lesson_id: int):
    lesson_dir = join(settings.ROOT_DIR, "..", LESSONS_DIR, f"L_{lesson_id}")
    try:
        if not await path.exists(lesson_dir):
            return
        if not await path.isdir(lesson_dir):
            return
        await asyncio.to_thread(rmtree, lesson_dir)
    except FileNotFoundError:
        pass
