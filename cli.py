import sys
from bootstrap import initialize
from core.workflow import ingest, run

def main():
    initialize()

    cmd = sys.argv[1]

    if cmd == "ingest":
        file_path = sys.argv[2]
        do_id = ingest(file_path)
        print("[INGESTED]", do_id)

    if cmd == "run":
        file_path = sys.argv[2]

        # fake parent ID for now
        do_id = ingest(file_path)

        child, result = run(do_id, file_path)

        print("[CHILD DO]", child)
        print("[RESULT]", result)


if __name__ == "__main__":
    main()