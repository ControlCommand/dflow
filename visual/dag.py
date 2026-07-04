"""
DAG Builder for DFlow - Build directed acyclic graphs from Catalog lineage data.
RFC-0007: DAG System
"""

from core.catalog import get_all_dos, validate_lineage_integrity, detect_lineage_cycles


def build_dag():
    """
    Build a DAG from all Data Objects in the Catalog.

    Returns a dictionary where:
    - keys are DO IDs
    - values are lists of parent IDs (lineage)

    Raises ValueError if lineage integrity validation fails.
    """
    # Validate lineage integrity first
    is_valid, errors = validate_lineage_integrity()
    if not is_valid:
        raise ValueError(f"Lineage integrity validation failed: {errors}")

    # Check for cycles
    has_cycles, cycles = detect_lineage_cycles()
    if has_cycles:
        raise ValueError(f"Cycle detected in lineage: {cycles}")

    all_dos = get_all_dos()

    graph = {}
    for do_data in all_dos:
        do_id = do_data["id"]
        lineage = do_data["lineage"]
        graph[do_id] = lineage

    return graph


def get_children(do_id, dag=None):
    """Get all direct children of a given DO."""
    if dag is None:
        dag = build_dag()

    children = []
    for node_id, parents in dag.items():
        if do_id in parents:
            children.append(node_id)

    return children


def get_ancestors(do_id, dag=None, visited=None):
    """Get all ancestors (parents, grandparents, etc.) of a DO."""
    if dag is None:
        dag = build_dag()

    if visited is None:
        visited = set()

    if do_id in visited:
        return []

    visited.add(do_id)

    parents = dag.get(do_id, [])
    ancestors = list(parents)

    for parent in parents:
        ancestors.extend(get_ancestors(parent, dag, visited))

    return list(set(ancestors))


def get_descendants(do_id, dag=None, visited=None):
    """Get all descendants (children, grandchildren, etc.) of a DO."""
    if dag is None:
        dag = build_dag()

    if visited is None:
        visited = set()

    if do_id in visited:
        return []

    visited.add(do_id)

    children = get_children(do_id, dag)
    descendants = list(children)

    for child in children:
        descendants.extend(get_descendants(child, dag, visited))

    return list(set(descendants))


def find_roots(dag=None):
    """Find root nodes (DOs with no parents/lineage)."""
    if dag is None:
        dag = build_dag()

    roots = []
    for node_id, parents in dag.items():
        if not parents:
            roots.append(node_id)

    return roots


def find_leaves(dag=None):
    """Find leaf nodes (DOs with no children)."""
    if dag is None:
        dag = build_dag()

    # All nodes that are parents of other nodes
    has_children = set()
    for parents in dag.values():
        has_children.update(parents)

    leaves = []
    for node_id in dag.keys():
        if node_id not in has_children:
            leaves.append(node_id)

    return leaves


def get_siblings(do_id, dag=None):
    """Get all siblings (DOs with same parents) of a given DO."""
    if dag is None:
        dag = build_dag()

    if do_id not in dag:
        return []

    my_parents = set(dag[do_id])
    siblings = []

    for node_id, parents in dag.items():
        if node_id != do_id and set(parents) == my_parents:
            siblings.append(node_id)

    return siblings


def get_transformation_history(do_id, dag=None):
    """
    Get the complete transformation history for a DO.
    Returns list of (do_id, state, parent_ids) tuples from root to current.
    """
    if dag is None:
        dag = build_dag()

    from core.catalog import get_do

    history = []
    current_id = do_id
    visited = set()

    while current_id and current_id not in visited:
        visited.add(current_id)
        do_data = get_do(current_id)
        if do_data:
            history.append({
                "id": current_id,
                "state": do_data["state"],
                "parents": dag.get(current_id, [])
            })

        parents = dag.get(current_id, [])
        current_id = parents[0] if parents else None

    # Reverse to get root-to-leaf order
    history.reverse()
    return history


def validate_graph_integrity(dag=None):
    """
    Comprehensive graph integrity validation.
    Returns (is_valid, list_of_errors).
    """
    if dag is None:
        dag = build_dag()

    errors = []
    all_ids = set(dag.keys())

    # Check 1: No duplicate IDs (already guaranteed by dict)

    # Check 2: No duplicate edges
    edges_seen = set()
    for node_id, parents in dag.items():
        for parent in parents:
            edge = (parent, node_id)
            if edge in edges_seen:
                errors.append(f"Duplicate edge: {parent[:8]}... -> {node_id[:8]}...")
            edges_seen.add(edge)

    # Check 3: All parent references exist
    for node_id, parents in dag.items():
        for parent in parents:
            if parent not in all_ids:
                errors.append(f"Missing parent: {node_id[:8]}... references non-existent {parent[:8]}...")

    # Check 4: No cycles (already checked in build_dag, but verify again)
    from core.catalog import detect_lineage_cycles
    has_cycles, cycles = detect_lineage_cycles()
    if has_cycles:
        for cycle in cycles:
            cycle_str = " -> ".join([cid[:8] for cid in cycle])
            errors.append(f"Cycle detected: {cycle_str}")

    return (len(errors) == 0, errors)


def to_dot_format(dag=None):
    """
    Convert DAG to DOT format for visualization tools like Graphviz.

    Returns a string in DOT format with state-based node coloring.
    """
    if dag is None:
        dag = build_dag()

    from core.catalog import get_do

    # State color mapping
    state_colors = {
        "INGRESS": "#FFE4B5",      # Light orange
        "VALIDATED": "#98FB98",    # Pale green
        "ACTIVE": "#87CEEB",       # Light blue
        "SCRATCH": "#DDA0DD",      # Plum
        "CURATED": "#FFD700",      # Gold
        "ARCHIVED": "#D3D3D3",     # Light gray
        "REJECTED": "#FF6B6B"      # Light red
    }

    lines = ["digraph DFlow {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box, style=filled];")
    lines.append("")

    # Add nodes with state information
    for node_id, parents in dag.items():
        short_id = node_id[:8]
        do_data = get_do(node_id)
        state = do_data["state"] if do_data else "UNKNOWN"
        color = state_colors.get(state, "#FFFFFF")

        label = f"{short_id}\\n{state}"
        lines.append(f'  "{short_id}" [label="{label}", fillcolor="{color}"];')

        # Add edges
        for parent in parents:
            short_parent = parent[:8]
            lines.append(f'  "{short_parent}" -> "{short_id}";')

    lines.append("}")

    return "\n".join(lines)