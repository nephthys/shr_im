#!/usr/bin/env python
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

# Autoload serializers
from django.template import loader
from django.conf import settings
from serializers import *

template_cache = {} 
original_get_template = loader.get_template
def cached_get_template(template_name):
    global template_cache
    t = template_cache.get(template_name,None)
    if not t or settings.DEBUG:
        template_cache[template_name] = t = original_get_template(template_name)
    return t
loader.get_template = cached_get_template
