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

from .core.utils import (
    convert_to_local_datetime,
    register_module,
    render_datetime,
    BASE_DIR,
)
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
    admin.add_link(MenuLink('Log Out', '/auth/logout'))

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
        'convert_to_local_datetime': convert_to_local_datetime,
        'current_user': current_user,
        'render_datetime': render_datetime,
    })

    # Add middlewares.
    from . import middleware
    app.before_request(middleware.set_tz)

    if use_celery:
        celery_init_app(app)

    return app
