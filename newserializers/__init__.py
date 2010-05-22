from inspect import isclass
from formatters import *
from formatters.json_formatter import *
from formatters.xml_formatter import *

class BaseSerializer(object):
    def default(self, obj):
        return (obj.__class__.__name__.lower(),
            obj.__dict__)

_serializers_register = {}
_default_serializer = BaseSerializer()

def serialize(format, objs, method=None, out=None, *args, **kwargs):
    fmt = formatter(format)(out=out)
    fmt.start()
    for obj in objs:
        fmt.format(serialization(obj, method, *args, **kwargs))
    fmt.end()
    return fmt.get()

def register(objclass, serializer):
    if not isclass(serializer):
        raise TypeError('Serializer must be a BaseSerializer-derived class')
    if not issubclass(serializer, BaseSerializer):
        raise TypeError('Class "%s" is not a serializer' % serializer.__name__)
    _serializers_register[objclass.__name__] = serializer()

def serialization(obj, method=None, *args, **kwargs):
    try:
        ser = _serializers_register[obj.__class__.__name__]
    except KeyError:
        ser = _default_serializer
    try:
        m = getattr(ser, method or 'default')
    except AttributeError:
        raise RuntimeError('Serialization "%s" is not defined in serializer "%s" for object "%s"' % \
            (method, ser.__class__.__name__, obj.__class__.__name__))
    
    return m(obj, *args, **kwargs) 

