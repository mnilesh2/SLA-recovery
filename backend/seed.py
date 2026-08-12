from sqlalchemy.orm import Session
from .models import User
from .auth import get_password_hash


def seed_initial_data(db: Session):
    existing_admin = db.query(User).filter(User.username == "admin").first()
    if existing_admin:
        return

    admin_user = User(
        username="admin",
        hashed_password=get_password_hash("admin123"),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
