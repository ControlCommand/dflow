import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bootstrap import initialize
from core.workflow import ingest, run
from core.registry import get_do, get_all_dos


def main():
    initialize()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cli.py ingest <file_path>     - Ingest a file into the system")
        print("  python cli.py run <file_path>        - Run pipeline on a file")
        print("  python cli.py status <do_id>         - Get status of a Data Object")
        print("  python cli.py list                   - List all Data Objects")
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
            print("[ERROR] Please provide a file path")
            return
        
        file_path = sys.argv[2]
        
        # Validate file exists
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        # Create initial DO and run workflow
        do_id = ingest(file_path)
        child_id, result = run(do_id, file_path)
        
        print(f"[PIPELINE COMPLETE]")
        print(f"  Parent DO: {do_id} (state: CURATED)")
        print(f"  Child DO:  {child_id} (state: ACTIVE)")
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
        print(f"  Lineage:   {do_data['lineage']}")
        print(f"  Created:   {do_data['created_at']}")
        print(f"  Updated:   {do_data['updated_at']}")
        if do_data['metadata']:
            print(f"  Metadata:  {do_data['metadata']}")
    
    elif cmd == "list":
        dos = get_all_dos()
        
        if not dos:
            print("[INFO] No Data Objects in registry")
            return
        
        print(f"[DATA OBJECTS] ({len(dos)} total)")
        print("-" * 80)
        for do_data in dos:
            print(f"ID: {do_data['id'][:8]}... | State: {do_data['state']:10} | Path: {do_data['path']}")
    
    else:
        print(f"[ERROR] Unknown command: {cmd}")
        print("Available commands: ingest, run, status, list")


if __name__ == "__main__":
    main()