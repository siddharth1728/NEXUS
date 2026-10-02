"""Action Graph Domain Logic."""

import uuid
from collections import defaultdict
from collections.abc import Sequence

from app.core.errors import GraphCycleError
from app.models.action import ActionEdge
from app.models.enums import EdgeRelationType


def check_for_cycles(
    new_edge: ActionEdge,
    existing_edges: Sequence[ActionEdge],
) -> None:
    """Check if adding new_edge to existing_edges creates a cycle in DEPENDS_ON relations.

    Raises:
        GraphCycleError: If a cycle is detected or if self-referencing.
    """
    if new_edge.source_id == new_edge.target_id:
        raise GraphCycleError(
            cycle_path=[str(new_edge.source_id)], message="Self-referencing edges are not allowed."
        )

    # Only cycle-check DEPENDS_ON for now, as it's the strict DAG portion.
    # If other edge types imply DAG semantics, add them here.
    if new_edge.relation_type != EdgeRelationType.DEPENDS_ON:
        return

    # Build adjacency list: target -> source means 'source depends on target'
    # Actually wait: A -> depends_on -> B means A is the source and B is the target.
    # A path B -> ... -> A means B depends on A.
    # If we add A -> B, we must ensure B doesn't already depend on A (i.e. no path from B to A).
    graph: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)

    for edge in existing_edges:
        if edge.relation_type == EdgeRelationType.DEPENDS_ON:
            graph[edge.source_id].append(edge.target_id)

    # Temporarily add the new edge to check for cycles
    graph[new_edge.source_id].append(new_edge.target_id)

    # Perform DFS from the source node to find cycles
    visited: set[uuid.UUID] = set()
    recursion_stack: set[uuid.UUID] = set()

    def dfs(node: uuid.UUID) -> bool:
        visited.add(node)
        recursion_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in recursion_stack:
                return True

        recursion_stack.remove(node)
        return False

    # Since we only added one edge, any new cycle must involve new_edge.source_id
    if dfs(new_edge.source_id):
        raise GraphCycleError(
            cycle_path=[],  # Would reconstruct actual path in a real implementation
            message=f"Adding edge from {new_edge.source_id} to {new_edge.target_id} creates a cycle.",
        )


def resolve_cycles(
    new_edge: ActionEdge,
    existing_edges: Sequence[ActionEdge],
    actions_map: dict[uuid.UUID, "Action"],
) -> bool:
    """Check for cycles and if one is found, flag the involved actions as CONFLICT.

    Returns True if a cycle was found and flagged, False otherwise.
    """
    from app.models.enums import ConfidenceLevel

    try:
        check_for_cycles(new_edge, existing_edges)
        return False
    except GraphCycleError:
        # Flag as CONFLICT
        if new_edge.source_id in actions_map:
            actions_map[new_edge.source_id].confidence = ConfidenceLevel.CONFLICT
        if new_edge.target_id in actions_map:
            actions_map[new_edge.target_id].confidence = ConfidenceLevel.CONFLICT
        return True
