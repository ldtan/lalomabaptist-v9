from os import environ
from typing import Optional

from flask import Flask
from flask_security import SQLAlchemyUserDatastore
from redis import Redis

from .core.utils import register_module
from .core.tasks import celery_init_app


def create_app(
        session_redis: Optional[Redis] = None,
        use_celery: bool = False
    ) -> Flask:
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
    from .extensions import session

    if session_redis:
        app.config.update({
            'SESSION_TYPE': 'redis',
            'SESSION_REDIS': session_redis,
        })
    else:
        app.config.update({
            'SESSION_TYPE': 'sqlalchemy',
            'SESSION_SQLALCHEMY': db,
            'SESSION_SQLALCHEMY_TABLE': 'sessions',
        })

    session.init_app(app)

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
    from . import (
        auth,
        base,
    )

    bp_modules = (
        auth,
        base,
    )
    [register_module(app, bpm, db.session, admin)
            for bpm in bp_modules]

    if use_celery:
        celery_init_app(app)

    return app
