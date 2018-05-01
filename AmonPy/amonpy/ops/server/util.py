from datetime import datetime
import jsonpickle
class DatetimeHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return obj.strftime('%Y-%m-%dT%H:%M:%S.%f')
