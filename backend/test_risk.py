from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result3 = conn.execute(text("SELECT DISTINCT risk_level FROM jclg_ai_insight"))
    print('Risk levels:', [r[0] for r in result3])
    
    result2 = conn.execute(text("SELECT COUNT(*) FROM jclg_ai_insight WHERE LOWER(risk_level) = 'high'"))
    print('High risk (LOWER):', result2.fetchone()[0])
