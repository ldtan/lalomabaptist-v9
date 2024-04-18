from os import environ

from flask import Flask
from flask_security import SQLAlchemyUserDatastore
from flask_session import Session

from .core.utils import register_module
from .core.tasks import celery_init_app


def create_app(use_celery: bool = False) -> Flask:
    """Flask app factory."""

    app = Flask(__name__, static_folder=None, template_folder=None)

    # Retrieve app configurations.
    debug = bool(environ.get('FLASK_DEBUG', 0))
    app.config.from_object('config.Development' if debug \
            else 'config.Production')
    
    # Setup SQLAlchemy extension.
    from .extensions import db
    db.init_app(app)

    # Setup Migrate extension.
    from .extensions import migrate
    migrate.init_app(app, db)

    # Setup Session extension.
    Session(app)

    # Setup Babel extension.
    from .extensions import babel
    babel.init_app(app)

    # Setup Security extension.
    from .auth.models import Role, User
    from .extensions import security

    datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, datastore)

    # Setup Admin extension.
    from .extensions import admin
    admin.init_app(app)

    # Register modules.
    from . import auth
    register_module(app, auth, db.session, admin)

    if use_celery:
        celery_init_app(app)

    return app
