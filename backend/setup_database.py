from pathlib import Path

from sqlalchemy import create_engine

from config import DATABASE_URL

ROOT = Path(__file__).resolve().parent.parent


def run_sql(path):
    sql = path.read_text(encoding="utf-8")
    engine = create_engine(DATABASE_URL)
    with engine.begin() as connection:
        connection.exec_driver_sql(sql)


def setup_database():
    engine = create_engine(DATABASE_URL)
    schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    seed = (ROOT / "database" / "seed.sql").read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.exec_driver_sql(schema)
        connection.exec_driver_sql(seed)


if __name__ == "__main__":
    setup_database()
    print("Module 4 schema and sample data are ready.")
