"""Conflict Resolution Module."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from app.models.action import Action
from app.models.enums import ConfidenceLevel


@dataclass
class ConflictReport:
    action_ids: list[uuid.UUID]
    description: str


def detect_contradictory_actions(actions: Sequence[Action]) -> list[ConflictReport]:
    """Flag contradictory claims or actions across documents.

    For Phase 03, we use a basic heuristic looking for opposing terms in similar action titles/descriptions.
    """
    reports = []

    for i, action_a in enumerate(actions):
        for action_b in actions[i + 1 :]:
            a_text = f"{action_a.title} {action_a.description}".lower()
            b_text = f"{action_b.title} {action_b.description}".lower()

            # Look for common entities (e.g. words longer than 5 chars that exist in both)
            a_words = set(w for w in a_text.split() if len(w) > 5)
            b_words = set(w for w in b_text.split() if len(w) > 5)

            common_words = a_words.intersection(b_words)

            if len(common_words) > 0:
                # Check for antonyms/contradictions
                contradictions = [
                    ("approve", "reject"),
                    ("allow", "deny"),
                    ("true", "false"),
                    ("include", "exclude"),
                ]

                for term1, term2 in contradictions:
                    if (term1 in a_text and term2 in b_text) or (
                        term2 in a_text and term1 in b_text
                    ):
                        reports.append(
                            ConflictReport(
                                action_ids=[action_a.id, action_b.id],
                                description=f"Contradictory terms '{term1}' and '{term2}' found concerning common subjects: {common_words}",
                            )
                        )

                        # Flag them as CONFLICT
                        action_a.confidence = ConfidenceLevel.CONFLICT
                        action_b.confidence = ConfidenceLevel.CONFLICT

                        break  # Only report once per pair

    return reports
