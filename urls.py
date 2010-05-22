# -*- coding: utf-8 -*-
#
#    shr.im * just an URL shortener
#    Copyright (C) 2009 Camille Bouiller <aftercem@gmail.com>
#    Copyright (C) 2009 Rémy Hubscher <natim@users.sf.net>
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
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'shr.url.views.homepage'),
    (r'^login/?$', 'shr.oauthlogin.views.connection'),
    (r'^login/callback/?$', 'shr.oauthlogin.views.callback'),
    (r'^logout/?$', 'shr.oauthlogin.views.disconnect'),
    (r'^api/?$', 'shr.url.views.view_doc_api'),
    (r'^tools/?$', 'shr.url.views.view_tools'),
    (r'^contact/?$', 'shr.url.views.contact'),
    (r'^api/1.0/(?P<function>[-\w]+)$', 'shr.url.views.justAPIv1'),
    (r'^api/1.0/(?P<function>[-\w]+).(?P<format_output>[-\w]+)$', 'shr.url.views.justAPIv1'),
    (r'^ajax/(?P<function>[-\w]+)$', 'shr.url.views.ajax_pages'),
    (r'^timeline/?$', 'shr.url.views.urls_timeline'),
    (r'^popular/?$', 'shr.url.views.urls_popular'),
    (r'^s/(?P<alias>.*)/$', 'shr.url.views.view_fiche'),
    (r'^c/(?P<alias>.*)/$', 'shr.url.views.view_clics'),
    (r'^u/(?P<url>.*)/$', 'shr.url.views.view_user'),
    (r'^d/(?P<url>.*)/$', 'shr.url.views.view_domain'),
    (r'^del/(?P<alias>.*)/$', 'shr.url.views.delete'),
    (r'^admin/(.*)', admin.site.root),
    (r'^(?P<alias>.*)/$', 'shr.url.views.redir'),
)

if settings.DEBUG:
	urlpatterns += patterns('',(r'^/site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
	(r'^upload/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
	(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),)
