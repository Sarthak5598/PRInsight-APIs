"""
AI Service for PR Insights.
This is a placeholder for Step 2 - add AI after core metrics work.

Future capabilities:
- Summarize PR discussions
- Classify comments (suggestion, nit, blocker)
- Sentiment analysis
- Review quality scoring
"""

from typing import Optional


class AIService:
    """
    AI-powered insights service.
    Start with placeholders, add real AI later.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.enabled = bool(api_key)
    
    async def summarize_pr_discussion(self, comments: list[dict]) -> Optional[dict]:
        """
        Summarize the discussion on a PR.
        
        Future implementation:
        - Send comments to LLM
        - Get summary, key points, decisions
        """
        if not self.enabled:
            return None
        
        # TODO: Implement with OpenAI/Claude
        # For now, return placeholder
        return {
            "summary": "AI summarization not yet implemented",
            "key_points": [],
            "decisions": []
        }
    
    async def classify_comment(self, comment_body: str) -> Optional[dict]:
        """
        Classify a comment type.
        
        Categories:
        - suggestion: "You could also..."
        - nit: "Minor: consider..."
        - blocker: "This will break..."
        - question: "Why did you..."
        - approval: "LGTM", "Looks good"
        """
        if not self.enabled:
            return None
        
        # TODO: Implement classification
        return {
            "category": "unknown",
            "confidence": 0.0
        }
    
    async def analyze_review_quality(self, user_comments: list[dict]) -> Optional[dict]:
        """
        Analyze the quality of a user's reviews.
        
        Metrics:
        - Constructiveness score
        - Specificity score
        - Actionability score
        """
        if not self.enabled:
            return None
        
        # TODO: Implement quality analysis
        return {
            "constructiveness": 0.0,
            "specificity": 0.0,
            "actionability": 0.0,
            "overall_score": 0.0
        }
    
    async def detect_review_patterns(self, user_id: int, comments: list[dict]) -> Optional[dict]:
        """
        Detect patterns in a user's reviewing style.
        
        Patterns:
        - Focuses on: security, performance, style, etc.
        - Common feedback themes
        - Review depth (surface vs deep)
        """
        if not self.enabled:
            return None
        
        # TODO: Implement pattern detection
        return {
            "focus_areas": [],
            "common_themes": [],
            "review_depth": "unknown"
        }
