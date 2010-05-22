from newserializers import formatters
from django.utils import simplejson

from datetime import datetime

class JsonEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return simplejson.JSONEncoder.default(self, obj)

class JsonFormatter(formatters.BaseFormatter):
    def start(self):
        self.buffer = ['[']

    def end(self):
        self.buffer.pop() # remove last comma
        self.buffer.append(']')
        self.data = ''.join(self.buffer)

    def format(self, data):
        self.buffer.append(simplejson.dumps(data[1], cls=JsonEncoder))
        self.buffer.append(',') 

formatters.register('json', JsonFormatter)
