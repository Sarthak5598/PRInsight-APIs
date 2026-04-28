"""
Users API Route.
Endpoints for user-related queries and insights.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.modules.user_accounts.service import UserService
from app.modules.pr_insights.service import InsightsService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users with pagination"""
    service = UserService(db)
    users = service.get_all_users(skip=skip, limit=limit)
    return {
        "users": [
            {
                "id": u.id,
                "github_id": u.github_id,
                "username": u.username,
                "avatar_url": u.avatar_url
            }
            for u in users
        ]
    }


@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    from app.modules.user_accounts.models import User
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "github_id": user.github_id,
        "username": user.username,
        "avatar_url": user.avatar_url
    }


@router.get("/{user_id}/activity")
async def get_user_activity(user_id: int, db: Session = Depends(get_db)):
    """Get comprehensive activity summary for a user"""
    insights = InsightsService(db)
    summary = insights.get_user_activity_summary(user_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="User not found")
    
    return summary


@router.get("/{user_id}/consistency")
async def get_reviewer_consistency(user_id: int, db: Session = Depends(get_db)):
    """Get reviewer consistency metrics across repos"""
    insights = InsightsService(db)
    consistency = insights.get_reviewer_consistency(user_id)
    return consistency


@router.get("/top/commenters")
async def get_top_commenters(
    repo_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get users who comment the most"""
    insights = InsightsService(db)
    return {"top_commenters": insights.get_top_commenters(repo_id=repo_id, limit=limit)}


@router.get("/top/authors")
async def get_top_pr_authors(
    repo_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get users who author the most PRs"""
    insights = InsightsService(db)
    return {"top_authors": insights.get_top_pr_authors(repo_id=repo_id, limit=limit)}


@router.get("/top/reviewers")
async def get_top_reviewers(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top reviewers across all repos (global metric)"""
    insights = InsightsService(db)
    return {"top_reviewers": insights.get_global_top_reviewers(limit=limit)}
