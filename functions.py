#-*- encoding: utf-8 -*-
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

from django.contrib.auth.models import User
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import ObjectDoesNotExist
from shr.oauthlogin.models import Account
import re
import string, random
import urllib2
from math import floor, log10
from BeautifulSoup import *

def generate_stats_line(values, dates, more_dates):
    max_value = max(values)
    
    if max_value >= 4:
        label_clics = '0|%d|%d|%d|%d' % (round(max_value/4), round(max_value/2), round(max_value/1.5), max_value)
    else:
        label_clics_list = []
        i = 0
        while i <= max_value:
            label_clics_list.append(i)
            i += 1
        label_clics = ('|'.join(map(str,label_clics_list)))

    img_graph  = 'http://chart.apis.google.com/chart?cht=lc&chm=B,e6f2fa,0,0.0,0.0&chco=0077cc&chs=640x220&chxt=x,x,y&'
    img_graph += 'chd=t:%s&' % (','.join(map(str,values)))
    img_graph += 'chds=0,%s&' % (max_value)
    img_graph += 'chxl=0:|%s|' % ('|'.join(map(str,dates)))
    img_graph += '1:|%s|' % (more_dates)
    img_graph += '2:|%s' % (label_clics)
    
    return img_graph
    
def is_bot_or_crawler(user_agent, ip):
    exclude_ips = ['70.37.71.','70.37.92.','70.32.121.','174.129.175.212','174.133.61.66']
    list_robots = ['libwww-perl','google','mozzler','commons-httpclient','fetcher','twitt','topsy','twingly','postrank','pycurl','tweet','cozop','urllib','bot','scooter','slurp','voila','wisenut','fast','index','teoma','mirago','search','find','loader','archive','spider','crawler']
    
    if len(user_agent) == 0:
        return True
        
    for bot in list_robots:
        if bot in str(user_agent.lower()):
            return True
    
    for ip_bot in exclude_ips:
        if ip.startswith(ip_bot):
            return True
 
    return False
   
def get_list_page(request,obj_list,parPage,nb=3):
	paginator = Paginator(obj_list, parPage)
	try:
		page = int(request.GET.get('p', '1'))
	except ValueError:
		page = 1
	try:
		obj = paginator.page(page)
	except (EmptyPage, InvalidPage):
		obj = paginator.page(1)
		page = 1
	nb_page = paginator.num_pages
	list_page = []
	i = 1
	while i <= nb_page:
		cond = i < page + nb and i > page - nb
		if i < nb or i > nb_page - nb or cond:
			list_page.append(i)
		else:
			if (i >= nb and i <= page - nb):
				i = page - nb
			elif (i >= page + nb and i <= nb_page - nb):
				i = nb_page - nb
			list_page.append('...')
		
		i += 1
	return list_page, page, obj.object_list
    
def makePassword(minlength=5,maxlength=25):
    length=random.randint(minlength,maxlength)
    letters=string.ascii_letters+string.digits # alphanumeric, upper and lowercase
    return ''.join([random.choice(letters) for _ in range(length)])

def extractDataFromUrl(url):
    maxlength= 1*1024*1024
    headers = {}
    headers['User-Agent'] = 'shr.im automatic fetcher (Mozilla/5.0 compatible)'
    req = urllib2.Request(url, None, headers)
    try:
        requete = urllib2.urlopen(req)
        heads_req = requete.info().getheader('Content-Type','')
        content_type = heads_req.split(';')[0].strip()
        encoding = heads_req.split('charset=')[-1]
        
        if not content_type.startswith('text/') and not content_type.startswith('image/'):
            requete.close()
            return None
        
        try:
            length_url = int(requete.info().getheader('Content-Length', '0'))
        except ValueError:
            length_url = 0
        
        if length_url > maxlength:
            return None
        
        page = requete.read()
    except urllib2.URLError:
        return None
        
    soup_base = BeautifulSoup(page, parseOnlyThese=SoupStrainer('head')).prettify()
    soup = BeautifulStoneSoup(soup_base, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
    try:
        match_title = soup.head.title.string
    except:
        match_title = 'Unnamed title'
            
    match_description = ''
        
    for meta in soup.findAll('meta'):
        if 'description' == meta.get('name', '').lower():
            match_description = meta['content']
            break
                
    return {'title': match_title.strip(), 'description': match_description.strip()}

    
def extractDataFromUrl4(url):
    charset = 'utf-8'  
    data = ''
    match_title = ''
    try:
        req = urllib2.Request(url)   
        response = urllib2.urlopen(req)   
        data = response.read()   
        info = response.info()   
        ignore, charset = info['Content-Type'].split('charset=') 
        match_description = data
    except:
        match_description = data.decode(charset).encode('utf-8')
                
    return {'title': match_title, 'description': match_description}
            
def alphaID(input, to_num=False, pad_up=-1):
    index_chars = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base  = len(index_chars)
	
    if to_num:
        # Digital number  <<--  alphabet letter code
        input, length = (input[::1], len(input) - 1)
        out = 0
			
        for index, value in enumerate(input):
            bcpow = base ** (length - index)
            out += index_chars.find(value) * bcpow

        if not pad_up == -1:
            pad_up -= 1
				
        if pad_up > 0:
            out -= base ** pad_up
    else:
        # Digital number  -->>  alphabet letter code
        if not pad_up == -1:
            pad_up -= 1
				
        if pad_up > 0:
            input +=  base ** pad_up

        out, i = ('', int(floor(log10(input) / log10(base))))
			
        while i >= 0:
            a = int(floor(input / (base ** i)))
            out += index_chars[a]
            input -= a * (base ** i)
            i -= 1
			
        return out
