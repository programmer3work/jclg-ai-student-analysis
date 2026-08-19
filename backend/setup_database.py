from pathlib import Path

from sqlalchemy import create_engine

from config import DATABASE_URL

ROOT = Path(__file__).resolve().parent.parent


def run_sql(path):
    sql = path.read_text(encoding="utf-8")
    engine = create_engine(DATABASE_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql(sql)


if __name__ == "__main__":
    run_sql(ROOT / "database" / "schema.sql")
    run_sql(ROOT / "database" / "seed.sql")
    print("Module 4 schema and sample data are ready.")
