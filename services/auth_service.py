"""Authentication and user management service."""

import logging
from typing import Optional, List

import bcrypt
from sqlalchemy import select

from database import SessionContext
from models.user import User
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt and return the UTF-8 decoded hash."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def login(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Returns the User object on success, or None on failure.
    Only active users can log in.
    """
    try:
        with SessionContext() as session:
            stmt = select(User).where(
                User.username == username,
                User.is_active == True,  # noqa: E712
            )
            user = session.execute(stmt).scalar_one_or_none()
            if user is None:
                logger.warning("Login failed: user '%s' not found or inactive.", username)
                return None

            if not _verify_password(password, user.password_hash):
                logger.warning("Login failed: incorrect password for user '%s'.", username)
                return None

            # Detach the object so it remains accessible after session closes
            session.expunge(user)
            return user

    except Exception:
        logger.exception("Unexpected error during login for user '%s'.", username)
        return None


def create_user(
    username: str,
    password: str,
    full_name: str,
    role: str = "CASHIER",
) -> Optional[User]:
    """
    Create a new user with a bcrypt-hashed password.

    Returns the created User object, or None on error (e.g. duplicate username).
    """
    try:
        with SessionContext() as session:
            # Check for duplicate username
            existing = session.execute(
                select(User).where(User.username == username)
            ).scalar_one_or_none()
            if existing is not None:
                logger.warning("Cannot create user: username '%s' already exists.", username)
                return None

            user = User(
                username=username,
                password_hash=_hash_password(password),
                full_name=full_name,
                role=role,
            )
            session.add(user)
            session.flush()  # populate id
            session.expunge(user)
            return user

    except Exception:
        logger.exception("Error creating user '%s'.", username)
        return None


def change_password(user_id: int, new_password: str) -> bool:
    """
    Update the password hash for the given user.

    Returns True on success, False on error.
    """
    try:
        with SessionContext() as session:
            user = session.get(User, user_id)
            if user is None:
                logger.warning("Cannot change password: user id %d not found.", user_id)
                return False

            user.password_hash = _hash_password(new_password)
            return True

    except Exception:
        logger.exception("Error changing password for user id %d.", user_id)
        return False


def get_all_users() -> List[User]:
    """Return a list of all users (including inactive ones)."""
    try:
        with SessionContext() as session:
            stmt = select(User).order_by(User.id)
            users = list(session.execute(stmt).scalars().all())
            for u in users:
                session.expunge(u)
            return users

    except Exception:
        logger.exception("Error fetching all users.")
        return []


def get_user_by_id(user_id: int) -> Optional[User]:
    """Return a User by primary key, or None if not found."""
    try:
        with SessionContext() as session:
            user = session.get(User, user_id)
            if user is not None:
                session.expunge(user)
            return user

    except Exception:
        logger.exception("Error fetching user id %d.", user_id)
        return None


def seed_admin() -> Optional[User]:
    """
    Create the default admin user if no users exist in the database.

    Uses credentials from config: DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_PASSWORD.
    Returns the created User, the existing admin, or None on error.
    """
    try:
        with SessionContext() as session:
            user_count = session.execute(
                select(User)
            ).scalars().first()

            if user_count is not None:
                logger.info("Users already exist — skipping admin seed.")
                return None

            admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=_hash_password(DEFAULT_ADMIN_PASSWORD),
                full_name="Administrator",
                role="ADMIN",
            )
            session.add(admin)
            session.flush()
            session.expunge(admin)
            logger.info("Default admin user seeded (username='%s').", DEFAULT_ADMIN_USERNAME)
            return admin

    except Exception:
        logger.exception("Error seeding admin user.")
        return None
