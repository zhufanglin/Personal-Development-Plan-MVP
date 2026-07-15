from uuid import uuid4
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    status = Column(String(20), default="not_started")
    current_question = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")
    result = relationship("AssessmentResult", back_populates="assessment", uselist=False, cascade="all, delete-orphan")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    type = Column(String(20), nullable=False)
    dimension = Column(String(50), nullable=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id"), nullable=False)
    question_id = Column(String(36), ForeignKey("assessment_questions.id"), nullable=False)
    answer_value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())

    assessment = relationship("Assessment", back_populates="responses")
    question = relationship("AssessmentQuestion")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    assessment_id = Column(String(36), ForeignKey("assessments.id"), unique=True, nullable=False)
    type = Column(String(20), nullable=False)
    result_data = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    assessment = relationship("Assessment", back_populates="result")

class AssessmentHistory(Base):
    __tablename__ = "assessment_histories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    result_snapshot = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
