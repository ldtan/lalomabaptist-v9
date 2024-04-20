from os import (
    environ,
    name as os_name,
)

from dotenv import load_dotenv

from app import create_app


load_dotenv('.flaskenv')
load_dotenv('instance/.env')

# Note:
# Redislite only works in Linux (posix) platforms and will throw an error
# when installed or ran in Windows (nt).
if os_name == 'posix':
    from redislite import Redis
    from redislite.client import RedisLiteException

    try:
        redis_db = Redis(environ.get('REDISLITE_PATH', None))
        environ['REDIS_URL'] = f"redis+socket://{redis_db.socket_file}"
    except RedisLiteException:
        redis_db = None
else:
    redis_db = None

flask_app = create_app(use_celery=False, session_redis=redis_db)
celery_app = flask_app.extensions.get('celery', None)

# Note:
# When running Celery on Windows OS, remember to add "--pool=solo" in the
# command line as Windows doesn't allow Celery to run mutliple
# threads/workers.
# 
# Example:
# celery -A wsgi.celery worker -l info --pool=solo

if __name__ == '__main__':
    flask_app.run()
