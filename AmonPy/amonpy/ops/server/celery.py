from __future__ import absolute_import

from celery import Celery

from amonpy.tools.config import AMON_CONFIG

name = AMON_CONFIG.get('rabbitmq','name')
password = AMON_CONFIG.get('rabbitmq','password')
vhost = AMON_CONFIG.get('rabbitmq','vhost')

if (name is not "") and (password is not "") and (vhost is not ""):
    Broker = 'amqp://%s:%s@localhost/%s'%(name,password,vhost)
    Backend = 'amqp://%s:%s@localhost/%s'%(name,password,vhost)
else:
    Broker = 'amqp://'
    Backend = 'amqp://'

app = Celery('server',
             broker=Broker,
             backend=Backend,
             include=['amonpy.ops.server.amon_server',
                      'amonpy.analyses.ICHAWC',
                      'amonpy.analyses.ICSwift'])

#app.conf.task_routes = {'amonpy.ops.server.amon_server.error_handler':{'queue':'default'},
                        #'amonpy.analyses.ICHAWC.ic_hawc':{'queue':'ic_hawc'},
                        #'amonpy.analyses.ICSwift.ic_swift':{'queue':'ic_swift'}}

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    BROKER_POOL_LIMIT = 1000,

)


if __name__ == '__main__':
    app.start()
