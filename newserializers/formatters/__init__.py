from inspect import isclass
from cStringIO import StringIO

_formatters_register = {}

class BaseFormatter(object):
    def __init__(self, *args, **kwargs):
        self.data = ''
        self.out = kwargs.get('out')

    def start(self):
        raise NotImplementedError

    def end(self):
        raise NotImplementedError

    def get(self):
        if self.out:
            self.out.write(self.data)
            return self.out

        return self.data

    def format(self, data):
        raise NotImplementedError

def register(format_name, formatter):
    if not isclass(formatter):
        raise TypeError('Formatter must be a BaseFormatter-derived class')
    if not issubclass(formatter, BaseFormatter):
        raise TypeError('Class "%s" is not a formatter' % formatter.__name__)
    _formatters_register[format_name] = formatter

def formatter(format):
    try:
        return _formatters_register[format]
    except KeyError:
        raise RuntimeError('No formatter registered for format "%s"' % format)

