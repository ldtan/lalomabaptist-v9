from typing import Optional

from flask_security import current_user


def current_user_id() -> Optional[int]:
    """Gets the ID of the current logged in user. Returns None if user
    is anonymous.
    """

    return current_user.id if current_user \
            and current_user.is_authenticated else None

def is_current_user_super() -> bool:
    """Returns True if the current logged in user has a Super User role,
    else False.
    """
    
    return getattr(current_user, 'is_super_user', False)
