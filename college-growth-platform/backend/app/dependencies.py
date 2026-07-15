from uuid import uuid4
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"

async def get_or_create_dev_user(db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == DEV_USER_ID))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=DEV_USER_ID,
            email="dev@localhost.com",
            nickname="开发用户",
            password_hash="dev-mode",
            role="student",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if credentials is None:
        user = await get_or_create_dev_user(db)
        user.id = str(user.id)
        return user

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return await get_or_create_dev_user(db)
    except JWTError:
        return await get_or_create_dev_user(db)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return await get_or_create_dev_user(db)
    return user

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    return await get_current_user(credentials, db)
