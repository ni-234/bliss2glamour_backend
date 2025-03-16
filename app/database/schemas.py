from datetime import datetime
from re import match as re_match
from typing import Optional

from fastapi import HTTPException, status
from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated


def email_validator(email: str):
    try:
        if not re_match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email address")
        return email
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def password_validator(password: str):
    try:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in password):
            raise ValueError("Password must contain at least one letter")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()-_+=~`[]{}|;:,.<>?/" for char in password):
            raise ValueError("Password must contain at least one special character")
        return password
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


class CreateUserSchema(BaseModel):
    first_name: str
    last_name: str
    username: Annotated[str, AfterValidator(email_validator)]
    password: Annotated[str, AfterValidator(password_validator)]


class UpdateUserSchema(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    password: Annotated[Optional[str], AfterValidator(password_validator)]


class GetAllUsersSchema(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    is_active: bool
    role: str


class User(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    hashed_password: str
    is_active: bool
    role: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str


class Lesson(BaseModel):
    id: int
    name: str
    thumbnail_image: str
    theory_file: str
    practical_file: Optional[str]
    consultation_sheet: Optional[str]


class CreateQuizSchema(BaseModel):
    name: str
    lesson_id: int
    quiz_json: dict
    quiz_answers: dict
    duration: int


class QuizDetails(BaseModel):
    id: int
    name: str
    lesson_id: int
    quiz_json: str
    duration: int


class LessonWithQuiz(BaseModel):
    id: int
    name: str
    thumbnail_image: str
    theory_file: str
    practical_file: Optional[str]
    consultation_sheet: Optional[str]
    quiz: Optional[QuizDetails]


class StartQuizRequest(BaseModel):
    lesson_id: int
    user_id: int


class SubmitQuizRequest(BaseModel):
    quiz_id: int
    start_time: datetime
    end_time: datetime
    submitted_answers: dict


class QuizStartResponse(BaseModel):
    id: int
    name: str
    lesson_id: int
    quiz_json: str
    duration: int
