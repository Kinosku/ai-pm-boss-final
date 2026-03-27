from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.developer import Developer
from schemas.user import UserUpdate, UserResponse
from routers.auth import get_current_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Shared settings page — profile section."""
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    payload: UserUpdate,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.patch("/password")
async def change_password(
    current_password: str,
    new_password:     str,
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from routers.auth import verify_password, hash_password
    if not verify_password(current_password, current_user.hashed_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "Password updated successfully"}


@router.get("/developer-profile")
async def get_developer_profile(
    db: AsyncSession   = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employee: get own developer profile (skills, integrations, role)."""
    result = await db.execute(
        select(Developer).where(Developer.user_id == current_user.id)
    )
    dev = result.scalar_one_or_none()
    if not dev:
        return {"developer": None}
    return {
        "developer": {
            "id":             dev.id,
            "role":           dev.role,
            "skills":         dev.skills,
            "github_username":dev.github_username,
            "slack_user_id":  dev.slack_user_id,
            "jira_account_id":dev.jira_account_id,
            "is_available":   dev.is_available,
            "velocity":       dev.velocity,
        }
    }


@router.patch("/developer-profile")
async def update_developer_profile(
    skills:          list[str] | None = None,
    github_username: str | None       = None,
    slack_user_id:   str | None       = None,
    db: AsyncSession                   = Depends(get_db),
    current_user: User                 = Depends(get_current_user),
):
    result = await db.execute(
        select(Developer).where(Developer.user_id == current_user.id)
    )
    dev = result.scalar_one_or_none()
    if not dev:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Developer profile not found")

    if skills is not None:          dev.skills          = skills
    if github_username is not None: dev.github_username = github_username
    if slack_user_id is not None:   dev.slack_user_id   = slack_user_id

    await db.flush()
    return {"message": "Developer profile updated"}
