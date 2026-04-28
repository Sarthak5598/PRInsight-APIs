"""
Webhook API Route.
Receives GitHub webhook events and processes them.
Verifies signatures using per-repo webhook secrets.
"""

import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import get_settings
from app.modules.business_accounts.models import Repository
from app.modules.pr_comments.webhook_handler import WebhookHandler

router = APIRouter(prefix="/webhook", tags=["webhook"])


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not secret:
        return True  # Skip verification if no secret configured
    
    if not signature:
        return False
    
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


def get_repo_id_from_payload(payload: dict) -> int | None:
    """Extract github_repo_id from webhook payload"""
    repo = payload.get("repository")
    if repo:
        return repo.get("id")
    return None


@router.post("/github")
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256")
):
    """
    Main GitHub webhook endpoint.
    Handles: pull_request, issue_comment, pull_request_review_comment
    
    Signature verification:
    1. First checks per-repo webhook secret (from business account)
    2. Falls back to global GITHUB_WEBHOOK_SECRET if repo not registered
    """
    settings = get_settings()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Parse payload first to get repo info
    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Get event type
    event_type = x_github_event
    if not event_type:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
    
    # Determine which secret to use for verification
    github_repo_id = get_repo_id_from_payload(payload)
    webhook_secret = None
    
    if github_repo_id:
        # Look up repo's webhook secret
        repo = db.query(Repository).filter(
            Repository.github_repo_id == github_repo_id
        ).first()
        
        if repo and repo.webhook_secret:
            webhook_secret = repo.webhook_secret
    
    # Fall back to global secret if no per-repo secret
    if not webhook_secret:
        webhook_secret = settings.GITHUB_WEBHOOK_SECRET
    
    # Verify signature
    if webhook_secret:
        if not verify_signature(body, x_hub_signature_256, webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    handler = WebhookHandler(db)
    result = handler.handle_event(event_type, payload)
    
    return result


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint"""
    return {"status": "ok", "endpoint": "webhook"}
