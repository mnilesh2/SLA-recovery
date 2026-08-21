"""
Database Seeding
Initialize database with default users and data on first run
"""

import logging
from sqlalchemy.orm import Session

from .models import User
from .auth import create_user

logger = logging.getLogger(__name__)

DEFAULT_USERS = [
    {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",
        "role": "admin"
    },
    {
        "username": "approver",
        "email": "approver@example.com",
        "password": "approver123",
        "role": "approver"
    },
    {
        "username": "reviewer",
        "email": "reviewer@example.com",
        "password": "reviewer123",
        "role": "reviewer"
    }
]


def seed_initial_data(db: Session):
    """Seed database with initial data if not already present"""
    try:
        from .auth import hash_password

        # Create or update default users
        for user_data in DEFAULT_USERS:
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()

            if existing_user:
                # Update password and role for existing users
                existing_user.hashed_password = hash_password(user_data["password"])
                existing_user.role = user_data["role"]
                db.commit()
                logger.info(f"Updated default user: {existing_user.username}")
            else:
                # Create new user
                user = create_user(
                    db,
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"]
                )
                logger.info(f"Created default user: {user.username}")

        logger.info("Database seeding completed successfully")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        raise
