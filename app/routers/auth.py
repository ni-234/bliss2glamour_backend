from datetime import timedelta
from typing import Annotated

from jose import JWTError
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_helper import (
    authenticate_user,
    hashPassword,
    oauth2_scheme,
    blacklist_token,
    verify_token,
    create_access_token,
    create_refresh_token,
)
from ..database.crud import create_user
from ..database.database import async_get_db
from ..database.schemas import Token, CreateUserSchema
from ..settings import settings

router = APIRouter(tags=["AUTH"])


@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    refresh_token = await create_refresh_token(data={"sub": user.username})
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=max_age,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signup")
async def signup(
    user: CreateUserSchema,
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    hashed_password = hashPassword(user.password)
    return await create_user(
        db, user.username, user.first_name, user.last_name, hashed_password
    )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token not found"
        )

    user_email = await verify_token(refresh_token, db)

    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token"
        )

    new_access_token = await create_access_token(data={"sub": user_email})
    return Token(access_token=new_access_token, token_type="bearer")


@router.post("/logout")
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    access_token: str = Depends(oauth2_scheme),
):
    try:
        await blacklist_token(access_token, db)
        response.delete_cookie(key="refresh_token")
        return {"message": "Logout successful"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
