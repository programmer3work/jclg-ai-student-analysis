from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

inspector = inspect(engine)

# Check tables used by the current dashboard
for table_name in ['jclg_student', 'jclg_stream', 'jclg_group', 'jclg_result', 'jclg_marks', 'jclg_ai_insight']:
    print(f"\n{table_name}:")
    try:
        columns = inspector.get_columns(table_name)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Get row count
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
            count = result.fetchone()[0]
            print(f"  Row count: {count}")
    except Exception as e:
        print(f"  Error: {e}")
