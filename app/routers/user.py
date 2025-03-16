from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_helper import (
    admin_required,
    get_current_user,
    hashPassword,
    user_required,
)
from ..database import crud
from ..database.database import async_get_db
from ..database.models import User
from ..database.schemas import GetAllUsersSchema, UpdateUserSchema

router = APIRouter(tags=["USER"])


@router.get("/all", response_model=List[GetAllUsersSchema])
async def get_all_users(
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await crud.get_all_users(db)


@router.get("/get/{user_id}", response_model=GetAllUsersSchema)
async def get_user(
    user_id: int,
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return GetAllUsersSchema(
        id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        role=user.role,
    )


@router.get("/me", response_model=GetAllUsersSchema)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[bool, Depends(user_required)],
):
    return GetAllUsersSchema(
        id=current_user.id,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        role=current_user.role,
    )


@router.get("/inactive", response_model=List[GetAllUsersSchema])
async def get_inactive_users(
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    return await crud.get_all_inactive_users(db)


@router.patch("/update/{user_id}")
async def update_user(
    user_id: int,
    user: UpdateUserSchema,
    _: Annotated[bool, Depends(user_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    hashed_password = None
    if user.password:
        hashed_password = hashPassword(user.password)
    crud.update_user(db, user_id, user.first_name, user.last_name, hashed_password)
    return {"message": "User updated successfully"}


@router.patch("/activate-status/{user_id}/")
async def active_status(
    user_id: int,
    status: bool,
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    await crud.update_active_status(db, user_id, status)
    return {"message": "User activated successfully"}


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[bool, Depends(admin_required)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    await crud.delete_user(db, user_id, current_user)
    return {"message": "User deleted successfully"}
