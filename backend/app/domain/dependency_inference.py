"""Dependency Edge Inference Engine."""

import re
import uuid
from collections.abc import Sequence

from app.models.action import Action, ActionEdge
from app.models.enums import EdgeRelationType


def infer_dependencies(actions: Sequence[Action], tenant_id: uuid.UUID) -> list[ActionEdge]:
    """Infer DEPENDS_ON or BLOCKS edges between actions based on textual cues."""
    edges = []

    # Very basic heuristic for Phase 03:
    # If Action B's description says "depends on [Action A title]" or "requires [Action A title]"

    for target_action in actions:
        desc = target_action.description.lower()
        for source_action in actions:
            if source_action.id == target_action.id:
                continue

            source_title = source_action.title.lower()

            # Simple keyword matching
            requires_pattern = (
                rf"(requires|depends on|blocked by|after)\s+['\"]?{re.escape(source_title)}['\"]?"
            )

            if re.search(requires_pattern, desc):
                edges.append(
                    ActionEdge(
                        tenant_id=tenant_id,
                        source_id=source_action.id,
                        target_id=target_action.id,
                        relation_type=EdgeRelationType.DEPENDS_ON,
                        metadata_payload={"inferred": True, "method": "keyword_match"},
                    )
                )

    return edges
