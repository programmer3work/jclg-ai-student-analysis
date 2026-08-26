"""Seed clearly labeled demo records for the Module 4 visual demo."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

DATA_FILE = Path(__file__).with_name("demo_data.json")


def columns(connection, table):
    return {
        row[0]
        for row in connection.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = :table"),
            {"table": table},
        )
    }


def insert_row(connection, table, values):
    available = columns(connection, table)
    values = {key: value for key, value in values.items() if key in available}
    fields = ", ".join(values)
    parameters = ", ".join(f":{key}" for key in values)
    connection.execute(text(f"INSERT INTO {table} ({fields}) VALUES ({parameters}) ON CONFLICT DO NOTHING"), values)


def main():
    with DATA_FILE.open(encoding="utf-8") as data_file:
        demo_data = json.load(data_file)
    streams = {item["code"]: item["name"] for item in demo_data["streams"]}
    stream_subjects = {item["code"]: item["subjects"] for item in demo_data["streams"]}
    student_branches = {int(student_id): branch for student_id, branch in demo_data["student_branches"].items()}
    risk_by_student = {int(student_id): risk for student_id, risk in demo_data["risk_by_student"].items()}
    recommendations = demo_data["recommendations"]

    with engine.begin() as connection:
        stream_columns = columns(connection, "jclg_stream")
        existing_stream = connection.execute(text("SELECT * FROM jclg_stream ORDER BY stream_id LIMIT 1")).mappings().first()
        for code, name in streams.items():
            values = {"stream_code": code, "stream_name": name}
            if existing_stream:
                for field in ("campus_id", "status"):
                    if field in stream_columns and existing_stream.get(field) is not None:
                        values[field] = existing_stream[field]
            insert_row(connection, "jclg_stream", values)

        group_columns = columns(connection, "jclg_group")
        existing_group = connection.execute(text("SELECT * FROM jclg_group ORDER BY group_id LIMIT 1")).mappings().first()
        stream_rows = connection.execute(text("SELECT stream_id, stream_code FROM jclg_stream")).mappings().all()
        stream_ids = {row["stream_code"]: row["stream_id"] for row in stream_rows}
        group_ids = {}
        for code in streams:
            row = connection.execute(text("SELECT group_id FROM jclg_group WHERE stream_id = :stream_id ORDER BY group_id LIMIT 1"), {"stream_id": stream_ids[code]}).first()
            if row:
                group_ids[code] = row[0]
                continue
            values = {"stream_id": stream_ids[code], "group_code": f"{code}-A", "group_name": f"{code} Intermediate A", "status": True}
            if existing_group:
                for field in ("academic_year_id", "campus_id"):
                    if field in group_columns and existing_group.get(field) is not None:
                        values[field] = existing_group[field]
            insert_row(connection, "jclg_group", values)
            group_ids[code] = connection.execute(text("SELECT group_id FROM jclg_group WHERE stream_id = :stream_id ORDER BY group_id DESC LIMIT 1"), {"stream_id": stream_ids[code]}).scalar_one()

        subject_columns = columns(connection, "jclg_subject")
        existing_subject = connection.execute(text("SELECT * FROM jclg_subject ORDER BY subject_id LIMIT 1")).mappings().first()
        subject_ids = {}
        for branch, names in stream_subjects.items():
            for name in names:
                code = f"{branch}-{name.upper().replace(' ', '-')[:12]}"
                row = connection.execute(text("SELECT subject_id FROM jclg_subject WHERE subject_code = :code"), {"code": code}).first()
                if not row:
                    values = {"subject_code": code, "subject_name": name}
                    if "status" in subject_columns:
                        values["status"] = True
                    if existing_subject:
                        for field in ("campus_id", "subject_type", "credits", "pass_marks", "max_marks"):
                            if field in subject_columns and existing_subject.get(field) is not None:
                                values[field] = existing_subject[field]
                    insert_row(connection, "jclg_subject", values)
                    row = connection.execute(text("SELECT subject_id FROM jclg_subject WHERE subject_code = :code"), {"code": code}).first()
                subject_ids[(branch, name)] = row[0]

        exam_subject_columns = columns(connection, "jclg_exam_subject")
        existing_exam_subject = connection.execute(text("SELECT * FROM jclg_exam_subject ORDER BY exam_subject_id LIMIT 1")).mappings().first()
        exam_subject_ids = {}
        exam_columns = columns(connection, "jclg_exam")
        exam_date_column = "exam_date" if "exam_date" in exam_columns else "start_date"
        exam_rows = connection.execute(text(f"SELECT exam_id, {exam_date_column} AS exam_date FROM jclg_exam ORDER BY exam_id")).mappings().all()
        exam_ids = [row["exam_id"] for row in exam_rows]
        exam_dates = {row["exam_id"]: row["exam_date"] for row in exam_rows}
        for branch, names in stream_subjects.items():
            for exam_id in exam_ids:
                for name in names:
                    subject_id = subject_ids[(branch, name)]
                    row = connection.execute(text("SELECT exam_subject_id FROM jclg_exam_subject WHERE exam_id = :exam_id AND subject_id = :subject_id"), {"exam_id": exam_id, "subject_id": subject_id}).first()
                    if not row:
                        values = {"exam_id": exam_id, "subject_id": subject_id, "max_marks": 100}
                        if "exam_date" in exam_subject_columns:
                            values["exam_date"] = exam_dates[exam_id]
                        if existing_exam_subject:
                            for field in ("section_id", "status", "pass_marks"):
                                if field in exam_subject_columns and existing_exam_subject.get(field) is not None:
                                    values[field] = existing_exam_subject[field]
                        insert_row(connection, "jclg_exam_subject", values)
                        row = connection.execute(text("SELECT exam_subject_id FROM jclg_exam_subject WHERE exam_id = :exam_id AND subject_id = :subject_id"), {"exam_id": exam_id, "subject_id": subject_id}).first()
                    exam_subject_ids[(branch, exam_id, name)] = row[0]

        student_columns = columns(connection, "jclg_student")
        for student_id, branch in student_branches.items():
            assignments = {"group_id": group_ids[branch]}
            if "stream_id" in student_columns:
                assignments["stream_id"] = stream_ids[branch]
            setters = ", ".join(f"{key} = :{key}" for key in assignments)
            assignments["student_id"] = student_id
            connection.execute(text(f"UPDATE jclg_student SET {setters} WHERE student_id = :student_id"), assignments)

            marks = connection.execute(text("""SELECT m.marks_id, es.exam_id
                                             FROM jclg_marks m
                                             JOIN jclg_exam_subject es ON es.exam_subject_id = m.exam_subject_id
                                             WHERE m.student_id = :student_id
                                             ORDER BY es.exam_id, m.marks_id"""), {"student_id": student_id}).mappings().all()
            for exam_id in sorted({row["exam_id"] for row in marks}):
                exam_marks = [row for row in marks if row["exam_id"] == exam_id]
                for mark, name in zip(exam_marks, stream_subjects[branch]):
                    connection.execute(text("UPDATE jclg_marks SET exam_subject_id = :exam_subject_id WHERE marks_id = :marks_id"), {"exam_subject_id": exam_subject_ids[(branch, exam_id, name)], "marks_id": mark["marks_id"]})

        insight_columns = columns(connection, "jclg_ai_insight")
        if "stream_id" in insight_columns and "risk_level" in insight_columns:
            for student_id, branch in student_branches.items():
                risk = risk_by_student.get(student_id, "low")
                connection.execute(
                    text("""UPDATE jclg_ai_insight
                           SET stream_id = :stream_id, risk_level = :risk_level, recommendation = :recommendation
                           WHERE student_id = :student_id"""),
                    {"stream_id": stream_ids[branch], "risk_level": risk, "recommendation": recommendations[risk], "student_id": student_id},
                )

        exam_rows = connection.execute(text(f"SELECT exam_id, {exam_date_column} AS exam_date FROM jclg_exam ORDER BY exam_id")).mappings().all()
        for exam, configured_exam in zip(exam_rows, demo_data["exams"]):
            connection.execute(text("UPDATE jclg_exam SET exam_name = :exam_name WHERE exam_id = :exam_id"), {"exam_name": configured_exam["name"], "exam_id": exam["exam_id"]})

    print(f"Demo seed applied from {DATA_FILE.name}.")


if __name__ == "__main__":
    main()
