import json
from sqlalchemy.orm import Session
from app.models.telemetry import ProductEvent, ProductFeedback
from app.core.config import settings

# Explicit allowlist of events to prevent garbage telemetry.
ALLOWED_EVENTS = {
    "ACCOUNT_CREATED",
    "ONBOARDING_COMPLETED",
    "GITHUB_CONNECTED",
    "PROJECT_CREATED",
    "FIRST_SYNC_COMPLETED",
    "SYNC_STARTED",
    "SYNC_COMPLETED",
    "SYNC_FAILED",
    "ATLAS_VIEWED",
    "SIGNAL_SELECTED",
    "FOLLOW_PROOF_OPENED",
    "PROOF_VIEWED",
    "NEXT_EXPEDITION_OPENED",
    "QUEST_STARTED",
    "QUEST_MARKED_COMPLETE",
    "QUEST_VERIFIED",
    "PROJECT_INTELLIGENCE_VIEWED",
    "LAB_OPENED",
    "LAB_ACTIVITY_COMPLETED",
    "COPILOT_STARTED",
    "DEFEND_BUILD_STARTED",
    "DEFEND_BUILD_COMPLETED",
    "AI_FAILURE",
    "NEXUS_ID_CREATED",
    "PUBLIC_PROFILE_ENABLED",
    "REVIEW_LINK_CREATED",
    "MENTOR_INVITED",
    "MENTOR_ACCEPTED",
}

def record_event(db: Session, event_type: str, user_id: int = None, context: dict = None):
    """
    Records a safe product event. Should be called as a BackgroundTask
    where latency is sensitive, or synchronously where strict transaction
    consistency is required (e.g. QUEST_VERIFIED).
    """
    if event_type not in ALLOWED_EVENTS:
        # Silently drop unallowlisted events or log a safe warning.
        return None

    # Sanitize context data to strictly prevent secrets/source code leaking
    safe_context = _sanitize_context(context)

    event = ProductEvent(
        user_id=user_id,
        event_type=event_type,
        context_data=safe_context
    )
    db.add(event)
    try:
        db.commit()
    except Exception as e:
        # Swallow DB failures so telemetry doesn't bring down core features.
        db.rollback()
        print(f"[TELEMETRY ERROR] Could not record {event_type}: {e}")

def record_feedback(db: Session, user_id: int, feature_context: str, is_helpful: bool, reason: str = None):
    """
    Records contextual feedback.
    """
    ALLOWED_REASONS = {
        "EVIDENCE_UNCLEAR", "RECOMMENDATION_UNCLEAR", "NEXT_STEP_UNCLEAR",
        "INTERFACE_CONFUSING", "INFORMATION_INACCURATE", "OTHER"
    }

    if reason and reason not in ALLOWED_REASONS:
        reason = "OTHER"

    feedback = ProductFeedback(
        user_id=user_id,
        feature_context=feature_context,
        is_helpful=is_helpful,
        reason=reason
    )
    db.add(feedback)
    db.commit()
    return feedback

def _sanitize_context(context: dict) -> dict:
    if not context:
        return {}
    
    # Strip any dangerous keys
    dangerous_keys = {"password", "token", "secret", "api_key", "source_code", "raw_prompt", "email"}
    safe = {}
    for k, v in context.items():
        if any(d in k.lower() for d in dangerous_keys):
            continue
        # Truncate overly long values
        if isinstance(v, str) and len(v) > 255:
            safe[k] = v[:252] + "..."
        else:
            safe[k] = v
    return safe

def get_product_health(db: Session) -> dict:
    """
    Aggregates product health metrics safely for internal dashboards.
    """
    total_users = db.query(ProductEvent).filter(ProductEvent.event_type == "ACCOUNT_CREATED").count()
    successful_syncs = db.query(ProductEvent).filter(ProductEvent.event_type == "SYNC_COMPLETED").count()
    failed_syncs = db.query(ProductEvent).filter(ProductEvent.event_type == "SYNC_FAILED").count()
    quest_verified = db.query(ProductEvent).filter(ProductEvent.event_type == "QUEST_VERIFIED").count()
    ai_failures = db.query(ProductEvent).filter(ProductEvent.event_type == "AI_FAILURE").count()

    return {
        "active_users": total_users,
        "successful_syncs": successful_syncs,
        "failed_syncs": failed_syncs,
        "quest_verification_events": quest_verified,
        "ai_failure_events": ai_failures
    }
