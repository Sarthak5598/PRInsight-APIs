from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.pr_comments.models import PullRequest, Comment


class PRCommentService:
    """
    Service for managing Pull Requests and Comments.
    Core ingestion layer - keeps operations simple and reliable.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Pull Request Operations ====================
    
    def upsert_pull_request(
        self,
        github_pr_id: int,
        github_pr_number: int,
        repo_id: int,
        author_id: int,
        title: str,
        body: str = None,
        state: str = "open",
        gh_created_at: datetime = None,
        gh_updated_at: datetime = None,
        merged_at: datetime = None,
        closed_at: datetime = None,
        raw_payload: dict = None
    ) -> PullRequest:
        """
        Create or update a Pull Request.
        Idempotent - safe for webhook retries.
        """
        pr = self.db.query(PullRequest).filter(
            PullRequest.github_pr_id == github_pr_id
        ).first()
        
        if pr:
            # Update existing PR
            pr.title = title
            pr.body = body
            pr.state = state
            pr.gh_updated_at = gh_updated_at
            pr.merged_at = merged_at
            pr.closed_at = closed_at
            if raw_payload:
                pr.raw_payload = raw_payload
        else:
            # Create new PR
            pr = PullRequest(
                github_pr_id=github_pr_id,
                github_pr_number=github_pr_number,
                repo_id=repo_id,
                author_id=author_id,
                title=title,
                body=body,
                state=state,
                gh_created_at=gh_created_at or datetime.utcnow(),
                gh_updated_at=gh_updated_at,
                merged_at=merged_at,
                closed_at=closed_at,
                raw_payload=raw_payload
            )
            self.db.add(pr)
        
        self.db.commit()
        self.db.refresh(pr)
        return pr
    
    def get_pr_by_github_id(self, github_pr_id: int) -> PullRequest | None:
        """Get PR by GitHub PR ID"""
        return self.db.query(PullRequest).filter(
            PullRequest.github_pr_id == github_pr_id
        ).first()
    
    def get_prs_by_repo(self, repo_id: int, skip: int = 0, limit: int = 100) -> list[PullRequest]:
        """Get all PRs for a repository"""
        return self.db.query(PullRequest).filter(
            PullRequest.repo_id == repo_id
        ).offset(skip).limit(limit).all()
    
    def get_prs_by_author(self, author_id: int, skip: int = 0, limit: int = 100) -> list[PullRequest]:
        """Get all PRs by a specific author"""
        return self.db.query(PullRequest).filter(
            PullRequest.author_id == author_id
        ).offset(skip).limit(limit).all()
    
    # ==================== Comment Operations ====================
    
    def create_comment(
        self,
        github_comment_id: int,
        pr_id: int,
        user_id: int,
        body: str,
        comment_type: str = "issue_comment",
        gh_created_at: datetime = None,
        gh_updated_at: datetime = None,
        raw_payload: dict = None
    ) -> Comment | None:
        """
        Create a comment if it doesn't exist.
        Returns None if comment already exists (idempotent).
        """
        # Idempotency check - skip if already exists
        existing = self.db.query(Comment).filter(
            Comment.github_comment_id == github_comment_id
        ).first()
        
        if existing:
            return None  # Already processed
        
        comment = Comment(
            github_comment_id=github_comment_id,
            pr_id=pr_id,
            user_id=user_id,
            body=body,
            comment_type=comment_type,
            gh_created_at=gh_created_at or datetime.utcnow(),
            gh_updated_at=gh_updated_at,
            raw_payload=raw_payload
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment
    
    def update_comment(
        self,
        github_comment_id: int,
        body: str,
        gh_updated_at: datetime = None
    ) -> Comment | None:
        """Update an existing comment"""
        comment = self.db.query(Comment).filter(
            Comment.github_comment_id == github_comment_id
        ).first()
        
        if not comment:
            return None
        
        comment.body = body
        comment.gh_updated_at = gh_updated_at
        
        self.db.commit()
        self.db.refresh(comment)
        return comment
    
    def delete_comment(self, github_comment_id: int) -> bool:
        """Delete a comment (when deleted on GitHub)"""
        comment = self.db.query(Comment).filter(
            Comment.github_comment_id == github_comment_id
        ).first()
        
        if not comment:
            return False
        
        self.db.delete(comment)
        self.db.commit()
        return True
    
    def get_comments_by_pr(self, pr_id: int) -> list[Comment]:
        """Get all comments for a PR"""
        return self.db.query(Comment).filter(
            Comment.pr_id == pr_id
        ).order_by(Comment.gh_created_at).all()
    
    def get_comments_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Comment]:
        """Get all comments by a user"""
        return self.db.query(Comment).filter(
            Comment.user_id == user_id
        ).offset(skip).limit(limit).all()
