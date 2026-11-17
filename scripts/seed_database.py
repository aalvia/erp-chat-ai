import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.database.seed import seed_demo
from app.database.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        summary = seed_demo(db)
    finally:
        db.close()
    print("Base de demostración lista.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
