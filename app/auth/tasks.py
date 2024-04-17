import time
from typing import Dict

from celery import shared_task
from celery.contrib.abortable import AbortableTask


@shared_task(bind=True, base=AbortableTask)
def test(self, data):
    for ch in data['input']:
        print(ch)
        time.sleep(1)

        if self.is_aborted():
            return 'TASK STOPPED!'
    
    return 'Done!'
