from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class OptionSchema(BaseModel):
    label: str
    value: int

class AssessmentQuestionSchema(BaseModel):
    id: UUID
    type: str
    dimension: str | None = None
    question_text: str
    options: list[OptionSchema]
    sort_order: int

    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    id: UUID
    type: str
    status: str
    current_question: int = 0
    total_questions: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentDetail(AssessmentBase):
    responses: list["AssessmentResponseSchema"] = []

class AssessmentResponseSchema(BaseModel):
    id: UUID
    question_id: UUID
    answer_value: Any

    class Config:
        from_attributes = True

class AnswerSubmit(BaseModel):
    question_id: UUID
    answer_value: Any

class AssessmentResultSchema(BaseModel):
    id: UUID
    type: str
    result_data: Any
    summary: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssessmentHistorySchema(BaseModel):
    id: UUID
    type: str
    result_snapshot: Any
    version: int
    created_at: datetime

    class Config:
        from_attributes = True

class StartAssessmentResponse(BaseModel):
    assessment: AssessmentBase
    questions: list[AssessmentQuestionSchema]

class AssessmentListResponse(BaseModel):
    holland: AssessmentBase | None = None
    ability: AssessmentBase | None = None
    values: AssessmentBase | None = None
    learning_habit: AssessmentBase | None = None
    readiness: AssessmentBase | None = None

class SubmitResponse(BaseModel):
    assessment_id: UUID
    result: AssessmentResultSchema
    message: str = "测评提交成功"
