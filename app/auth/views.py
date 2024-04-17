from .tasks import test

def index():
    from flask import jsonify
    from flask_security import current_user

    return jsonify({
        'current_user': str(current_user),
    })

def start_task():
    from flask import jsonify

    data = {'input': 'Hello World!'}
    task = test.delay(data)

    return 'Task Started'

def get_task(id: str):
    from flask import jsonify
    from celery.result import AsyncResult

    result = AsyncResult(id)
    
    return jsonify({
        'ready': result.ready(),
        'successful': result.successful(),
        'value': result.result if result.ready() else None,
    })
