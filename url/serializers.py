# -*- coding: utf-8 -*-
#
#    shr.im * just an URL shortener
#    Copyright (C) 2009 Camille Bouiller <aftercem@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from shr.url.models import *
import newserializers

class UrlSerializer(newserializers.BaseSerializer):
    def get_urls(self, obj, *args, **kwargs):
        domain_app = settings.SITE_URL
        data = { 
            'alias':        '%s/%s' % (domain_app, obj.url_min),
            'nb_clics':     obj.nb_clics,
            'domain':       obj.domain,
            'description':  obj.description,
            'title':        obj.title,
            'source':       obj.url_src,
        }
        return('url', data)
        
    def get_error(self, obj, *args, **kwargs):
        data = { 
            'error_id':         obj.id,
            'error_text':       obj.text,
        }
        return('query', data)
        
    def get_url_details(self, obj, *args, **kwargs):
        if obj.auteur:
            author_link = obj.auteur.username
        else:
            author_link = 'Guest'
        domain_app = settings.SITE_URL
        data = { 
            'alias':        '%s/%s' % (domain_app, obj.url_min),
            'domain':       obj.domain,
            'title':        obj.title,
            'description':  obj.description,
            'source':       obj.url_src,
            'user':  {
                'username': author_link,
            }
        }
        return('url', data)
        
newserializers.register(Url, UrlSerializer)	
