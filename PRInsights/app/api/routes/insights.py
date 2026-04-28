"""
Insights API Route.
Endpoints for PR insights, metrics, and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.modules.business_accounts.service import RepositoryService
from app.modules.pr_comments.service import PRCommentService
from app.modules.pr_insights.service import InsightsService

router = APIRouter(prefix="/insights", tags=["insights"])


# ==================== Repository Insights ====================

@router.get("/repos")
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all tracked repositories"""
    service = RepositoryService(db)
    repos = service.get_all_repositories(skip=skip, limit=limit)
    return {
        "repositories": [
            {
                "id": r.id,
                "github_repo_id": r.github_repo_id,
                "full_name": r.full_name,
                "owner": r.owner,
                "name": r.name
            }
            for r in repos
        ]
    }


@router.get("/repos/{repo_id}")
async def get_repo_summary(repo_id: int, db: Session = Depends(get_db)):
    """Get summary metrics for a repository"""
    insights = InsightsService(db)
    summary = insights.get_repo_summary(repo_id)
    
    if not summary:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    return summary


@router.get("/repos/{repo_id}/top-commenters")
async def get_repo_top_commenters(
    repo_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top commenters for a specific repo"""
    insights = InsightsService(db)
    return {"top_commenters": insights.get_top_commenters(repo_id=repo_id, limit=limit)}


@router.get("/repos/{repo_id}/most-discussed")
async def get_repo_most_discussed_prs(
    repo_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get most discussed PRs in a repo"""
    insights = InsightsService(db)
    return {"most_discussed_prs": insights.get_most_discussed_prs(repo_id=repo_id, limit=limit)}


# ==================== PR Insights ====================

@router.get("/prs/{pr_id}")
async def get_pr_insights(pr_id: int, db: Session = Depends(get_db)):
    """
    Get detailed insights for a specific PR.
    
    Returns:
    - Comment count
    - Unique reviewers
    - Turnaround time (if merged)
    - Time to first review
    """
    insights = InsightsService(db)
    pr_insights = insights.get_pr_insights(pr_id)
    
    if not pr_insights:
        raise HTTPException(status_code=404, detail="Pull request not found")
    
    return pr_insights


@router.get("/prs/{pr_id}/comments")
async def get_pr_comments(pr_id: int, db: Session = Depends(get_db)):
    """Get all comments for a PR"""
    service = PRCommentService(db)
    comments = service.get_comments_by_pr(pr_id)
    
    return {
        "pr_id": pr_id,
        "comment_count": len(comments),
        "comments": [
            {
                "id": c.id,
                "github_comment_id": c.github_comment_id,
                "user_id": c.user_id,
                "body": c.body,
                "comment_type": c.comment_type,
                "created_at": c.gh_created_at.isoformat() if c.gh_created_at else None
            }
            for c in comments
        ]
    }


# ==================== Global Insights ====================

@router.get("/most-discussed")
async def get_most_discussed_prs_global(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get most discussed PRs across all repos"""
    insights = InsightsService(db)
    return {"most_discussed_prs": insights.get_most_discussed_prs(limit=limit)}


@router.get("/summary")
async def get_global_summary(db: Session = Depends(get_db)):
    """
    Get global summary across all tracked repos.
    High-level metrics dashboard.
    """
    from sqlalchemy import func
    from app.modules.user_accounts.models import User
    from app.modules.business_accounts.models import Repository
    from app.modules.pr_comments.models import PullRequest, Comment
    
    total_users = db.query(func.count(User.id)).scalar()
    total_repos = db.query(func.count(Repository.id)).scalar()
    total_prs = db.query(func.count(PullRequest.id)).scalar()
    total_comments = db.query(func.count(Comment.id)).scalar()
    
    open_prs = db.query(func.count(PullRequest.id)).filter(
        PullRequest.state == "open"
    ).scalar()
    
    merged_prs = db.query(func.count(PullRequest.id)).filter(
        PullRequest.state == "merged"
    ).scalar()
    
    return {
        "total_users": total_users,
        "total_repositories": total_repos,
        "total_pull_requests": total_prs,
        "open_pull_requests": open_prs,
        "merged_pull_requests": merged_prs,
        "total_comments": total_comments,
        "avg_comments_per_pr": round(total_comments / total_prs, 2) if total_prs > 0 else 0
    }
