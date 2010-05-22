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

from shr.url.models import *
from django.contrib import admin

class UrlAdmin(admin.ModelAdmin):
    list_display = ('title', 'url_min', 'pub_date', 'ip_post', 'auteur', 'nb_clics', 'is_private', 'country')
    search_fields = ('url_src', 'url_min', 'auteur', 'ip_post')
    date_hierarchy = ('pub_date')
    list_filter = ('pub_date', 'ip_post', 'is_private')

class ClicAdmin(admin.ModelAdmin):
    list_display = ('url', 'pub_date', 'ip_post', 'referer', 'country')
    search_fields = ('url', 'referer', 'country')
    date_hierarchy = ('pub_date')
    
class APIAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'etat', 'nb_rqt', 'last_ip', 'date_propose', 'last_date')
    search_fields = ('auteur', 'cle')
    date_hierarchy = ('last_date')
    list_filter = ('etat', 'last_date')

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'int', 'nb_clics', 'nb_links')
    
class GeolocAdmin(admin.ModelAdmin):
    list_display = ('link', 'country', 'nb_clics')
    
admin.site.register(Url, UrlAdmin)
admin.site.register(Clic, ClicAdmin)
admin.site.register(API, APIAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Geoloc, GeolocAdmin)
