from __future__ import absolute_import

from celery import Celery

app = Celery('analyser',
             broker='amqp://',
             backend='amqp://',
             include=['analyser.runanal'])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
  #  CELERY_TASK_SERIALIZER='json',
   # CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    #CELERY_RESULT_SERIALIZER='json',
)

if __name__ == '__main__':
    app.start()