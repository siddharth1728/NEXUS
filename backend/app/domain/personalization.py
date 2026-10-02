"""Personalization Engine Domain Logic."""

from app.models.action import Action
from app.models.user import User


def score_action_relevance(action: Action, user: User) -> float:
    """Score how relevant an action is to a user based on their role and action properties.

    Returns:
        float: A score between 0.0 and 1.0.
    """
    score = 0.0

    # 1. Direct assignment
    if action.assignee_id == user.id:
        return 1.0

    # 2. Role-based scoring heuristics
    user_role = user.role.lower()
    action_title_desc = f"{action.title} {action.description}".lower()

    role_keywords = {
        "admin": ["admin", "system", "manage", "approve", "review", "configure"],
        "manager": ["approve", "review", "budget", "schedule", "plan", "report"],
        "engineer": ["code", "deploy", "build", "fix", "bug", "implement", "test"],
        "member": ["task", "update", "read", "participate"],
    }

    keywords = role_keywords.get(user_role, [])

    match_count = sum(1 for kw in keywords if kw in action_title_desc)

    if match_count > 0:
        score += min(0.5 + (match_count * 0.1), 0.8)
    else:
        score += 0.1

    # 3. Priority boost
    if action.priority == "P0":
        score = min(score + 0.3, 1.0)
    elif action.priority == "P1":
        score = min(score + 0.2, 1.0)

    return round(min(max(score, 0.0), 1.0), 2)
