"""
Progress Tracking Module
Handles student progress tracking and trends
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ProgressService:
    """Service for progress tracking and trends"""

    @staticmethod
    def get_student_progress(student_id):
        """Get progress trend for a student over time"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        e.exam_date,
                        e.exam_name,
                        ROUND(AVG(r.percentage), 2) as exam_percentage,
                        COUNT(r.result_id) as subject_count,
                        ROUND(AVG(r.marks_obtained), 2) as average_marks
                    FROM jclg_result r
                    JOIN jclg_exam e ON r.exam_id = e.exam_id
                    WHERE r.student_id = :student_id
                    GROUP BY e.exam_id, e.exam_date, e.exam_name
                    ORDER BY e.exam_date ASC
                """)
                results = conn.execute(query, {"student_id": student_id}).fetchall()
                
                progress = []
                for row in results:
                    progress.append({
                        "exam_date": str(row[0]) if row[0] else None,
                        "exam_name": row[1],
                        "exam_percentage": float(row[2]) if row[2] else 0,
                        "subject_count": row[3] or 0,
                        "average_marks": float(row[4]) if row[4] else 0,
                    })
                return progress
        except Exception as e:
            print(f"Error fetching progress: {e}")
            return []

    @staticmethod
    def get_progress_summary(student_id):
        """Get summary of progress metrics"""
        try:
            with engine.connect() as conn:
                # Get latest and previous exam performance
                query = text("""
                    WITH ranked_exams AS (
                        SELECT 
                            r.student_id,
                            e.exam_date,
                            ROUND(AVG(r.percentage), 2) as exam_avg,
                            ROW_NUMBER() OVER (ORDER BY e.exam_date DESC) as rn
                        FROM jclg_result r
                        JOIN jclg_exam e ON r.exam_id = e.exam_id
                        WHERE r.student_id = :student_id
                        GROUP BY r.student_id, e.exam_id, e.exam_date
                    )
                    SELECT 
                        MAX(CASE WHEN rn = 1 THEN exam_avg END) as latest_percentage,
                        MAX(CASE WHEN rn = 2 THEN exam_avg END) as previous_percentage,
                        COUNT(*) as total_exams
                    FROM ranked_exams
                """)
                result = conn.execute(query, {"student_id": student_id}).fetchone()
                
                latest = float(result[0]) if result[0] else 0
                previous = float(result[1]) if result[1] else 0
                improvement = latest - previous if previous > 0 else 0
                
                return {
                    "latest_percentage": latest,
                    "previous_percentage": previous,
                    "improvement": round(improvement, 2),
                    "total_exams": result[2] or 0,
                    "status": "improving" if improvement > 0 else ("stable" if improvement == 0 else "declining")
                }
        except Exception as e:
            print(f"Error fetching progress summary: {e}")
            return None

    @staticmethod
    def get_improving_students(class_name=None, limit=10):
        """Get list of students showing improvement"""
        try:
            with engine.connect() as conn:
                if class_name:
                    query = text("""
                        WITH ranked_exams AS (
                            SELECT 
                                s.student_id,
                                s.student_code,
                                s.class_name,
                                ROUND(AVG(r.percentage), 2) as exam_avg,
                                ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY e.exam_date DESC) as rn
                            FROM jclg_student s
                            LEFT JOIN jclg_result r ON s.student_id = r.student_id
                            LEFT JOIN jclg_exam e ON r.exam_id = e.exam_id
                            WHERE s.class_name = :class_name
                            GROUP BY s.student_id, s.student_code, s.class_name, e.exam_id
                        )
                        SELECT 
                            student_id,
                            student_code,
                            class_name,
                            MAX(CASE WHEN rn = 1 THEN exam_avg END) as latest,
                            MAX(CASE WHEN rn = 2 THEN exam_avg END) as previous
                        FROM ranked_exams
                        GROUP BY student_id, student_code, class_name
                        HAVING MAX(CASE WHEN rn = 1 THEN exam_avg END) > MAX(CASE WHEN rn = 2 THEN exam_avg END)
                        ORDER BY (MAX(CASE WHEN rn = 1 THEN exam_avg END) - MAX(CASE WHEN rn = 2 THEN exam_avg END)) DESC
                        LIMIT :limit
                    """)
                    results = conn.execute(query, {"class_name": class_name, "limit": limit}).fetchall()
                else:
                    query = text("""
                        WITH ranked_exams AS (
                            SELECT 
                                s.student_id,
                                s.student_code,
                                s.class_name,
                                ROUND(AVG(r.percentage), 2) as exam_avg,
                                ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY e.exam_date DESC) as rn
                            FROM jclg_student s
                            LEFT JOIN jclg_result r ON s.student_id = r.student_id
                            LEFT JOIN jclg_exam e ON r.exam_id = e.exam_id
                            GROUP BY s.student_id, s.student_code, s.class_name, e.exam_id
                        )
                        SELECT 
                            student_id,
                            student_code,
                            class_name,
                            MAX(CASE WHEN rn = 1 THEN exam_avg END) as latest,
                            MAX(CASE WHEN rn = 2 THEN exam_avg END) as previous
                        FROM ranked_exams
                        GROUP BY student_id, student_code, class_name
                        HAVING MAX(CASE WHEN rn = 1 THEN exam_avg END) > MAX(CASE WHEN rn = 2 THEN exam_avg END)
                        ORDER BY (MAX(CASE WHEN rn = 1 THEN exam_avg END) - MAX(CASE WHEN rn = 2 THEN exam_avg END)) DESC
                        LIMIT :limit
                    """)
                    results = conn.execute(query, {"limit": limit}).fetchall()
                
                improving = []
                for row in results:
                    latest = float(row[3]) if row[3] else 0
                    previous = float(row[4]) if row[4] else 0
                    improving.append({
                        "student_id": row[0],
                        "student_code": row[1],
                        "class_name": row[2],
                        "latest_percentage": latest,
                        "previous_percentage": previous,
                        "improvement": round(latest - previous, 2)
                    })
                return improving
        except Exception as e:
            print(f"Error fetching improving students: {e}")
            return []
