from datetime import datetime
from os import path
from types import ModuleType
from typing import (
    Any,
    Optional,
    Union,
)

from flask import (
    Blueprint,
    Flask,
    session,
)
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from pytz import timezone
from sqlalchemy.orm import Session
import pytz


BASE_DIR: str = path.abspath(path.dirname(path.dirname(path.dirname(__file__))))


def isclass(var: Any) -> bool:
    """Returns True if var is a class type, else False."""

    return isinstance(var, type)

def utcnow() -> datetime:
    return datetime.now(timezone('UTC'))

def convert_to_local_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone('UTC'))

    tz = session.get('tz', 'UTC')
    return dt.astimezone(timezone(tz))

def render_datetime(
        dt: datetime,
        format: str = '%Y-%m-%d %H:%M:%S %Z%z'
    ) -> str:

    local_dt = convert_to_local_datetime(dt)
    return local_dt.strftime(format)

def register_module(app: Flask, module: ModuleType,
        db_session: Optional[Session] = None, admin: Optional[Admin] = None):
    
    if not hasattr(module, 'create_blueprint'):
        raise AttributeError('attribute `create_blueprint` is not found')
    
    module_bp: Blueprint = module.create_blueprint()
    app.register_blueprint(module_bp)

    if hasattr(module_bp, 'admin_views') and admin and db_session:
        for admin_view in module_bp.admin_views:
            if isclass(admin_view) and issubclass(admin_view, ModelView):
                admin_view = admin_view(session=db_session, category=module_bp.name)

            if isinstance(admin_view, ModelView):
                admin.add_view(admin_view)

    if hasattr(module, 'prepare_blueprint'):
        with app.app_context():
            module.prepare_blueprint()

def exclude(collection: Union[list, tuple], items: Union[list, tuple]):
    """Exlclude items from a list."""
    
    CollectionClass = type(collection)
    return CollectionClass(item for item in collection if item not in items)
