from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)
    role = Column(String, default="user")

    # Relationships
    quiz_results = relationship("QuizResult", back_populates="user")


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(
        Integer, autoincrement=True, primary_key=True, unique=True, nullable=False
    )
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    name = Column(String, index=True)
    thumbnail_image = Column(String)
    theory_file = Column(String)
    practical_file = Column(String, nullable=True)
    consultation_sheet = Column(String, nullable=True)

    # Relationships
    quiz = relationship("Quiz", uselist=False, back_populates="lesson")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    name = Column(String, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), unique=True)
    quiz_json = Column(
        String
    )  # json string [{ type: "multiple_choice", questions: [ { question_id: 1 ,question: "What is 1+1?", answers: ["1", "2", "3", "4"]} ] }]
    quiz_answers = Column(String)  # json string [{ question_id: 1, answer: 2 }]
    duration = Column(Integer)

    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    quiz_results = relationship("QuizResult", back_populates="quiz")


class QuizResult(Base):
    __tablename__ = "quiz_results"
    __table_args__ = (UniqueConstraint("user_id", "quiz_id", name="unique_user_quiz"),)

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    score = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    submitted_answers = Column(String)  # json string [{ question_id: 1, answer: 2 }]

    # Relationships
    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="quiz_results")
