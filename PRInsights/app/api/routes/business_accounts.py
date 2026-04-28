"""
Business Accounts API Route.
Endpoints for registering and managing repositories (business accounts).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.modules.business_accounts.service import RepositoryService

router = APIRouter(prefix="/business-accounts", tags=["business-accounts"])


class CreateBusinessAccountRequest(BaseModel):
    """Request body for creating a business account"""
    github_repo_id: int
    name: str
    owner: str
    webhook_secret: str
    description: str = None


class UpdateWebhookSecretRequest(BaseModel):
    """Request body for updating webhook secret"""
    webhook_secret: str


@router.post("/")
async def create_business_account(
    request: CreateBusinessAccountRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new business account (repository).
    
    Call this when onboarding a new repo:
    1. Get the github_repo_id from GitHub API
    2. Set up webhook in GitHub with a secret
    3. Register here with the same secret
    """
    service = RepositoryService(db)
    
    try:
        repo = service.create_business_account(
            github_repo_id=request.github_repo_id,
            name=request.name,
            owner=request.owner,
            webhook_secret=request.webhook_secret,
            description=request.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": repo.id,
        "github_repo_id": repo.github_repo_id,
        "full_name": repo.full_name,
        "message": "Business account registered successfully"
    }


@router.get("/")
async def list_business_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all registered business accounts"""
    service = RepositoryService(db)
    repos = service.get_all_repositories(skip=skip, limit=limit)
    
    return {
        "business_accounts": [
            {
                "id": r.id,
                "github_repo_id": r.github_repo_id,
                "full_name": r.full_name,
                "owner": r.owner,
                "name": r.name,
                "is_active": r.is_active,
                "has_webhook_secret": bool(r.webhook_secret)
            }
            for r in repos
        ]
    }


@router.get("/{repo_id}")
async def get_business_account(repo_id: int, db: Session = Depends(get_db)):
    """Get business account details"""
    from app.modules.business_accounts.models import Repository
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    return {
        "id": repo.id,
        "github_repo_id": repo.github_repo_id,
        "full_name": repo.full_name,
        "owner": repo.owner,
        "name": repo.name,
        "description": repo.description,
        "is_active": repo.is_active,
        "has_webhook_secret": bool(repo.webhook_secret),
        "created_at": repo.created_at.isoformat() if repo.created_at else None
    }


@router.patch("/{repo_id}/webhook-secret")
async def update_webhook_secret(
    repo_id: int,
    request: UpdateWebhookSecretRequest,
    db: Session = Depends(get_db)
):
    """Update webhook secret for a business account"""
    service = RepositoryService(db)
    
    try:
        repo = service.update_webhook_secret(repo_id, request.webhook_secret)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return {
        "id": repo.id,
        "full_name": repo.full_name,
        "message": "Webhook secret updated"
    }


@router.delete("/{repo_id}")
async def deactivate_business_account(repo_id: int, db: Session = Depends(get_db)):
    """Deactivate a business account (soft delete)"""
    from app.modules.business_accounts.models import Repository
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Business account not found")
    
    repo.is_active = False
    db.commit()
    
    return {
        "id": repo.id,
        "full_name": repo.full_name,
        "message": "Business account deactivated"
    }
