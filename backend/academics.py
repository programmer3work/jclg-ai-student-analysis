"""
Academic Performance Module
Handles academic data analysis and metrics
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class AcademicService:
    """Service for academic performance data"""

    @staticmethod
    def get_student_academics(student_id):
        """Get academic performance for a student"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        s.student_id,
                        s.student_code,
                        s.class_name,
                        s.section,
                        COUNT(DISTINCT r.exam_id) as total_exams,
                        ROUND(AVG(r.percentage), 2) as average_percentage,
                        MAX(r.percentage) as highest_percentage,
                        MIN(r.percentage) as lowest_percentage,
                        ROUND(AVG(r.marks_obtained), 2) as average_marks
                    FROM jclg_student s
                    LEFT JOIN jclg_result r ON s.student_id = r.student_id
                    WHERE s.student_id = :student_id
                    GROUP BY s.student_id, s.student_code, s.class_name, s.section
                """)
                result = conn.execute(query, {"student_id": student_id}).fetchone()
                
                if result:
                    return {
                        "student_id": result[0],
                        "student_code": result[1],
                        "class_name": result[2],
                        "section": result[3],
                        "total_exams": result[4] or 0,
                        "average_percentage": float(result[5]) if result[5] else 0,
                        "highest_percentage": float(result[6]) if result[6] else 0,
                        "lowest_percentage": float(result[7]) if result[7] else 0,
                        "average_marks": float(result[8]) if result[8] else 0,
                    }
                return None
        except Exception as e:
            print(f"Error fetching academics: {e}")
            return None

    @staticmethod
    def get_subject_wise_performance(student_id):
        """Get subject-wise performance breakdown"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        sub.subject_id,
                        sub.subject_name,
                        COUNT(r.result_id) as attempts,
                        ROUND(AVG(r.percentage), 2) as average_percentage,
                        ROUND(AVG(r.marks_obtained), 2) as average_marks,
                        MAX(r.percentage) as best_percentage
                    FROM jclg_subject sub
                    LEFT JOIN jclg_exam_subject es ON sub.subject_id = es.subject_id
                    LEFT JOIN jclg_result r ON es.exam_subject_id = r.exam_subject_id 
                        AND r.student_id = :student_id
                    GROUP BY sub.subject_id, sub.subject_name
                    ORDER BY average_percentage DESC
                """)
                results = conn.execute(query, {"student_id": student_id}).fetchall()
                
                subjects = []
                for row in results:
                    subjects.append({
                        "subject_id": row[0],
                        "subject_name": row[1],
                        "attempts": row[2] or 0,
                        "average_percentage": float(row[3]) if row[3] else 0,
                        "average_marks": float(row[4]) if row[4] else 0,
                        "best_percentage": float(row[5]) if row[5] else 0,
                    })
                return subjects
        except Exception as e:
            print(f"Error fetching subject performance: {e}")
            return []

    @staticmethod
    def get_class_analytics():
        """Get overall class performance analytics"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        s.class_name,
                        COUNT(DISTINCT s.student_id) as total_students,
                        ROUND(AVG(r.percentage), 2) as class_average,
                        MAX(r.percentage) as highest_score,
                        MIN(r.percentage) as lowest_score,
                        COUNT(CASE WHEN r.percentage >= 75 THEN 1 END) as high_performers
                    FROM jclg_student s
                    LEFT JOIN jclg_result r ON s.student_id = r.student_id
                    GROUP BY s.class_name
                    ORDER BY s.class_name
                """)
                results = conn.execute(query).fetchall()
                
                analytics = []
                for row in results:
                    analytics.append({
                        "class_name": row[0],
                        "total_students": row[1],
                        "class_average": float(row[2]) if row[2] else 0,
                        "highest_score": float(row[3]) if row[3] else 0,
                        "lowest_score": float(row[4]) if row[4] else 0,
                        "high_performers": row[5] or 0,
                    })
                return analytics
        except Exception as e:
            print(f"Error fetching class analytics: {e}")
            return []
