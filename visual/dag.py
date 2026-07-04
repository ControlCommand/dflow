"""
DAG Builder for DFlow - Build directed acyclic graphs from lineage data.
RFC-0007: DAG System
"""

from core.registry import get_all_dos


def build_dag():
    """
    Build a DAG from all Data Objects in the registry.
    
    Returns a dictionary where:
    - keys are DO IDs
    - values are lists of parent IDs (lineage)
    """
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


def to_dot_format(dag=None):
    """
    Convert DAG to DOT format for visualization tools like Graphviz.
    
    Returns a string in DOT format.
    """
    if dag is None:
        dag = build_dag()
    
    lines = ["digraph DFlow {"]
    lines.append("  rankdir=TB;")
    lines.append("  node [shape=box];")
    lines.append("")
    
    # Add nodes and edges
    for node_id, parents in dag.items():
        short_id = node_id[:8]
        lines.append(f'  "{short_id}" [label="{short_id}"];')
        
        for parent in parents:
            short_parent = parent[:8]
            lines.append(f'  "{short_parent}" -> "{short_id}";')
    
    lines.append("}")
    
    return "\n".join(lines)