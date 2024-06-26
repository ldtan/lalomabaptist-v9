from datetime import (
    date,
    datetime,
)
from os import (
    environ,
    path,
)
from typing import Optional

from flask import Flask
from flask_admin.menu import MenuLink
from flask_security import (
    SQLAlchemyUserDatastore,
    current_user,
)
from redis import Redis

from .core.localization import (
    now,
    render_datetime,
    to_user_timezone,
    to_utc,
    utcnow,
)
from .core.utils import register_module
from .core.tasks import celery_init_app


def create_app(
        session_redis: Optional[Redis] = None,
        use_celery: bool = False
    ) -> Flask:
    """Flask app factory."""

    debug = bool(environ.get('FLASK_DEBUG', 0))

    app = Flask(
        __name__,
        static_folder='static' if debug else None,
        template_folder='templates',
    )
    
    # Retrieve app configurations.
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
    admin.add_links(
        MenuLink('Log Out', '/auth/logout'),
        MenuLink('Exit Admin', '/'),
    )

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
    
    # Add additional context to templates.
    app.jinja_env.globals.update({
        'date': date,
        'datetime': datetime,
        'current_user': current_user,
        'now': now,
        'utcnow': utcnow,
        'render_datetime': render_datetime,
        'to_user_timezone': to_user_timezone,
        'to_utc': to_utc,
    })

    # Add middlewares.
    from . import middleware
    app.before_request(middleware.set_local_timezone)

    if use_celery:
        celery_init_app(app)

    return app
