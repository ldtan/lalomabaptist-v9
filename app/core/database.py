from datetime import datetime
from typing import Union
import uuid as uuid_module

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Integer,
    Uuid,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class DbModel(DeclarativeBase):
    """The base model for all SQLAlchemy models."""

    @declared_attr
    def id(cls) -> Mapped[int]:
        for base in cls.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                type = ForeignKey(base.id)
                break
        else:
            type = Integer

        return mapped_column(type, primary_key=True)
    
    @classmethod
    def columns_and_relationships(cls, columns_only: bool = False,
                relationships_only: bool = False,
                exclude: Union[list, tuple] = tuple()):
        
        if columns_only:
            cols_rels = cls.__mapper__.columns
        elif relationships_only:
            cols_rels = cls.__mapper__.relationships
        
        return (cr for cr in cols_rels if cr.key not in exclude) if exclude else cols_rels
    

class UuidMixin:
    """Adds a 'uuid' column that generates a unique uuid on create."""

    @declared_attr
    def uuid(cls) -> Mapped[uuid_module.UUID]:
        return mapped_column(
            Uuid(as_uuid=True, native_uuid=True),
            nullable=False,
            unique=True,
            default=uuid_module.uuid4,
        )
    

class DateTimeTrackerMixin:
    """Add columns 'created_at' and 'updated_at' to track timestamps of when a
    record is created and updated.
    """
    
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
        )
    
    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
