from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.assessment_service import assessment_service, ASSESSMENT_TYPES

router = APIRouter()

class AnswerRequest(BaseModel):
    question_id: str
    answer_value: dict

@router.get("")
async def list_assessments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.get_assessments_status(user.id, db)

@router.post("/{assessment_type}/start")
async def start_assessment(
    assessment_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if assessment_type not in ASSESSMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的测评类型: {assessment_type}")
    assessment, questions = await assessment_service.start_assessment(user.id, assessment_type, db)
    return {
        "assessment": {
            "id": str(assessment.id),
            "type": assessment.type,
            "status": assessment.status,
            "current_question": assessment.current_question,
            "total_questions": assessment.total_questions,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
        },
        "questions": questions,
    }

@router.get("/growth-profile")
async def get_growth_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.get_growth_profile(user.id, db)

@router.get("/{assessment_type}/questions")
async def get_questions(
    assessment_type: str,
    user: User = Depends(get_current_user),
):
    if assessment_type not in ASSESSMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的测评类型: {assessment_type}")
    questions = await assessment_service.get_questions(assessment_type)
    return {"type": assessment_type, "questions": questions, "total": len(questions)}

@router.post("/{assessment_id}/answer")
async def submit_answer(
    assessment_id: str,
    body: AnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await assessment_service.submit_answer(assessment_id, body.question_id, body.answer_value, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{assessment_id}/submit")
async def submit_assessment(
    assessment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await assessment_service.submit_assessment(assessment_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{assessment_id}/result")
async def get_result(
    assessment_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await assessment_service.get_result(assessment_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="测评结果不存在或测评尚未完成")
    return result

@router.get("/history")
async def list_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.get_history(user.id, db)

@router.get("/{assessment_type}/history")
async def get_type_history(
    assessment_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if assessment_type not in ASSESSMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的测评类型: {assessment_type}")
    return await assessment_service.get_type_history(user.id, assessment_type, db)
