# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import task

import time


@task
def report_test():
    print('test task start')
    time.sleep(60)
    print('test task finished.')
    result = {'status': 0, 'msg': 'Ok'}
    return result




