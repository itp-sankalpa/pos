"""Staff controller — bridges the UI and auth_service for staff management."""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select

from database import SessionContext
from models.user import User
from services.auth_service import (
    get_all_users,
    create_user,
    change_password,
    get_user_by_id,
)

logger = logging.getLogger(__name__)


class StaffController:
    """Delegates staff (user) management operations to auth_service.

    For operations not available in auth_service (update_user, toggle_active),
    the controller interacts with the database session directly.
    """

    def __init__(self):
        """No-argument constructor."""
        pass

    # ── Read operations ─────────────────────────────────────────────

    def get_all_staff(self) -> List[User]:
        """Return a list of all users (including inactive ones)."""
        return get_all_users()

    # ── Write operations ────────────────────────────────────────────

    def create_staff(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str = "CASHIER",
    ) -> Optional[User]:
        """Create a new staff user with a bcrypt-hashed password.

        Returns the created User, or None on error (e.g. duplicate username).
        """
        return create_user(
            username=username,
            password=password,
            full_name=full_name,
            role=role,
        )

    def update_staff(self, staff_id: int, **kwargs) -> Optional[User]:
        """Update a staff member's fields.

        Accepted kwargs: full_name, role, is_active.
        Returns the updated User, or None on error.
        """
        try:
            with SessionContext() as session:
                user = session.get(User, staff_id)
                if user is None:
                    logger.warning(
                        "Cannot update staff: user id %d not found.", staff_id
                    )
                    return None

                allowed_fields = {"full_name", "role", "is_active"}
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        setattr(user, key, value)
                    else:
                        logger.warning(
                            "Ignoring unknown field '%s' in staff update.", key
                        )

                user.updated_at = datetime.utcnow()
                session.flush()
                session.expunge(user)
                return user

        except Exception:
            logger.exception("Error updating staff id %d.", staff_id)
            return None

    def change_password(self, staff_id: int, new_password: str) -> bool:
        """Update the password hash for the given staff member.

        Returns True on success, False on error.
        """
        return change_password(staff_id, new_password)

    def toggle_active(self, staff_id: int) -> Optional[User]:
        """Toggle the is_active flag for the given staff member.

        Returns the updated User, or None on error.
        """
        try:
            with SessionContext() as session:
                user = session.get(User, staff_id)
                if user is None:
                    logger.warning(
                        "Cannot toggle active: user id %d not found.", staff_id
                    )
                    return None

                user.is_active = not user.is_active
                user.updated_at = datetime.utcnow()
                session.flush()
                session.expunge(user)

                logger.info(
                    "Toggled is_active for user '%s' (id=%d) to %s.",
                    user.username,
                    user.id,
                    user.is_active,
                )
                return user

        except Exception:
            logger.exception("Error toggling active for staff id %d.", staff_id)
            return None
