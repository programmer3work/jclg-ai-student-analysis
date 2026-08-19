"""
Populate sample data for testing dashboard statistics
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def populate_sample_data():
    """Add sample analysis data for dashboard statistics"""
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            # Get existing students
            students_result = conn.execute(
                text("SELECT student_id FROM jclg_student LIMIT 5")
            )
            student_ids = [row[0] for row in students_result]
            
            if not student_ids:
                print("No students found in database!")
                trans.rollback()
                return
            
            print(f"Found {len(student_ids)} students")
            
            # Check if analysis data already exists
            existing = conn.execute(
                text("SELECT COUNT(*) FROM jclg_ai_student_analysis")
            ).fetchone()
            
            existing_count = existing[0] if existing else 0
            print(f"Existing analysis records: {existing_count}")
            
            if existing_count >= 5:
                print("Sample data already populated!")
                trans.commit()
                return
            
            # Insert analysis data
            analysis_sql = """
                INSERT INTO jclg_ai_student_analysis
                (student_id, overall_score, performance_level, strengths, weaknesses, 
                 learning_gaps, recommendations, risk_level, generated_at)
                VALUES (:student_id, :overall_score, :performance_level, :strengths, 
                        :weaknesses, :learning_gaps, :recommendations, :risk_level, :generated_at)
                ON CONFLICT DO NOTHING
            """
            
            for i, student_id in enumerate(student_ids):
                # Vary the data for each student
                if i == 0:
                    score, level, risk = 92.5, "Excellent", "low"
                elif i == 1:
                    score, level, risk = 45.0, "Below Average", "high"
                elif i == 2:
                    score, level, risk = 78.5, "Good", "medium"
                elif i == 3:
                    score, level, risk = 62.0, "Average", "medium"
                else:
                    score, level, risk = 88.0, "Excellent", "low"
                
                conn.execute(
                    text(analysis_sql),
                    {
                        "student_id": student_id,
                        "overall_score": score,
                        "performance_level": level,
                        "strengths": "Strong in mathematics and logical reasoning",
                        "weaknesses": "Needs improvement in language subjects",
                        "learning_gaps": "Grammar and vocabulary",
                        "recommendations": "Practice daily and take extra tuition",
                        "risk_level": risk,
                        "generated_at": datetime.now() - timedelta(days=random.randint(1, 7))
                    }
                )
            
            # Insert subject analysis for the first 2 students
            subject_analysis_sql = """
                INSERT INTO jclg_ai_subject_analysis
                (analysis_id, subject_id, average_percentage, performance_level, 
                 strengths, weaknesses, recommendations)
                SELECT 
                    a.analysis_id, 
                    s.subject_id,
                    :avg_percentage,
                    :perf_level,
                    :strengths,
                    :weaknesses,
                    :recommendations
                FROM jclg_ai_student_analysis a, jclg_subject s
                WHERE a.student_id = :student_id
                AND s.subject_id IN (1, 2)
                ON CONFLICT DO NOTHING
            """
            
            for student_id in student_ids[:2]:
                for perf_data in [
                    {"avg": 85.0, "level": "Excellent", "str": "Good concept clarity", "weak": "Speed", "rec": "Practice more"},
                    {"avg": 72.0, "level": "Good", "str": "Regular practice", "weak": "Applications", "rec": "Work on applications"}
                ]:
                    conn.execute(
                        text(subject_analysis_sql),
                        {
                            "student_id": student_id,
                            "avg_percentage": perf_data["avg"],
                            "perf_level": perf_data["level"],
                            "strengths": perf_data["str"],
                            "weaknesses": perf_data["weak"],
                            "recommendations": perf_data["rec"]
                        }
                    )
            
            trans.commit()
            print("Sample data populated successfully!")
            
            # Display statistics
            count = conn.execute(
                text("SELECT COUNT(*) FROM jclg_ai_student_analysis")
            ).fetchone()
            print(f"Total analysis records: {count[0]}")
            
    except Exception as e:
        print(f"Error populating data: {e}")
        if trans:
            trans.rollback()


if __name__ == "__main__":
    populate_sample_data()
