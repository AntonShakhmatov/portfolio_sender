from common.database import engine, text

with engine.connect() as conn:
    rows = conn.excute(text("SELECT * FROM profile_skills WHERE id=:uid"), {"uid": 3}).mappings().all()
    print(rows)