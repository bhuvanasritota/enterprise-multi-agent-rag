import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.entities import User, UserRole
email=os.getenv("ADMIN_EMAIL","admin@example.com").lower(); password=os.getenv("ADMIN_PASSWORD","")
if len(password)<12: raise SystemExit("Set ADMIN_PASSWORD to at least 12 characters")
with SessionLocal() as db:
    user=db.scalar(select(User).where(User.email==email))
    if user: user.role=UserRole.ADMIN; user.hashed_password=hash_password(password)
    else: db.add(User(email=email,hashed_password=hash_password(password),role=UserRole.ADMIN))
    db.commit(); print(f"Admin ready: {email}")
