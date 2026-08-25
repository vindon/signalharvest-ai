#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import settings
from db.database import init_db


def main():
    settings.ensure_dirs()
    print(f"Initialising database at: {settings.database_path}")
    init_db()
    print(f"Done. Path: {settings.database_path_obj.resolve()}")


if __name__ == "__main__":
    main()
