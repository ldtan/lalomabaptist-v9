from os import environ


class Config:
    # Flask:
    SECRET_KEY = environ['SECRET_KEY']
    TEMPLATES_AUTO_RELOAD = True

    # SQLAlchemy:
    SQLALCHEMY_DATABASE_URI = environ['DB_URI']
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Session
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # Security:
    SECURITY_PASSWORD_HASH = environ['SECURITY_PASSWORD_HASH']
    SECURITY_PASSWORD_SALT = environ['SECURITY_PASSWORD_SALT']
    SECURITY_URL_PREFIX = '/auth'
    SECURITY_REGISTERABLE = False
    SECURITY_TRACKABLE = True
    SECURITY_USERNAME_ENABLE = True

    # CSRF:
    WTF_CSRF_SECRET_KEY = environ['WTF_CSRF_SECRET_KEY']
    WTF_CSRF_CHECK_DEFAULT = False

    # Admin:
    FLASK_ADMIN_FLUID_LAYOUT = True

    # Custom:
    SUSER_EMAIL = environ.get('SUSER_EMAIL', None)
    SUSER_USERNAME = environ.get('SUSER_USERNAME', None)
    SUSER_PASSWORD = environ.get('SUSER_PASSWORD', None)


class Production(Config):
    # Flask:
    DEBUG = False
    TESTING = False

    # SQLAlchemy:
    SQLALCHEMY_TRACK_MODIFICATIONS = True


class Development(Config):
    # Flask:
    DEBUG = True
    TESTING = True

    # SQLAlchemy:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery
    CELERY = dict(
        broker_url=environ.get('REDIS_URL', None),
        result_backend=environ.get('REDIS_URL', None),
        task_ignore_result=True,
    )
