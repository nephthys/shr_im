from newserializers import formatters
from django.utils.encoding import smart_unicode
from xml.etree import cElementTree as ET

class XmlFormatter(formatters.BaseFormatter):
    def start(self):
        self.root = ET.Element('objects')

    def end(self):
        self.data = ET.tostring(self.root, 'utf8')

    def format_element(self, parent, data):
        for k,v in data.items():
            el = ET.SubElement(parent, k)
            if isinstance(v, dict):
                self.format_element(el, v)
            elif isinstance(v, list) or isinstance(v, tuple):
                self.format_element(el, dict([('item', item) for item in v]))
            else:
                el.text = smart_unicode(v)

    def format(self, data):
        d = { data[0]: data[1] }
        self.format_element(self.root, d)

formatters.register('xml', XmlFormatter)
