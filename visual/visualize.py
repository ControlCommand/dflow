"""
Visualizer for DFlow - Render DAGs and workflow visualizations.
RFC-0007: DAG System (Visualization Layer)
"""

from visual.dag import build_dag, to_dot_format, get_ancestors, get_descendants, find_roots, get_children
from core.catalog import get_do


def print_dag_ascii(dag=None):
    """Print a simple ASCII representation of the DAG (Level 1 visualization)."""
    if dag is None:
        try:
            dag = build_dag()
        except ValueError as e:
            print(f"[ERROR] Cannot build DAG: {e}")
            return

    if not dag:
        print("[INFO] No Data Objects to visualize")
        return

    print("=" * 60)
    print("DFLOW LINEAGE GRAPH")
    print("=" * 60)

    # Group by roots and their descendants
    roots = find_roots(dag)

    for root in roots:
        _print_tree(root, dag, 0, set())

    print("=" * 60)


def _print_tree(node_id, dag, depth, visited):
    """Recursively print tree structure with state information."""
    if node_id in visited:
        print("  " * depth + "└─ [CYCLE DETECTED]")
        return

    visited.add(node_id)
    short_id = node_id[:8]

    # Get DO info
    from core.catalog import get_do
    do_data = get_do(node_id)
    state = do_data["state"] if do_data else "UNKNOWN"

    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""

    print(f"{indent}{prefix}{short_id} [{state}]")

    # Get children
    children = get_children(node_id, dag)

    for i, child in enumerate(children):
        _print_tree(child, dag, depth + 1, visited.copy())


def save_dot_file(filename, dag=None):
    """Save DAG to a DOT file for Graphviz visualization."""
    dot_content = to_dot_format(dag)

    with open(filename, 'w') as f:
        f.write(dot_content)

    print(f"[INFO] DOT file saved to: {filename}")
    print(f"[INFO] To render: dot -Tpng {filename} -o {filename}.png")


def show_do_lineage(do_id):
    """Show full lineage for a specific Data Object."""
    from core.catalog import get_do
    from visual.dag import get_ancestors, get_descendants, get_siblings, get_transformation_history

    do_data = get_do(do_id)

    if do_data is None:
        print(f"[ERROR] Data Object not found: {do_id}")
        return

    print(f"\n{'=' * 60}")
    print(f"LINEAGE FOR: {do_id[:8]}...")
    print(f"{'=' * 60}")

    ancestors = get_ancestors(do_id)
    descendants = get_descendants(do_id)
    siblings = get_siblings(do_id)
    history = get_transformation_history(do_id)

    print(f"\nCurrent State: {do_data['state']}")
    print(f"Path: {do_data['path']}")
    print(f"Created: {do_data['created_at']}")
    print(f"Updated: {do_data['updated_at']}")

    print(f"\n--- Transformation History (Root to Current) ---")
    if history:
        for i, step in enumerate(history):
            marker = "→" if step["id"] == do_id else " "
            print(f"  {marker} Step {i+1}: {step['id'][:8]}... [{step['state']}]")
            if step["parents"]:
                print(f"      Parents: {[p[:8] for p in step['parents']]}")
    else:
        print("  (no history)")

    print(f"\n--- Ancestors ({len(ancestors)}) ---")
    if ancestors:
        for anc in ancestors:
            print(f"  ← {anc[:8]}")
    else:
        print("  (none - this is a root)")

    print(f"\n--- Descendants ({len(descendants)}) ---")
    if descendants:
        for desc in descendants:
            print(f"  → {desc[:8]}")
    else:
        print("  (none - this is a leaf)")

    print(f"\n--- Siblings ({len(siblings)}) ---")
    if siblings:
        for sib in siblings:
            print(f"  ↔ {sib[:8]}")
    else:
        print("  (none)")

    print(f"\nDirect Parents: {[p[:8] for p in do_data['lineage']]}")
    print(f"{'=' * 60}\n")