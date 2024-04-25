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
)
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.orm import Session


BASE_DIR: str = path.abspath(path.dirname(path.dirname(path.dirname(__file__))))


def isclass(var: Any) -> bool:
    """Returns True if var is a class type, else False."""

    return isinstance(var, type)

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
