from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    total = conn.execute(text("SELECT COUNT(*) FROM jclg_student")).fetchone()[0]
    analysed = conn.execute(text("SELECT COUNT(*) FROM jclg_ai_student_analysis")).fetchone()[0]
    high = conn.execute(text("SELECT COUNT(*) FROM jclg_ai_student_analysis WHERE risk_level = 'High' OR risk_level = 'high' OR risk_level = 'HIGH' OR risk_level = 'High '" )).fetchone()[0]
    print('TOTAL', total)
    print('ANALYSED', analysed)
    print('HIGH', high)
    print('RISK_VALUES', [row[0] for row in conn.execute(text("SELECT DISTINCT risk_level FROM jclg_ai_student_analysis"))])
