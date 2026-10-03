"""Initialize (or re-verify) the SQLite database with schema + seed criteria.

Safe to re-run: table creation uses IF NOT EXISTS and criteria are only seeded
if the evaluation_criteria table is currently empty.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.database import init_db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=os.environ.get("DATABASE_PATH", "data/app.db"))
    args = parser.parse_args()
    init_db(args.db_path)
    print(f"Database initialized at {args.db_path}")


if __name__ == "__main__":
    main()
