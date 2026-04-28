"""
Webhook Handler for GitHub Events.
Core ingestion layer - keeps processing simple and reliable.

Responsibilities:
- Parse webhook payloads
- Handle events: pull_request, issue_comment, pull_request_review_comment
- Write to DB via services

NO AI processing here - that happens in pr_insights module.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.user_accounts.service import UserService
from app.modules.business_accounts.service import RepositoryService
from app.modules.pr_comments.service import PRCommentService


class WebhookHandler:
    """
    Handles incoming GitHub webhook events.
    All operations are idempotent - safe for retries.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.repo_service = RepositoryService(db)
        self.pr_service = PRCommentService(db)
    
    def handle_event(self, event_type: str, payload: dict) -> dict:
        """
        Main entry point for webhook handling.
        Routes to appropriate handler based on event type.
        """
        handlers = {
            "pull_request": self._handle_pull_request,
            "issue_comment": self._handle_issue_comment,
            "pull_request_review_comment": self._handle_review_comment,
        }
        
        handler = handlers.get(event_type)
        if not handler:
            return {"status": "ignored", "message": f"Event type '{event_type}' not handled"}
        
        return handler(payload)
    
    def _handle_pull_request(self, payload: dict) -> dict:
        """Handle pull_request events (opened, closed, merged, etc.)"""
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        
        # Upsert repository
        repo = self.repo_service.upsert_repository(
            github_repo_id=repo_data["id"],
            name=repo_data["name"],
            owner=repo_data["owner"]["login"],
            description=repo_data.get("description")
        )
        
        # Upsert author
        author_data = pr_data.get("user", {})
        author = self.user_service.upsert_user(
            github_id=author_data["id"],
            username=author_data["login"],
            avatar_url=author_data.get("avatar_url")
        )
        
        # Determine state
        state = pr_data.get("state", "open")
        if pr_data.get("merged"):
            state = "merged"
        
        # Parse timestamps
        gh_created_at = self._parse_timestamp(pr_data.get("created_at"))
        gh_updated_at = self._parse_timestamp(pr_data.get("updated_at"))
        merged_at = self._parse_timestamp(pr_data.get("merged_at"))
        closed_at = self._parse_timestamp(pr_data.get("closed_at"))
        
        # Upsert PR
        pr = self.pr_service.upsert_pull_request(
            github_pr_id=pr_data["id"],
            github_pr_number=pr_data["number"],
            repo_id=repo.id,
            author_id=author.id,
            title=pr_data["title"],
            body=pr_data.get("body"),
            state=state,
            gh_created_at=gh_created_at,
            gh_updated_at=gh_updated_at,
            merged_at=merged_at,
            closed_at=closed_at,
            raw_payload=payload  # Store raw for debugging
        )
        
        return {
            "status": "processed",
            "event": "pull_request",
            "action": action,
            "pr_id": pr.id,
            "pr_number": pr.github_pr_number
        }
    
    def _handle_issue_comment(self, payload: dict) -> dict:
        """Handle issue_comment events (created, edited, deleted)"""
        action = payload.get("action")
        comment_data = payload.get("comment", {})
        issue_data = payload.get("issue", {})
        repo_data = payload.get("repository", {})
        
        # Only process comments on PRs (issues with pull_request key)
        if "pull_request" not in issue_data:
            return {"status": "ignored", "message": "Comment not on a PR"}
        
        # Upsert repository
        repo = self.repo_service.upsert_repository(
            github_repo_id=repo_data["id"],
            name=repo_data["name"],
            owner=repo_data["owner"]["login"]
        )
        
        # Get or create PR (we need the PR to exist)
        pr = self.pr_service.get_pr_by_github_id(issue_data["id"])
        if not pr:
            # PR doesn't exist yet - we need to fetch it
            # For now, create a minimal PR record
            pr_author_data = issue_data.get("user", {})
            pr_author = self.user_service.upsert_user(
                github_id=pr_author_data["id"],
                username=pr_author_data["login"],
                avatar_url=pr_author_data.get("avatar_url")
            )
            
            pr = self.pr_service.upsert_pull_request(
                github_pr_id=issue_data["id"],
                github_pr_number=issue_data["number"],
                repo_id=repo.id,
                author_id=pr_author.id,
                title=issue_data["title"],
                body=issue_data.get("body"),
                state=issue_data.get("state", "open"),
                gh_created_at=self._parse_timestamp(issue_data.get("created_at"))
            )
        
        # Upsert comment author
        commenter_data = comment_data.get("user", {})
        commenter = self.user_service.upsert_user(
            github_id=commenter_data["id"],
            username=commenter_data["login"],
            avatar_url=commenter_data.get("avatar_url")
        )
        
        # Handle based on action
        if action == "created":
            comment = self.pr_service.create_comment(
                github_comment_id=comment_data["id"],
                pr_id=pr.id,
                user_id=commenter.id,
                body=comment_data["body"],
                comment_type="issue_comment",
                gh_created_at=self._parse_timestamp(comment_data.get("created_at")),
                raw_payload=payload
            )
            return {
                "status": "processed" if comment else "skipped",
                "event": "issue_comment",
                "action": action,
                "comment_id": comment.id if comment else None
            }
        
        elif action == "edited":
            comment = self.pr_service.update_comment(
                github_comment_id=comment_data["id"],
                body=comment_data["body"],
                gh_updated_at=self._parse_timestamp(comment_data.get("updated_at"))
            )
            return {
                "status": "processed" if comment else "not_found",
                "event": "issue_comment",
                "action": action
            }
        
        elif action == "deleted":
            deleted = self.pr_service.delete_comment(comment_data["id"])
            return {
                "status": "processed" if deleted else "not_found",
                "event": "issue_comment",
                "action": action
            }
        
        return {"status": "ignored", "action": action}
    
    def _handle_review_comment(self, payload: dict) -> dict:
        """Handle pull_request_review_comment events"""
        action = payload.get("action")
        comment_data = payload.get("comment", {})
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        
        # Upsert repository
        repo = self.repo_service.upsert_repository(
            github_repo_id=repo_data["id"],
            name=repo_data["name"],
            owner=repo_data["owner"]["login"]
        )
        
        # Upsert PR author
        pr_author_data = pr_data.get("user", {})
        pr_author = self.user_service.upsert_user(
            github_id=pr_author_data["id"],
            username=pr_author_data["login"],
            avatar_url=pr_author_data.get("avatar_url")
        )
        
        # Upsert PR
        pr = self.pr_service.upsert_pull_request(
            github_pr_id=pr_data["id"],
            github_pr_number=pr_data["number"],
            repo_id=repo.id,
            author_id=pr_author.id,
            title=pr_data["title"],
            body=pr_data.get("body"),
            state=pr_data.get("state", "open"),
            gh_created_at=self._parse_timestamp(pr_data.get("created_at"))
        )
        
        # Upsert comment author
        commenter_data = comment_data.get("user", {})
        commenter = self.user_service.upsert_user(
            github_id=commenter_data["id"],
            username=commenter_data["login"],
            avatar_url=commenter_data.get("avatar_url")
        )
        
        # Handle based on action
        if action == "created":
            comment = self.pr_service.create_comment(
                github_comment_id=comment_data["id"],
                pr_id=pr.id,
                user_id=commenter.id,
                body=comment_data["body"],
                comment_type="review_comment",
                gh_created_at=self._parse_timestamp(comment_data.get("created_at")),
                raw_payload=payload
            )
            return {
                "status": "processed" if comment else "skipped",
                "event": "pull_request_review_comment",
                "action": action,
                "comment_id": comment.id if comment else None
            }
        
        elif action == "edited":
            comment = self.pr_service.update_comment(
                github_comment_id=comment_data["id"],
                body=comment_data["body"],
                gh_updated_at=self._parse_timestamp(comment_data.get("updated_at"))
            )
            return {
                "status": "processed" if comment else "not_found",
                "event": "pull_request_review_comment",
                "action": action
            }
        
        elif action == "deleted":
            deleted = self.pr_service.delete_comment(comment_data["id"])
            return {
                "status": "processed" if deleted else "not_found",
                "event": "pull_request_review_comment",
                "action": action
            }
        
        return {"status": "ignored", "action": action}
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse ISO 8601 timestamp from GitHub"""
        if not timestamp_str:
            return None
        try:
            # GitHub uses ISO 8601 format: 2023-01-01T12:00:00Z
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
