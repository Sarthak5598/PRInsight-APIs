"""
PR Insights Service - Analytics and Metrics.
Your differentiation layer - this is where the value is.

Responsibilities:
- Aggregate metrics (comments per user, PR turnaround time)
- Cross-repo analytics (top reviewers overall)
- Computed insights from raw data

AI integration comes later (Step 2).
"""

from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.modules.user_accounts.models import User
from app.modules.business_accounts.models import Repository
from app.modules.pr_comments.models import PullRequest, Comment


class InsightsService:
    """
    Service for computing PR insights and metrics.
    All metrics computed via SQL - no AI dependency.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== User Metrics ====================
    
    def get_top_commenters(self, repo_id: int = None, limit: int = 10) -> list[dict]:
        """
        Get users who comment the most.
        Optionally filtered by repo.
        """
        query = (
            self.db.query(
                User.id,
                User.username,
                User.avatar_url,
                func.count(Comment.id).label("comment_count")
            )
            .join(Comment, Comment.user_id == User.id)
        )
        
        if repo_id:
            query = query.join(PullRequest, Comment.pr_id == PullRequest.id)
            query = query.filter(PullRequest.repo_id == repo_id)
        
        results = (
            query
            .group_by(User.id, User.username, User.avatar_url)
            .order_by(desc("comment_count"))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "user_id": r.id,
                "username": r.username,
                "avatar_url": r.avatar_url,
                "comment_count": r.comment_count
            }
            for r in results
        ]
    
    def get_top_pr_authors(self, repo_id: int = None, limit: int = 10) -> list[dict]:
        """Get users who author the most PRs"""
        query = (
            self.db.query(
                User.id,
                User.username,
                User.avatar_url,
                func.count(PullRequest.id).label("pr_count")
            )
            .join(PullRequest, PullRequest.author_id == User.id)
        )
        
        if repo_id:
            query = query.filter(PullRequest.repo_id == repo_id)
        
        results = (
            query
            .group_by(User.id, User.username, User.avatar_url)
            .order_by(desc("pr_count"))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "user_id": r.id,
                "username": r.username,
                "avatar_url": r.avatar_url,
                "pr_count": r.pr_count
            }
            for r in results
        ]
    
    def get_user_activity_summary(self, user_id: int) -> dict:
        """Get comprehensive activity summary for a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Count PRs authored
        pr_count = self.db.query(func.count(PullRequest.id)).filter(
            PullRequest.author_id == user_id
        ).scalar()
        
        # Count comments made
        comment_count = self.db.query(func.count(Comment.id)).filter(
            Comment.user_id == user_id
        ).scalar()
        
        # Repos contributed to
        repos_contributed = (
            self.db.query(func.count(func.distinct(PullRequest.repo_id)))
            .filter(PullRequest.author_id == user_id)
            .scalar()
        )
        
        # PRs reviewed (commented on but not authored)
        prs_reviewed = (
            self.db.query(func.count(func.distinct(Comment.pr_id)))
            .join(PullRequest, Comment.pr_id == PullRequest.id)
            .filter(Comment.user_id == user_id)
            .filter(PullRequest.author_id != user_id)
            .scalar()
        )
        
        return {
            "user_id": user.id,
            "username": user.username,
            "avatar_url": user.avatar_url,
            "prs_authored": pr_count,
            "comments_made": comment_count,
            "repos_contributed_to": repos_contributed,
            "prs_reviewed": prs_reviewed
        }
    
    # ==================== Repository Metrics ====================
    
    def get_repo_summary(self, repo_id: int) -> dict:
        """Get summary metrics for a repository"""
        repo = self.db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return None
        
        # Total PRs
        total_prs = self.db.query(func.count(PullRequest.id)).filter(
            PullRequest.repo_id == repo_id
        ).scalar()
        
        # Open PRs
        open_prs = self.db.query(func.count(PullRequest.id)).filter(
            PullRequest.repo_id == repo_id,
            PullRequest.state == "open"
        ).scalar()
        
        # Merged PRs
        merged_prs = self.db.query(func.count(PullRequest.id)).filter(
            PullRequest.repo_id == repo_id,
            PullRequest.state == "merged"
        ).scalar()
        
        # Total comments
        total_comments = (
            self.db.query(func.count(Comment.id))
            .join(PullRequest, Comment.pr_id == PullRequest.id)
            .filter(PullRequest.repo_id == repo_id)
            .scalar()
        )
        
        # Unique contributors
        unique_contributors = (
            self.db.query(func.count(func.distinct(PullRequest.author_id)))
            .filter(PullRequest.repo_id == repo_id)
            .scalar()
        )
        
        return {
            "repo_id": repo.id,
            "full_name": repo.full_name,
            "total_prs": total_prs,
            "open_prs": open_prs,
            "merged_prs": merged_prs,
            "total_comments": total_comments,
            "unique_contributors": unique_contributors
        }
    
    # ==================== PR-Level Metrics ====================
    
    def get_pr_insights(self, pr_id: int) -> dict:
        """Get detailed insights for a specific PR"""
        pr = self.db.query(PullRequest).filter(PullRequest.id == pr_id).first()
        if not pr:
            return None
        
        # Get comments
        comments = self.db.query(Comment).filter(Comment.pr_id == pr_id).all()
        
        # Unique commenters (excluding author)
        unique_commenters = len(set(
            c.user_id for c in comments if c.user_id != pr.author_id
        ))
        
        # Calculate turnaround time if merged
        turnaround_hours = None
        if pr.merged_at and pr.gh_created_at:
            delta = pr.merged_at - pr.gh_created_at
            turnaround_hours = delta.total_seconds() / 3600
        
        # Time to first review (first comment from non-author)
        first_review_hours = None
        non_author_comments = [c for c in comments if c.user_id != pr.author_id]
        if non_author_comments and pr.gh_created_at:
            first_comment = min(non_author_comments, key=lambda c: c.gh_created_at)
            delta = first_comment.gh_created_at - pr.gh_created_at
            first_review_hours = delta.total_seconds() / 3600
        
        return {
            "pr_id": pr.id,
            "pr_number": pr.github_pr_number,
            "title": pr.title,
            "state": pr.state,
            "comment_count": len(comments),
            "unique_reviewers": unique_commenters,
            "turnaround_hours": round(turnaround_hours, 2) if turnaround_hours else None,
            "time_to_first_review_hours": round(first_review_hours, 2) if first_review_hours else None
        }
    
    def get_most_discussed_prs(self, repo_id: int = None, limit: int = 10) -> list[dict]:
        """Get PRs with the most comments"""
        query = (
            self.db.query(
                PullRequest.id,
                PullRequest.github_pr_number,
                PullRequest.title,
                PullRequest.state,
                func.count(Comment.id).label("comment_count")
            )
            .join(Comment, Comment.pr_id == PullRequest.id)
        )
        
        if repo_id:
            query = query.filter(PullRequest.repo_id == repo_id)
        
        results = (
            query
            .group_by(PullRequest.id, PullRequest.github_pr_number, 
                     PullRequest.title, PullRequest.state)
            .order_by(desc("comment_count"))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "pr_id": r.id,
                "pr_number": r.github_pr_number,
                "title": r.title,
                "state": r.state,
                "comment_count": r.comment_count
            }
            for r in results
        ]
    
    # ==================== Cross-Repo Analytics ====================
    
    def get_global_top_reviewers(self, limit: int = 10) -> list[dict]:
        """
        Get top reviewers across ALL repos.
        This is where global user identity pays off!
        """
        results = (
            self.db.query(
                User.id,
                User.username,
                User.avatar_url,
                func.count(func.distinct(Comment.pr_id)).label("prs_reviewed"),
                func.count(Comment.id).label("total_comments")
            )
            .join(Comment, Comment.user_id == User.id)
            .join(PullRequest, Comment.pr_id == PullRequest.id)
            .filter(PullRequest.author_id != User.id)  # Exclude self-comments
            .group_by(User.id, User.username, User.avatar_url)
            .order_by(desc("prs_reviewed"))
            .limit(limit)
            .all()
        )
        
        return [
            {
                "user_id": r.id,
                "username": r.username,
                "avatar_url": r.avatar_url,
                "prs_reviewed": r.prs_reviewed,
                "total_comments": r.total_comments
            }
            for r in results
        ]
    
    def get_reviewer_consistency(self, user_id: int) -> dict:
        """
        Measure how consistently a user reviews across repos.
        Great metric for identifying reliable reviewers.
        """
        # Get all repos where user has reviewed
        repos_reviewed = (
            self.db.query(
                Repository.id,
                Repository.full_name,
                func.count(Comment.id).label("comments")
            )
            .join(PullRequest, PullRequest.repo_id == Repository.id)
            .join(Comment, Comment.pr_id == PullRequest.id)
            .filter(Comment.user_id == user_id)
            .filter(PullRequest.author_id != user_id)
            .group_by(Repository.id, Repository.full_name)
            .all()
        )
        
        return {
            "user_id": user_id,
            "repos_reviewed_count": len(repos_reviewed),
            "repos": [
                {"repo_id": r.id, "full_name": r.full_name, "comments": r.comments}
                for r in repos_reviewed
            ]
        }
