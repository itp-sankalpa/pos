"""Authentication controller — bridges the UI and auth_service layer."""

import logging
from typing import Optional

from services.auth_service import login as _login
from models.user import User

logger = logging.getLogger(__name__)


class AuthController:
    """Manages authentication state and delegates to auth_service."""

    # Class-level attribute so all instances (and the module) share the same user
    _current_user: Optional[User] = None

    def __init__(self):
        """No-argument constructor. State is held on the class attribute."""
        pass

    # ── Authentication ──────────────────────────────────────────────

    def login(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user and set the current session user on success.

        Returns the User object on success, or None on failure.
        """
        user = _login(username, password)
        if user is not None:
            self.set_current_user(user)
            logger.info("User '%s' logged in successfully.", username)
        else:
            logger.warning("Login failed for username '%s'.", username)
        return user

    # ── Session management ──────────────────────────────────────────

    def get_current_user(self) -> Optional[User]:
        """Return the currently authenticated user, or None if not logged in."""
        return self._current_user

    def set_current_user(self, user: Optional[User]) -> None:
        """Set (or clear) the currently authenticated user."""
        AuthController._current_user = user

    def logout(self) -> None:
        """Clear the current session user."""
        previous = self._current_user
        AuthController._current_user = None
        if previous is not None:
            logger.info("User '%s' logged out.", previous.username)
