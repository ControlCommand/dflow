"""
Visualizer for DFlow - Render DAGs and workflow visualizations.
RFC-0007: DAG System (Visualization Layer)
"""

from visual.dag import build_dag, to_dot_format, get_ancestors, get_descendants
from core.registry import get_do


def print_dag_ascii(dag=None):
    """Print a simple ASCII representation of the DAG."""
    if dag is None:
        dag = build_dag()
    
    if not dag:
        print("[INFO] No Data Objects to visualize")
        return
    
    print("=" * 60)
    print("DFLOW LINEAGE GRAPH")
    print("=" * 60)
    
    # Group by roots and their descendants
    roots = [node_id for node_id, parents in dag.items() if not parents]
    
    for root in roots:
        _print_tree(root, dag, 0, set())
    
    print("=" * 60)


def _print_tree(node_id, dag, depth, visited):
    """Recursively print tree structure."""
    if node_id in visited:
        return
    
    visited.add(node_id)
    short_id = node_id[:8]
    
    # Get DO info
    do_data = get_do(node_id)
    state = do_data["state"] if do_data else "UNKNOWN"
    
    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""
    
    print(f"{indent}{prefix}{short_id} [{state}]")
    
    # Get children
    children = []
    for child_id, parents in dag.items():
        if node_id in parents:
            children.append(child_id)
    
    for child in children:
        _print_tree(child, dag, depth + 1, visited)


def save_dot_file(filename, dag=None):
    """Save DAG to a DOT file for Graphviz visualization."""
    dot_content = to_dot_format(dag)
    
    with open(filename, 'w') as f:
        f.write(dot_content)
    
    print(f"[INFO] DOT file saved to: {filename}")
    print(f"[INFO] To render: dot -Tpng {filename} -o {filename}.png")


def show_do_lineage(do_id):
    """Show full lineage for a specific Data Object."""
    do_data = get_do(do_id)
    
    if do_data is None:
        print(f"[ERROR] Data Object not found: {do_id}")
        return
    
    print(f"\n{'=' * 60}")
    print(f"LINEAGE FOR: {do_id[:8]}...")
    print(f"{'=' * 60}")
    
    ancestors = get_ancestors(do_id)
    descendants = get_descendants(do_id)
    
    print(f"\nCurrent State: {do_data['state']}")
    print(f"Path: {do_data['path']}")
    
    print(f"\nAncestors ({len(ancestors)}):")
    if ancestors:
        for anc in ancestors:
            print(f"  ← {anc[:8]}")
    else:
        print("  (none - this is a root)")
    
    print(f"\nDescendants ({len(descendants)}):")
    if descendants:
        for desc in descendants:
            print(f"  → {desc[:8]}")
    else:
        print("  (none - this is a leaf)")
    
    print(f"\nDirect Parents: {do_data['lineage']}")
    print(f"{'=' * 60}\n")