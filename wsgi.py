from os import environ

from dotenv import load_dotenv
from redislite import Redis

from app import create_app


load_dotenv('.flaskenv')
load_dotenv('instance/.env')

redis_db = Redis(environ.get('REDISLITE_PATH', None))
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
