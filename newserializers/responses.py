from django.http import HttpResponse
from newserializers import serialize

class SerializedResponse(HttpResponse):
    mimetype = None
    formatter = None
    def __init__(self, objs, method=None, *args, **kwargs):
        content = serialize(self.__class__.formatter,
            objs, method, *args, **kwargs)
        super(SerializedResponse, self).__init__(content,
            mimetype=self.__class__.mimetype)

class JsonResponse(SerializedResponse):
    mimetype = 'application/json'
    formatter = 'json'

class XmlResponse(SerializedResponse):
    mimetype = 'application/xml'
    formatter = 'xml'
