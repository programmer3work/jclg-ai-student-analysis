from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

from config import ANALYSIS_TYPES, DATABASE_URL, DEFAULT_LANGUAGE, FRONTEND_ORIGINS, RISK_ATTENDANCE_THRESHOLD, RISK_LEVELS, RISK_MARKS_THRESHOLD, SUPPORTED_LANGUAGES

engine = create_engine(DATABASE_URL)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=FRONTEND_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def fetch_rows(query, parameters=None):
    with engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(query), parameters or {}).mappings()]


def ensure_student(student_id):
    if not fetch_rows("SELECT student_id FROM jclg_student WHERE student_id = :student_id", {"student_id": student_id}):
        raise HTTPException(status_code=404, detail="Student not found")


def table_schema_columns(table_name):
    with engine.connect() as connection:
        rows = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
        """), {"table_name": table_name}).scalars().all()
    return {column.lower() for column in rows}


def student_schema_columns():
    return table_schema_columns("jclg_student")


def student_name_sql():
    columns = student_schema_columns()
    if "name" in columns:
        return "s.name"
    return "CONCAT(COALESCE(s.first_name, ''), CASE WHEN COALESCE(s.first_name, '') <> '' AND COALESCE(s.last_name, '') <> '' THEN ' ' ELSE '' END, COALESCE(s.last_name, ''))"


def student_admission_sql():
    columns = student_schema_columns()
    if "admission_no" in columns:
        return "COALESCE(s.admission_no, s.student_code)"
    if "student_code" in columns:
        return "s.student_code"
    return "COALESCE(s.admission_no, s.student_code)"


def student_class_sql():
    columns = student_schema_columns()
    if "class_name" in columns:
        return "s.class_name"
    return "COALESCE(g.group_code, 'N/A')"


def student_section_sql():
    columns = student_schema_columns()
    if "section" in columns:
        return "s.section"
    return "COALESCE(sec.section_name, 'N/A')"


def parent_name_sql():
    columns = table_schema_columns("jclg_parent")
    if "name" in columns:
        return "p.name"
    if "first_name" in columns or "last_name" in columns:
        return "CONCAT(COALESCE(p.first_name, ''), CASE WHEN COALESCE(p.first_name, '') <> '' AND COALESCE(p.last_name, '') <> '' THEN ' ' ELSE '' END, COALESCE(p.last_name, ''))"
    if "guardian_name" in columns or "father_name" in columns or "mother_name" in columns:
        return "COALESCE(NULLIF(p.guardian_name, ''), NULLIF(p.father_name, ''), NULLIF(p.mother_name, ''), 'Not available')"
    return "'Not available'"


def parent_contact_sql():
    columns = table_schema_columns("jclg_parent")
    for column in ("contact", "phone", "mobile"):
        if column in columns:
            return f"p.{column}"
    return "'N/A'"


def parent_relation_sql():
    return "p.relation" if "relation" in table_schema_columns("jclg_parent") else "'N/A'"


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/config")
def application_config():
    streams = fetch_rows("SELECT stream_id, stream_code, stream_name FROM jclg_stream ORDER BY stream_code")
    subject_columns = table_schema_columns("jclg_subject")
    subject_stream = "stream_id" if "stream_id" in subject_columns else "NULL"
    subjects = fetch_rows(f"SELECT subject_id, subject_code, subject_name, {subject_stream} AS stream_id FROM jclg_subject ORDER BY subject_name")
    return {"streams": streams, "classes": [row["stream_code"] for row in streams], "subjects": subjects, "languages": SUPPORTED_LANGUAGES, "default_language": DEFAULT_LANGUAGE, "analysis_types": ANALYSIS_TYPES, "risk_levels": RISK_LEVELS}


@app.get("/dashboard")
def dashboard_alias():
    return dashboard_statistics()


@app.get("/dashboard/statistics")
def dashboard_statistics():
    return fetch_rows("""
        SELECT (SELECT COUNT(*) FROM jclg_student) AS total_students,
               (SELECT COUNT(DISTINCT student_id) FROM jclg_ai_insight WHERE LOWER(risk_level) = 'high') AS high_risk,
               (SELECT COUNT(DISTINCT student_id) FROM jclg_attendance WHERE LOWER(engagement_status) = 'improving') AS improving,
               (SELECT COUNT(*) FROM jclg_ai_insight) AS ai_insights
    """)[0]


@app.get("/student")
@app.get("/students")
def students():
    columns = student_schema_columns()
    stream_join = "LEFT JOIN jclg_stream st ON st.stream_id = s.stream_id" if "stream_id" in columns else "LEFT JOIN jclg_group g ON g.group_id = s.group_id LEFT JOIN jclg_stream st ON st.stream_id = g.stream_id LEFT JOIN jclg_section sec ON sec.section_id = s.section_id"
    parent_name = parent_name_sql()
    parent_contact = parent_contact_sql()
    parent_relation = parent_relation_sql()
    return {"value": fetch_rows(f"""
        SELECT s.student_id,
               {student_admission_sql()} AS admission_no,
               {student_name_sql()} AS name,
               {student_class_sql()} AS class_name,
               {student_section_sql()} AS section,
               st.stream_code, st.stream_name,
               COALESCE(g.group_code, 'N/A') AS group_code,
               {parent_name} AS parent_name, {parent_contact} AS parent_contact, {parent_relation} AS parent_relation
        FROM jclg_student s
        {stream_join}
        LEFT JOIN jclg_student_parent sp ON sp.student_id = s.student_id
        LEFT JOIN jclg_parent p ON p.parent_id = sp.parent_id
        ORDER BY s.student_id
    """)}


@app.get("/performance/{student_id}")
def performance(student_id: int):
    ensure_student(student_id)
    mark_columns = table_schema_columns("jclg_marks")
    production_marks = "marks_id" in mark_columns and "exam_subject_id" in mark_columns
    mark_id = "m.marks_id" if production_marks else "m.mark_id"
    subject_id = "es.subject_id" if production_marks else "m.subject_id"
    exam_columns = table_schema_columns("jclg_exam")
    exam_date = "e.exam_date" if "exam_date" in exam_columns else "e.start_date"
    exam_date = exam_date if production_marks else "m.exam_date"
    exam_id = "es.exam_id" if production_marks else "m.exam_id"
    total_marks = "es.max_marks" if production_marks else "m.total_marks"
    mark_status = "COALESCE(m.grade, 'Published')" if production_marks else "m.status"
    mark_join = "JOIN jclg_exam_subject es ON es.exam_subject_id = m.exam_subject_id" if production_marks else ""
    subjects = fetch_rows(f"""
        SELECT {mark_id} AS mark_id, sub.subject_code, sub.subject_name, m.marks_obtained,
               {total_marks} AS total_marks, {exam_date} AS exam_date, {mark_status} AS status, e.exam_name,
               ROUND(AVG(m.marks_obtained) OVER (PARTITION BY {subject_id}), 2) AS subject_average
        FROM jclg_marks m
        {mark_join}
        JOIN jclg_subject sub ON sub.subject_id = {subject_id}
        JOIN jclg_exam e ON e.exam_id = {exam_id}
        WHERE m.student_id = :student_id
        ORDER BY {exam_date}, sub.subject_name
    """, {"student_id": student_id})
    result_status = "r.result_status" if "result_status" in table_schema_columns("jclg_result") else "r.status"
    result_exam_date = "e.exam_date" if "exam_date" in exam_columns else "e.start_date"
    results = fetch_rows(f"""
        SELECT r.result_id, e.exam_name, r.total_marks, r.percentage, r.grade, {result_status} AS status
        FROM jclg_result r JOIN jclg_exam e ON e.exam_id = r.exam_id
        WHERE r.student_id = :student_id ORDER BY {result_exam_date}
    """, {"student_id": student_id})
    average = fetch_rows("SELECT ROUND(AVG(marks_obtained), 2) AS average_marks, COUNT(*) AS recorded_marks FROM jclg_marks WHERE student_id = :student_id", {"student_id": student_id})[0]
    return {"student_id": student_id, "average": average, "subjects": subjects, "results": results}


@app.get("/engagement/{student_id}")
def engagement(student_id: int):
    ensure_student(student_id)
    attendance_columns = table_schema_columns("jclg_attendance")
    attendance_status = "status" if "status" in attendance_columns else "engagement_status"
    assignments = "NULL::numeric" if "assignments_completed" not in attendance_columns else "assignments_completed"
    participation = "NULL::numeric" if "participation_score" not in attendance_columns else "participation_score"
    return fetch_rows(f"""
        SELECT ROUND(AVG(CASE WHEN LOWER(CAST({attendance_status} AS TEXT)) IN ('true', 'present', 'attended', 'yes') THEN 100.0 ELSE 0.0 END), 2) AS attendance_percent,
               ROUND(AVG({assignments}), 2) AS assignments_completed,
               ROUND(AVG({participation}), 2) AS participation_score,
               (ARRAY_AGG(engagement_status ORDER BY attendance_date DESC))[1] AS status,
               COUNT(*) AS attendance_records
        FROM jclg_attendance WHERE student_id = :student_id
    """, {"student_id": student_id})[0]


@app.get("/risk")
def risk():
    columns = student_schema_columns()
    student_join = "JOIN jclg_student s ON s.student_id = i.student_id" if "stream_id" in columns or "name" in columns or "first_name" in columns else "JOIN jclg_student s ON s.student_id = i.student_id"
    rows = fetch_rows(f"""
        WITH current_insight AS (
            SELECT i.*, ROW_NUMBER() OVER (PARTITION BY i.student_id ORDER BY i.generated_at DESC, i.insight_id DESC) AS row_number
            FROM jclg_ai_insight i
        )
        SELECT i.student_id,
               {student_name_sql()} AS name,
               {student_admission_sql()} AS admission_no,
               {student_class_sql()} AS class_name,
               {student_section_sql()} AS section,
               st.stream_code, LOWER(i.risk_level) AS risk_level, i.analysis_type, i.recommendation,
               i.generated_at,
               COALESCE(att.attendance_percent, 0) AS attendance_percent,
               COALESCE(marks.average_marks, 0) AS average_marks,
               CASE
                   WHEN COALESCE(att.attendance_percent, 0) < :attendance_threshold THEN 'Low attendance'
                   WHEN COALESCE(marks.average_marks, 0) < :marks_threshold THEN 'Low academic performance'
                   WHEN LOWER(i.risk_level) <> 'low' THEN 'AI risk assessment'
                   ELSE 'Stable indicators'
               END AS primary_indicator
        FROM current_insight i
        {student_join}
        LEFT JOIN jclg_group g ON g.group_id = s.group_id
        LEFT JOIN jclg_stream st ON st.stream_id = COALESCE(i.stream_id, g.stream_id)
        LEFT JOIN jclg_section sec ON sec.section_id = s.section_id
        LEFT JOIN (
            SELECT student_id, AVG(CASE WHEN LOWER(CAST(status AS TEXT)) IN ('true', 'present', 'attended', 'yes') THEN 100.0 ELSE 0.0 END) AS attendance_percent
            FROM jclg_attendance GROUP BY student_id
        ) att ON att.student_id = i.student_id
        LEFT JOIN (
            SELECT student_id, AVG(marks_obtained) AS average_marks
            FROM jclg_marks GROUP BY student_id
        ) marks ON marks.student_id = i.student_id
        WHERE i.row_number = 1 ORDER BY s.student_id
    """, {"attendance_threshold": RISK_ATTENDANCE_THRESHOLD, "marks_threshold": RISK_MARKS_THRESHOLD})
    for row in rows:
        if not row["risk_level"]:
            attendance = float(row["attendance_percent"] or 0)
            average_marks = float(row["average_marks"] or 0)
            if attendance < RISK_ATTENDANCE_THRESHOLD or average_marks < RISK_MARKS_THRESHOLD:
                row["risk_level"] = "high"
            elif attendance < 85 or average_marks < 75:
                row["risk_level"] = "moderate"
            else:
                row["risk_level"] = "low"
            row["primary_indicator"] = "Derived from attendance and marks"
    counts = {"low": 0, "moderate": 0, "high": 0}
    for row in rows:
        if row["risk_level"] in counts:
            counts[row["risk_level"]] += 1
    trend = fetch_rows("""
        SELECT generated_at::date AS assessed_date,
               COUNT(*) FILTER (WHERE LOWER(risk_level) = 'low') AS low,
               COUNT(*) FILTER (WHERE LOWER(risk_level) = 'moderate') AS moderate,
               COUNT(*) FILTER (WHERE LOWER(risk_level) = 'high') AS high
        FROM jclg_ai_insight
        GROUP BY generated_at::date ORDER BY assessed_date
    """)
    return {
        "summary": {"total_assessed": len(rows), **counts},
        "counts": counts,
        "trend": trend,
        "students": rows,
        "at_risk_students": [row for row in rows if row["risk_level"] != "low"],
    }


@app.get("/recommendations/{student_id}")
def recommendations(student_id: int, stream_code: str | None = None):
    ensure_student(student_id)
    rows = fetch_rows("""
        SELECT i.insight_id, i.analysis_type, i.risk_level, i.recommendation, i.generated_at,
               COALESCE(st.stream_code, 'N/A') AS stream_code, COALESCE(st.stream_name, 'Unknown') AS stream_name,
               COALESCE(g.group_code, 'N/A') AS group_code
        FROM jclg_ai_insight i
        JOIN jclg_student s ON s.student_id = i.student_id
        LEFT JOIN jclg_group g ON g.group_id = s.group_id
        LEFT JOIN jclg_stream st ON st.stream_id = COALESCE(i.stream_id, g.stream_id)
        WHERE i.student_id = :student_id AND (:stream_code IS NULL OR COALESCE(st.stream_code, 'N/A') = :stream_code)
        ORDER BY i.generated_at DESC, i.insight_id DESC
    """, {"student_id": student_id, "stream_code": stream_code})
    return {"student_id": student_id, "stream_code": stream_code, "recommendations": rows}


@app.get("/reports")
def reports(stream_code: str | None = None):
    parameters = {"stream_code": stream_code}
    name_expr = student_name_sql()
    admission_expr = student_admission_sql()
    exam_columns = table_schema_columns("jclg_exam")
    report_exam_date = "e.exam_date" if "exam_date" in exam_columns else "e.start_date"
    insights = fetch_rows(f"""
        SELECT i.insight_id,
               {name_expr} AS name,
               {admission_expr} AS admission_no,
               st.stream_code, i.analysis_type,
               i.risk_level, i.recommendation, i.generated_at
        FROM jclg_ai_insight i
        JOIN jclg_student s ON s.student_id = i.student_id
        LEFT JOIN jclg_group g ON g.group_id = s.group_id
        LEFT JOIN jclg_stream st ON st.stream_id = COALESCE(i.stream_id, g.stream_id)
        WHERE (:stream_code IS NULL OR st.stream_code = :stream_code)
        ORDER BY i.generated_at DESC, i.insight_id DESC
    """, parameters)
    results = fetch_rows(f"""
        SELECT r.result_id,
               {name_expr} AS name,
               {admission_expr} AS admission_no,
               st.stream_code, e.exam_name,
               r.total_marks, r.percentage, r.grade, {"r.result_status" if "result_status" in table_schema_columns("jclg_result") else "r.status"} AS status
        FROM jclg_result r
        JOIN jclg_student s ON s.student_id = r.student_id
        LEFT JOIN jclg_group g ON g.group_id = s.group_id
        LEFT JOIN jclg_stream st ON st.stream_id = g.stream_id
        JOIN jclg_exam e ON e.exam_id = r.exam_id
        WHERE (:stream_code IS NULL OR st.stream_code = :stream_code)
        ORDER BY {report_exam_date} DESC, s.student_id
    """, parameters)
    usage_columns = table_schema_columns("jclg_ai_usage")
    usage = fetch_rows(f"""
        SELECT u.usage_id,
               {name_expr} AS name,
               u.module_name, u.tokens_used, u.used_at
        FROM jclg_ai_usage u
        JOIN jclg_student s ON s.student_id = u.student_id
        ORDER BY u.used_at DESC, u.usage_id DESC
    """) if "student_id" in usage_columns else []
    alerts = [{"type": "Risk", "student": row["name"], "message": row["recommendation"], "level": row["risk_level"]} for row in insights if row["risk_level"].lower() != "low"]
    return {"insights": insights, "results": results, "ai_usage": usage, "alerts": alerts}
