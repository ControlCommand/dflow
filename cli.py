import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bootstrap import initialize
from core.workflow import ingest, run
from core.catalog import get_do, get_all_dos, validate_lineage_integrity, detect_lineage_cycles
from core.catalog_query import filter_by_state, filter_by_path, search_metadata, get_ancestors, get_descendants, get_siblings, full_text_search
from core.lifecycle import archive, reject as delete, get_allowed_next_states
from visual.visualize import print_dag_ascii, save_dot_file, show_do_lineage
from visual.dag import validate_graph_integrity


def main():
    initialize()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py ingest <file_path>           - Ingest a file into the system")
        print("  python cli.py run <do_id>                  - Run pipeline on a DO")
        print("  python cli.py status <do_id>               - Get status of a Data Object")
        print("  python cli.py list                         - List all Data Objects")
        print("  python cli.py lineage <do_id>              - Show full lineage for a DO")
        print("  python cli.py dag [--format ascii|dot]     - Visualize DAG")
        print("  python cli.py validate                     - Validate lineage integrity")
        print("")
        print("Query Commands:")
        print("  python cli.py query --state <state>        - Query by state")
        print("  python cli.py query --path <substring>     - Query by path substring")
        print("  python cli.py query --meta key=value       - Query by metadata")
        print("")
        print("Lifecycle Commands:")
        print("  python cli.py archive <id>                 - Archive a DO")
        print("  python cli.py delete <id>                  - Soft delete a DO (reject)")
        print("")
        print("Lineage Commands:")
        print("  python cli.py ancestors <id>               - Show ancestors of a DO")
        print("  python cli.py descendants <id>             - Show descendants of a DO")
        print("  python cli.py siblings <id>                - Show siblings of a DO")
        print("")
        print("  python cli.py inspect <id>                 - Full inspection of a DO")
        return

    cmd = sys.argv[1]

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a file path")
            return

        file_path = sys.argv[2]

        # Validate file exists
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return

        do_id = ingest(file_path)
        print(f"[INGESTED] DO ID: {do_id}")

    elif cmd == "run":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return

        do_id = sys.argv[2]

        # Get parent DO
        parent_do = get_do(do_id)
        if parent_do is None:
            print(f"[ERROR] Data Object not found: {do_id}")
            return

        child_id, result = run(do_id, parent_do["path"])

        print(f"[PIPELINE COMPLETE]")
        print(f"  Parent DO: {do_id[:8]}... (state: CURATED)")
        print(f"  Child DO:  {child_id[:8]}... (state: ACTIVE)")
        print(f"  Output: {result['output_path']}")

    elif cmd == "status":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return

        do_id = sys.argv[2]
        do_data = get_do(do_id)

        if do_data is None:
            print(f"[ERROR] Data Object not found: {do_id}")
            return

        print(f"[DATA OBJECT] {do_id}")
        print(f"  State:     {do_data['state']}")
        print(f"  Type:      {do_data['type']}")
        print(f"  Path:      {do_data['path']}")
        print(f"  Lineage:   {[p[:8] for p in do_data['lineage']]}")
        print(f"  Created:   {do_data['created_at']}")
        print(f"  Updated:   {do_data['updated_at']}")
        if do_data['metadata']:
            print(f"  Meta  {do_data['metadata']}")

    elif cmd == "list":
        dos = get_all_dos()

        if not dos:
            print("[INFO] No Data Objects in registry")
            return

        print(f"[DATA OBJECTS] ({len(dos)} total)")
        print("-" * 80)
        for do_data in dos:
            print(f"ID: {do_data['id'][:8]}... | State: {do_data['state']:10} | Path: {do_data['path']}")

    elif cmd == "lineage":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return

        do_id = sys.argv[2]
        show_do_lineage(do_id)

    elif cmd == "dag":
        fmt = "ascii"
        if len(sys.argv) >= 4 and sys.argv[3] == "--format":
            if len(sys.argv) >= 5:
                fmt = sys.argv[4]

        if fmt == "ascii":
            print_dag_ascii()
        elif fmt == "dot":
            filename = "dflow_graph.dot"
            save_dot_file(filename)
        else:
            print(f"[ERROR] Unknown format: {fmt}. Use 'ascii' or 'dot'")

    elif cmd == "validate":
        print("[VALIDATING LINEAGE INTEGRITY...]")

        # Check lineage integrity
        is_valid, errors = validate_lineage_integrity()
        if not is_valid:
            print(f"[FAIL] Lineage integrity issues found:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("[PASS] Lineage integrity OK")

        # Check for cycles
        has_cycles, cycles = detect_lineage_cycles()
        if has_cycles:
            print(f"[FAIL] Cycles detected:")
            for cycle in cycles:
                cycle_str = " -> ".join([cid[:8] for cid in cycle])
                print(f"  - {cycle_str}")
        else:
            print("[PASS] No cycles detected")

        # Validate graph
        try:
            is_valid, errors = validate_graph_integrity()
            if not is_valid:
                print(f"[FAIL] Graph integrity issues:")
                for err in errors:
                    print(f"  - {err}")
            else:
                print("[PASS] Graph integrity OK")
        except Exception as e:
            print(f"[FAIL] Graph validation error: {e}")

        print("\n[VALIDATION COMPLETE]")

    elif cmd == "query":
        # Query command with filters
        results = None
        
        if len(sys.argv) >= 4 and sys.argv[2] == "--state":
            state = sys.argv[3]
            results = filter_by_state(state)
            print(f"[QUERY] State: {state} ({len(results)} results)")
        
        elif len(sys.argv) >= 4 and sys.argv[2] == "--path":
            path_substring = sys.argv[3]
            results = filter_by_path(path_substring)
            print(f"[QUERY] Path contains: {path_substring} ({len(results)} results)")
        
        elif len(sys.argv) >= 4 and sys.argv[2] == "--meta":
            meta_arg = sys.argv[3]
            if "=" not in meta_arg:
                print("[ERROR] Metadata query must be key=value format")
                return
            key, value = meta_arg.split("=", 1)
            results = search_metadata(key, value)
            print(f"[QUERY] Metadata {key}={value} ({len(results)} results)")
        
        else:
            print("[ERROR] Query requires --state, --path, or --meta argument")
            return
        
        if results:
            print("-" * 80)
            for do_data in results:
                print(f"ID: {do_data['id'][:8]}... | State: {do_data['state']:10} | Path: {do_data['path']}")
        else:
            print("[INFO] No matching Data Objects found")

    elif cmd == "archive":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        try:
            result = archive(do_id)
            print(f"[ARCHIVED] {do_id[:8]}... transitioned from {result['from_state']} to {result['to_state']}")
        except Exception as e:
            print(f"[ERROR] Failed to archive: {e}")

    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        try:
            result = delete(do_id)
            print(f"[DELETED] {do_id[:8]}... transitioned from {result['from_state']} to {result['to_state']} (soft delete)")
        except Exception as e:
            print(f"[ERROR] Failed to delete: {e}")

    elif cmd == "ancestors":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        ancestors = get_ancestors(do_id)
        print(f"[ANCESTORS of {do_id[:8]}...] ({len(ancestors)} found)")
        for ancestor_id in ancestors:
            ancestor = get_do(ancestor_id)
            if ancestor:
                print(f"  - {ancestor_id[:8]}... | State: {ancestor['state']:10} | Path: {ancestor['path']}")
            else:
                print(f"  - {ancestor_id[:8]}... | (not found)")

    elif cmd == "descendants":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        descendants = get_descendants(do_id)
        print(f"[DESCENDANTS of {do_id[:8]}...] ({len(descendants)} found)")
        for desc_id in descendants:
            desc = get_do(desc_id)
            if desc:
                print(f"  - {desc_id[:8]}... | State: {desc['state']:10} | Path: {desc['path']}")
            else:
                print(f"  - {desc_id[:8]}... | (not found)")

    elif cmd == "siblings":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        siblings = get_siblings(do_id)
        print(f"[SIBLINGS of {do_id[:8]}...] ({len(siblings)} found)")
        for sib_id in siblings:
            sib = get_do(sib_id)
            if sib:
                print(f"  - {sib_id[:8]}... | State: {sib['state']:10} | Path: {sib['path']}")
            else:
                print(f"  - {sib_id[:8]}... | (not found)")

    elif cmd == "inspect":
        if len(sys.argv) < 3:
            print("[ERROR] Please provide a DO ID")
            return
        
        do_id = sys.argv[2]
        do_data = get_do(do_id)
        
        if do_data is None:
            print(f"[ERROR] Data Object not found: {do_id}")
            return
        
        print(f"[INSPECTION] {do_id}")
        print("=" * 80)
        print(f"State:     {do_data['state']}")
        print(f"Type:      {do_data['type']}")
        print(f"Path:      {do_data['path']}")
        print(f"Created:   {do_data['created_at']}")
        print(f"Updated:   {do_data['updated_at']}")
        print(f"Lineage:   {[p[:8] for p in do_data['lineage']]}")
        if do_data['metadata']:
            print(f"Metadata:  {do_data['metadata']}")
        
        # Show allowed transitions
        allowed = get_allowed_next_states(do_id)
        print(f"\nAllowed transitions: {allowed if allowed else 'None (terminal state)'}")
        
        # Show ancestors
        ancestors = get_ancestors(do_id)
        if ancestors:
            print(f"\nAncestors ({len(ancestors)}):")
            for a_id in ancestors:
                print(f"  - {a_id[:8]}...")
        
        # Show descendants
        descendants = get_descendants(do_id)
        if descendants:
            print(f"\nDescendants ({len(descendants)}):")
            for d_id in descendants:
                print(f"  - {d_id[:8]}...")

    else:
        print(f"[ERROR] Unknown command: {cmd}")
        print("Available commands: ingest, run, status, list, lineage, dag, validate, query, archive, delete, ancestors, descendants, siblings, inspect")


if __name__ == "__main__":
    main()