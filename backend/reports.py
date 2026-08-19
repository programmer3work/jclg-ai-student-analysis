"""
Reports Module
Handles comprehensive report generation and statistics
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ReportsService:
    """Service for report generation and statistics"""

    @staticmethod
    def get_dashboard_statistics():
        """Get overall dashboard statistics"""
        try:
            with engine.connect() as conn:
                # Total students
                students_result = conn.execute(text("SELECT COUNT(*) FROM jclg_student")).fetchone()
                total_students = students_result[0] if students_result else 0
                
                # Analysed students (those with analysis records)
                analysed_result = conn.execute(text(
                    "SELECT COUNT(DISTINCT student_id) FROM jclg_ai_student_analysis"
                )).fetchone()
                analysed_students = analysed_result[0] if analysed_result else 0
                
                # High risk students
                high_risk_result = conn.execute(text(
                    "SELECT COUNT(*) FROM jclg_ai_student_analysis WHERE LOWER(risk_level) = 'high'"
                )).fetchone()
                high_risk = high_risk_result[0] if high_risk_result else 0
                
                # Improving students (from progress tracking)
                improving_result = conn.execute(text("""
                    WITH ranked_exams AS (
                        SELECT 
                            s.student_id,
                            ROUND(AVG(r.percentage), 2) as exam_avg,
                            ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY e.exam_date DESC) as rn
                        FROM jclg_student s
                        LEFT JOIN jclg_result r ON s.student_id = r.student_id
                        LEFT JOIN jclg_exam e ON r.exam_id = e.exam_id
                        GROUP BY s.student_id, e.exam_id
                    )
                    SELECT COUNT(DISTINCT student_id)
                    FROM ranked_exams
                    WHERE (SELECT exam_avg FROM ranked_exams r2 WHERE r2.student_id = ranked_exams.student_id AND r2.rn = 1)
                        > (SELECT exam_avg FROM ranked_exams r2 WHERE r2.student_id = ranked_exams.student_id AND r2.rn = 2)
                """)).fetchone()
                improving_students = improving_result[0] if improving_result else 0
                
                return {
                    "total_students": total_students,
                    "analysed_students": analysed_students,
                    "high_risk_students": high_risk,
                    "improving_students": improving_students,
                    "ai_insights_generated": analysed_students,  # Same as analysed
                    "percentage_analysed": round((analysed_students / total_students * 100) if total_students > 0 else 0, 2),
                }
        except Exception as e:
            print(f"Error fetching dashboard statistics: {e}")
            return None

    @staticmethod
    def get_high_risk_students(limit=10):
        """Get high risk students list"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        asa.student_id,
                        s.student_code,
                        s.class_name,
                        s.section,
                        asa.overall_score,
                        asa.performance_level,
                        asa.risk_level,
                        asa.generated_at
                    FROM jclg_ai_student_analysis asa
                    JOIN jclg_student s ON asa.student_id = s.student_id
                    WHERE LOWER(asa.risk_level) = 'high'
                    ORDER BY asa.overall_score ASC
                    LIMIT :limit
                """)
                results = conn.execute(query, {"limit": limit}).fetchall()
                
                students = []
                for row in results:
                    students.append({
                        "student_id": row[0],
                        "student_code": row[1],
                        "class_name": row[2],
                        "section": row[3],
                        "overall_score": float(row[4]) if row[4] else 0,
                        "performance_level": row[5],
                        "risk_level": row[6],
                        "generated_at": str(row[7]) if row[7] else None,
                    })
                return students
        except Exception as e:
            print(f"Error fetching high risk students: {e}")
            return []

    @staticmethod
    def get_analysed_students(limit=10):
        """Get recently analysed students"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        asa.analysis_id,
                        asa.student_id,
                        s.student_code,
                        s.class_name,
                        s.section,
                        asa.overall_score,
                        asa.performance_level,
                        asa.generated_at
                    FROM jclg_ai_student_analysis asa
                    JOIN jclg_student s ON asa.student_id = s.student_id
                    ORDER BY asa.generated_at DESC
                    LIMIT :limit
                """)
                results = conn.execute(query, {"limit": limit}).fetchall()
                
                students = []
                for row in results:
                    students.append({
                        "analysis_id": row[0],
                        "student_id": row[1],
                        "student_code": row[2],
                        "class_name": row[3],
                        "section": row[4],
                        "overall_score": float(row[5]) if row[5] else 0,
                        "performance_level": row[6],
                        "generated_at": str(row[7]) if row[7] else None,
                    })
                return students
        except Exception as e:
            print(f"Error fetching analysed students: {e}")
            return []

    @staticmethod
    def get_ai_insights_summary():
        """Get AI insights summary"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        COUNT(*) as total_insights,
                        COUNT(DISTINCT student_id) as unique_students,
                        ROUND(AVG(overall_score), 2) as average_score,
                        COUNT(CASE WHEN performance_level = 'Excellent' THEN 1 END) as excellent_count,
                        COUNT(CASE WHEN performance_level = 'Good' THEN 1 END) as good_count,
                        COUNT(CASE WHEN performance_level = 'Average' THEN 1 END) as average_count,
                        COUNT(CASE WHEN performance_level = 'Below Average' THEN 1 END) as below_average_count,
                        MAX(generated_at) as latest_analysis
                    FROM jclg_ai_student_analysis
                """)
                result = conn.execute(query).fetchone()
                
                return {
                    "total_insights": result[0] or 0,
                    "unique_students": result[1] or 0,
                    "average_score": float(result[2]) if result[2] else 0,
                    "performance_breakdown": {
                        "excellent": result[3] or 0,
                        "good": result[4] or 0,
                        "average": result[5] or 0,
                        "below_average": result[6] or 0,
                    },
                    "latest_analysis": str(result[7]) if result[7] else None,
                }
        except Exception as e:
            print(f"Error fetching AI insights: {e}")
            return None

    @staticmethod
    def generate_class_report(class_name):
        """Generate comprehensive report for a class"""
        try:
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        s.class_name,
                        COUNT(DISTINCT s.student_id) as total_students,
                        COUNT(DISTINCT asa.student_id) as analysed_students,
                        ROUND(AVG(r.percentage), 2) as average_percentage,
                        COUNT(DISTINCT CASE WHEN asa.risk_level = 'high' THEN asa.student_id END) as high_risk_count,
                        COUNT(DISTINCT CASE WHEN asa.performance_level = 'Excellent' THEN asa.student_id END) as excellent_count
                    FROM jclg_student s
                    LEFT JOIN jclg_result r ON s.student_id = r.student_id
                    LEFT JOIN jclg_ai_student_analysis asa ON s.student_id = asa.student_id
                    WHERE s.class_name = :class_name
                    GROUP BY s.class_name
                """)
                result = conn.execute(query, {"class_name": class_name}).fetchone()
                
                if result:
                    return {
                        "class_name": result[0],
                        "total_students": result[1] or 0,
                        "analysed_students": result[2] or 0,
                        "average_percentage": float(result[3]) if result[3] else 0,
                        "high_risk_count": result[4] or 0,
                        "excellent_count": result[5] or 0,
                    }
                return None
        except Exception as e:
            print(f"Error generating class report: {e}")
            return None
