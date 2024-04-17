from typing import (
    Iterable,
    Tuple,
)
from enum import Enum


# Default Group Names:
ANONYMOUS = 'Anonymous'
AUTHENTICATED = 'Authenticated'

# Default Role Names:
SUPER_USER = 'Super User'
CREATOR = 'Creator'
EDITOR = 'Editor'
CONTRIBUTOR = 'Contributor'
READER = 'Reader'


class Permission(Enum):

    FULL_CONTROL: str = 'Full Control'

    CREATE_RECORD: str = 'Create Record'
    READ_RECORD: str = 'Read Record'
    EDIT_RECORD: str = 'Edit Record'
    DELETE_RECORD: str = 'Delete Record'
    
    CREATE_ACCESS: str = 'Create Access'
    ASSIGN_ACCESS: str = 'Assign Access'
    READ_ACCESS: str = 'Read Access'
    EDIT_ACCESS: str = 'Edit Access'
    DELETE_ACCESS: str = 'Delete Access'

    @classmethod
    def items(cls) -> Iterable[Tuple]:
        return [(const.name, const.value) for const in cls]
    
    @classmethod
    def names(cls) -> Iterable[str]:
        return [const.name for const in cls]
    
    @classmethod
    def values(cls) -> Iterable[str]:
        return [const.value for const in cls]
