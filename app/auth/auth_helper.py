from re import match as re_match
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import crud
from ..database.database import async_get_db, async_session_maker
from ..database.models import User
from ..settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashPassword(password: str):
    return pwd_context.hash(password)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await crud.get_user_by_username(db, username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user


async def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def verify_token(token: str, db: AsyncSession):
    is_blacklisted = await crud.get_token_blacklist(db, token)
    if is_blacklisted:
        return None

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        exp = payload.get("exp")
        if exp is None:
            return None
        if datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
        return username
    except JWTError:
        return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(async_get_db),
):
    user_email = await verify_token(token, db)
    if user_email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    user = await crud.get_user_by_username(db, user_email)

    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


async def do_bypass_active_check(path: str) -> bool:
    match path:
        case "/api/user/me":
            return True
        case _:
            return False


async def get_current_active_user(
    request: Request, current_user: Annotated[User, Depends(get_current_user)]
):
    if not await do_bypass_active_check(request.url.path):
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def blacklist_token(token: str, db: AsyncSession):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    expires_at = datetime.fromtimestamp(payload.get("exp"))
    await crud.insert_token_blacklist(db, token, expires_at)


class RoleChecker:
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        user: Annotated[User, Depends(get_current_active_user)],
        token: Annotated[str, Depends(oauth2_scheme)],
        db: AsyncSession = Depends(async_get_db),
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

        try:
            user_email = await verify_token(token, db)
            if not user_email or user_email != user.username:
                raise credentials_exception
            db_user = await crud.get_user_by_username(db, user_email)
            if not db_user:
                raise credentials_exception
            if db_user.role != user.role:
                raise credentials_exception
        except (JWTError, ValidationError):
            raise credentials_exception

        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You don't have enough permissions",
            )

        return True


class AuthDataFiles(StaticFiles):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(
        self,
        scope,
        receive,
        send,
    ) -> None:

        assert scope["type"] == "http"

        request = Request(scope, receive)
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
        token = await oauth2_scheme(request)
        path = request.url.path
        thumbnail_image_pattern = r"^\/data\/lessons\/L_\d+\/.*\.(png|jpg)$"
        async with async_session_maker() as db:
            user_email = await verify_token(token, db)
            if not user_email:
                raise credentials_exception
            db_user = await crud.get_user_by_username(db, user_email)
            if not db_user:
                raise credentials_exception
            if not db_user.is_active and not re_match(thumbnail_image_pattern, path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
                )
        await super().__call__(scope, receive, send)


admin_required = RoleChecker(["admin"])
user_required = RoleChecker(["user", "admin"])
