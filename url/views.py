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

from django.core import serializers
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.db.models import Sum, Avg
from django.utils import dateformat
from django.views.decorators.cache import cache_page
from datetime import datetime, timedelta
from shr.url.models import *
from shr.functions import *
from newserializers.responses import JsonResponse, XmlResponse
from urlparse import urlparse
from collections import defaultdict
import string, random
import urllib2
import re

# Use GeoIP (C/Python implementation) if available, then fallback to
# pygeoip (pure Python implementation)
try:
    import GeoIP as geoip
except ImportError:
    try:
        import pygeoip as geoip
    except ImportError:
        # Neither GeoIP/pygeoip installed, display a clean error
        raise ImportError(
                "Unable to find a Python GeoIP module. Please install GeoIP ("
                "http://www.maxmind.com/app/python) or pygeoip ("
                "http://code.google.com/p/pygeoip/)."
        )

def homepage(request):
    get_urls = request.GET.get('url_src', '')
    type_request = 'POST'
    data_request = request.POST
    list_urls = None
    
    if get_urls:
        type_request = 'GET'
        data_request = request.GET
    
    if request.method == type_request:
        form = UrlForm(data_request)
        if form.is_valid():
            new_url = form.save(commit=False)
            data_url = extractDataFromUrl(form.cleaned_data['url_src'])
            
            if not data_url:
                return HttpResponseRedirect('/?msg=12')
            
            new_url.domain = urlparse(form.cleaned_data['url_src']).netloc
            new_url.title = data_url['title'][0:200]
            new_url.description = data_url['description'][0:300]
            new_url.ip_post = request.META['REMOTE_ADDR']
            
            # Try to get an alias...
            if not form.cleaned_data['url_min']:
                alias_url = makePassword(3,4)
                try:
                    link = Url.objects.get(url_min=alias_url)
                    rand_numb = random.randint(0,9)
                    new_alias = '%s%s' % (makePassword(3,4), rand_numb)
                except Url.DoesNotExist:
                    new_alias = alias_url
                    
                new_url.url_min = alias_url
                
            # Géolocalisation des urls
            gi = geoip.GeoIP('%sGeoIP.dat' % (settings.STATIC_ROOT))
            country_data = gi.country_name_by_name(request.META['REMOTE_ADDR'])
        
            if country_data:
                try:
                    my_country = Country.objects.get(name=country_data)
                except Country.DoesNotExist:
                    my_country = Country(name=country_data, int=country_data)
                    my_country.save()
                my_country.nb_links += 1
                my_country.save()
                new_url.country = my_country
                
            if not request.user.is_anonymous():
                new_url.auteur = request.user
                
            new_url.save()
            return HttpResponseRedirect('/s/%s/?new' % (new_url.url_min))
    else:
        form = UrlForm()

    ctx = {}
    show_page = False
    separateur = '...'
    if request.user.is_authenticated():
        NB_LINKS = 5
        list_urls = Url.objects.filter(auteur=request.user).order_by('-pub_date')
        nb_links = list_urls.count()
        list_page, page, list_urls = get_list_page(request, list_urls, NB_LINKS)
        if nb_links > NB_LINKS:
            show_page = True

        # Copy the defined variables into the template context
        ctx.update(list_urls=list_urls,
                   nb_links=nb_links,
                   list_page=list_page,
                   page=page)

    num_msg = int(request.GET.get('msg', 0))

    # Define the common variables in the context
    ctx.update(request=request,
               form=form,
               num_msg=num_msg,
               separateur=separateur,
               show_page=show_page)
    return render_to_response('post_old.html', ctx)
    
def redir(request, alias):
    """
    Redirection vers la source du lien
    Renvoie une erreur 404 si le lien n'existe pas
    """

    p = get_object_or_404(Url, url_min=alias)
    
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referer_clic = request.META.get('HTTP_REFERER', None)
    ip = request.META['REMOTE_ADDR']
    
    is_bot = is_bot_or_crawler(user_agent, ip)

    # Géolocalisation des clics
    my_country = None
    gi = geoip.GeoIP('%sGeoIP.dat' % (settings.STATIC_ROOT))
    country_data = gi.country_name_by_name(ip)
    
    obFichier = open('%slist_clics.txt' % (settings.STATIC_ROOT), 'a')
    obFichier.write('\r%s - link.%d [%s | %s] // %s -- %s' % (is_bot, p.id, ip, country_data, user_agent, referer_clic))
    obFichier.close()
            
    if is_bot:
        return HttpResponsePermanentRedirect(p.url_src)
        
    p.nb_clics += 1
    p.save()
    
    clic = Clic(url=p, pub_date='', ip_post=request.META['REMOTE_ADDR'], referer=referer_clic)
    clic.save()

    if country_data:
        try:
            country = Country.objects.get(name=country_data)
        except Country.DoesNotExist:
            country = Country(name=country_data, int=country_data)
            country.save()
        
        try:
            my_geoloc = Geoloc.objects.get(link=p, country=country)
        except Geoloc.DoesNotExist:
            my_geoloc = Geoloc(link=p, country=country)
            
        my_geoloc.nb_clics += 1
        my_geoloc.save()
        country.nb_clics += 1
        country.save()
        
        clic.country = country
        clic.save()
    
    return HttpResponsePermanentRedirect(p.url_src)

def urls_timeline(request):
    title = 'Last links'
    txt = 'Timeline'

    list_urls = Url.objects.filter(is_private=0).order_by('-pub_date')
    
    if not list_urls:
        return HttpResponseRedirect('/?msg=11')
    
    nb_links = list_urls.count()
    list_page, page, list_urls = get_list_page(request, list_urls, 20)
    separateur = '...'
    
    return render_to_response('row_urls.html', {'request': request, 
                                                'title': title, 
                                                'txt': txt, 
                                                'separateur': separateur, 
                                                'list_page': list_page, 
                                                'page': page, 
                                                'nb_links': nb_links, 
                                                'list_urls': list_urls})

def urls_popular(request):
    title = 'Top links right now'
    txt = 'Popular'

    list_urls = Url.objects.filter(is_private=0).order_by('-nb_clics')
    
    if not list_urls:
        return HttpResponseRedirect('/?msg=11')
    
    nb_links = list_urls.count()
    list_page, page, list_urls = get_list_page(request, list_urls, 20)
    separateur = '...'
    
    return render_to_response('row_urls.html', {'request': request, 
                                                'title': title, 
                                                'txt': txt, 
                                                'separateur': separateur, 
                                                'list_page': list_page, 
                                                'page': page, 
                                                'nb_links': nb_links, 
                                                'list_urls': list_urls})
    
def view_domain(request, url):
    list_urls = Url.objects.filter(domain=url).order_by('-pub_date')
    
    if not list_urls:
        return HttpResponseRedirect('/?msg=11')
    
    nb_links = list_urls.count()
    list_page, page, list_urls = get_list_page(request, list_urls, 15)
    separateur = '...'
    
    return render_to_response('domain.html', {'request': request, 'url': url, 'separateur': separateur, 'list_page': list_page, 'page': page, 'nb_links': nb_links, 'list_urls': list_urls})
    
def view_user(request, url):
    user = get_object_or_404(User, username=url)
    
    if request.user.is_authenticated() and request.user == user:
        list_urls = Url.objects.filter(auteur=user).order_by('-pub_date')
    else:
        list_urls = Url.objects.filter(auteur=user, is_private=0).order_by('-pub_date')
    
    nb_links = list_urls.count()
    list_page, page, list_urls = get_list_page(request, list_urls, 15)
    separateur = '...'
    
    return render_to_response('user.html', {'request': request, 'url': url, 'separateur': separateur, 'list_page': list_page, 'page': page, 'nb_links': nb_links, 'list_urls': list_urls})

def view_tools(request):
    domain_app = settings.SITE_URL
    return render_to_response('tools.html', {'request': request, 'domain_app': domain_app})
    
def view_doc_api(request):
    account_api = None
    
    if request.user.is_authenticated():
        send_request = request.GET.get('send_request', '')
        act_key = request.GET.get('act', '')
        url_key = request.GET.get('key', '')
        
        try:
            account_api = API.objects.get(auteur=request.user)
        except API.DoesNotExist:
            account_api = None
        
        if act_key in ['reset', 'delete'] and url_key:
            try:
                account_exists = API.objects.get(auteur=request.user, cle=url_key)
            except API.DoesNotExist:
                account_exists = None
                
            if account_exists:
                if 'delete' in act_key:
                    account_exists.delete()
                    return HttpResponseRedirect('/api/?msg=52')
                else:
                    account_exists.cle = makePassword(30,30)
                    account_exists.save()
                    return HttpResponseRedirect('/api/?msg=51')
            
        if request.method == 'POST' and account_api is None and send_request:
            accept_tos = request.POST.get('accept_tos', '')
            if accept_tos:
                apikey = makePassword(30,30)
                new_api = API(auteur=request.user, pseudo=request.user.username, cle=apikey, etat=2, date_propose=datetime.now())
                new_api.save()
                return HttpResponseRedirect('/api/?msg=50')
            
    domain_api = '%s/api/1.0/' % (settings.SITE_URL)
    num_msg = int(request.GET.get('msg', 0))
    return render_to_response('api.html', {'request': request, 'domain_api': domain_api, 'account_api': account_api, 'num_msg': num_msg})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.send()
            return HttpResponseRedirect('/contact/?msg=60')
    else:  
        form = ContactForm()
    
    num_msg = int(request.GET.get('msg', 0))
    return render_to_response('contact.html', {'request': request, 'form': form, 'num_msg': num_msg})
    
def view_clics(request, alias):
    url = get_object_or_404(Url, url_min=alias)
    
    if request.user.is_authenticated():
        if request.user == url.auteur or request.user.is_superuser:
            list_clics = Clic.objects.filter(url=url).order_by('-pub_date')
            nb_clics = list_clics.count()
            list_page, page, list_clics = get_list_page(request, list_clics, 50)
            separateur = '...'

            return render_to_response('clics.html', {'request': request, 
                                                     'url': url, 
                                                     'list_clics': list_clics, 
                                                     'separateur': separateur, 
                                                     'list_page': list_page, 
                                                     'page': page, 
                                                     'nb_clics': nb_clics})
            
    return HttpResponseRedirect('/s/%s/' % (url.url_min))

def view_fiche(request, alias):
    """
    Fiche détaillée d'un lien (titre, description, domaine, date et stats)
    Renvoie une erreur 404 si le lien n'existe pas
    """
    
    domain_app = settings.SITE_URL
    url = get_object_or_404(Url, url_min=alias)
    list_clics = Clic.objects.filter(url=url).order_by('pub_date')
    shared_sameurl = Url.objects.filter(url_src=url.url_src).exclude(url_min=url.url_min).order_by('-pub_date')
    list_geoloc = Geoloc.objects.filter(link=url).order_by('nb_clics')
    top_referers = defaultdict(int)
    all_referers = []
    all_clics_hours = []
    all_clics_days = []
    clics_by_hours = defaultdict(int)
    clics_by_days = defaultdict(int)
    show_post = False
    url_redir = '%s%s' % (domain_app, url.get_absolute_redir())
    msg_tweet = '%s %s' % (url.title, url_redir)
    
    if url.is_private:
        view_stats = False
    else:
        view_stats = True
        
    if request.user.is_authenticated():
        if request.user == url.auteur:
            view_stats = True
        if url.auteur and url.auteur.username and request.user != url.auteur:
            msg_tweet = 'RT @%s: %s %s' % (url.auteur.username, url.title, url_redir)
            
    if 'post_tweet_%d' % (url.id) in request.session:
        msg_tweet = request.session['post_tweet_%d' % (url.id)]
        
    if request.GET.getlist('new'):
        created_now = True
        show_post = True
    
    if request.GET.getlist('post'):
        show_post = True
        
    num_msg = int(request.GET.get('msg', 0))
    
    # Envoi de tweets
    if request.user.is_authenticated():
        if request.user.get_profile().can_tweet() and request.POST.getlist('msg_updatetweet') and len(request.POST['msg_updatetweet']) > 0:  
            msg_tweet = request.POST['msg_updatetweet'].encode('utf-8')
            send_tweet = request.user.get_profile().tweet(msg_tweet)
            
            if len(msg_tweet) <= 140:
                if send_tweet:
                    if 'post_tweet_%d' % (url.id) in request.session:
                        del request.session['post_tweet_%d' % (url.id)]
                    return HttpResponseRedirect('%s?msg=20' % url.get_absolute_url())
                else:
                    request.session['post_tweet_%d' % (url.id)] = msg_tweet
                    return HttpResponseRedirect('%s?msg=21&post' % url.get_absolute_url())
            else:
                request.session['post_tweet_%d' % (url.id)] = msg_tweet
                return HttpResponseRedirect('%s?msg=22&post' % url.get_absolute_url())
            
    date_actuelle = datetime.now()
    date_now = dateformat.format(date_actuelle, "dmYHi")[:10]
    
    for clic in list_clics:
        date_clic = dateformat.format(clic.pub_date, "dmYHi")
        heure_clic = date_clic[:10]
        jour_clic = date_clic[:8]
        
        if clic.referer:
            domain_referer = urlparse(clic.referer).netloc
            top_referers[domain_referer] += 1
        
        clics_by_hours[heure_clic] += 1
        clics_by_days[jour_clic] += 1
            
    for data_hours in clics_by_hours:
        all_clics_hours.append({'date': data_hours, 'nbr': clics_by_hours[data_hours]})
    
    for data_days in clics_by_days:
        all_clics_days.append({'date': data_days, 'nbr': clics_by_days[data_days]})
        
    for ref in top_referers:
        all_referers.append({'nbr': top_referers[ref], 'url': ref})
    
    all_referers.sort()
    all_referers.reverse()
    all_referers = all_referers[0:5]
    
    last_clics_24hours = all_clics_hours
    last_clics_24hours.reverse()
    last_clics_24hours = last_clics_24hours[0:25]
    last_heure_clic = int(date_now[8:])
    
    date_now_lt = dateformat.format(date_actuelle, "dmY")[:10]
    date_yest_lt = dateformat.format(date_actuelle+timedelta(days=-1), "dmY")
    
    donnees_calcul = {'hours': {'dates': [], 'nbr': [], 'clics': []}, 'days': {'dates': [], 'nbr': [], 'clics': []}, 'weeks': {'dates': [], 'nbr': [], 'clics': []}}
    
    # Graphique des clics par heure
    for i in xrange(25):
        lt_clic = last_heure_clic+i
        jour_concern = date_yest_lt
        nb_clics = 0
        
        if lt_clic > 23:
            lt_clic = lt_clic-24
            jour_concern = date_now_lt

        if lt_clic < 10:
            lt_clic = '0%d' % (lt_clic)
        
        heure_precise = '%s%s' % (jour_concern, lt_clic)
        
        if heure_precise in clics_by_hours:
            nb_clics = clics_by_hours[heure_precise]
           
        donnees_calcul['hours']['nbr'].append(nb_clics)
        donnees_calcul['hours']['dates'].append(lt_clic)
        i += 1
    
    # Graphique des clics 7 jours
    jour_debut = timedelta(days=-6)
    for i in xrange(7):
        jour_concern = dateformat.format(date_actuelle+jour_debut+timedelta(days=i), "dmY")
        lt_jour = jour_concern[:2]
        nb_clics = 0
        
        if jour_concern in clics_by_days:
           nb_clics = clics_by_days[jour_concern]
        
        donnees_calcul['days']['nbr'].append(nb_clics)
        donnees_calcul['days']['dates'].append(lt_jour)
        i += 1
        
    # Graphique des clics 30 jours
    jour_debut = timedelta(days=-29)
    for i in xrange(30):
        jour_concern = dateformat.format(date_actuelle+jour_debut+timedelta(days=i), "dmY")
        lt_jour = jour_concern[:2]
        nb_clics = 0
        
        if jour_concern in clics_by_days:
            nb_clics = clics_by_days[jour_concern]
        
        donnees_calcul['weeks']['nbr'].append(nb_clics)
        donnees_calcul['weeks']['dates'].append(lt_jour)
        i += 1
        
    graph_last_24h  = generate_stats_line(donnees_calcul['hours']['nbr'], donnees_calcul['hours']['dates'], '%s|%s' % (date_yest_lt, date_now_lt))
    graph_last_7j   = generate_stats_line(donnees_calcul['days']['nbr'], donnees_calcul['days']['dates'], '%s' % (date_now_lt))
    graph_last_30j  = generate_stats_line(donnees_calcul['weeks']['nbr'], donnees_calcul['weeks']['dates'], '%s' % (date_now_lt))

    last_clics_data = Clic.objects.filter(url=url).order_by('-pub_date')[:5]
    
    return render_to_response('fiche.html', {'request': request, 'url': url, 'graph_last_24h': graph_last_24h, 'graph_last_7j': graph_last_7j, 'graph_last_30j': graph_last_30j, 'list_geoloc': list_geoloc, 
    'all_referers': all_referers, 'shared_sameurl': shared_sameurl, 'view_stats': view_stats, 'last_clics_data': last_clics_data, 'url_redir': url_redir, 'msg_tweet': msg_tweet, 'show_post': show_post, 'num_msg': num_msg})

def ajax_pages(request, function):
    if function == 'edit':
        id_url = request.POST.get('id')
        src_url = request.POST.get('url_src')
        
        if not id_url or not src_url or request.user.is_anonymous():
            return HttpResponse('Error')
        
        try:
            link = Url.objects.get(pk=id_url)
        except Url.DoesNotExist:
            return HttpResponse('Error')

        if link.auteur != request.user:
            return HttpResponse('Error')
                
        # More infos on this url
        if request.method == 'POST':
            form = EditForm(request.POST, instance=link)
            
            if form.is_valid():
                data_url = extractDataFromUrl(form.cleaned_data['url_src'])
                
                if not data_url:
                    return HttpResponse('Error')
                
                link.domain = urlparse(form.cleaned_data['url_src']).netloc
                link.title = data_url['title'][0:200]
                link.description = data_url['description'][0:300]
                link.save()
                form.save()
                
                return XmlResponse(Url.objects.filter(pk=link.id), method='get_url_details')
            else:
                return HttpResponse('Error')
        else:
            return HttpResponse('Error')
        
    if function == 'delete':
        if not request.POST.getlist('id') or request.user.is_anonymous():
            return HttpResponse('Error')
                   
        try:
            link = Url.objects.get(pk=request.POST['id'])
        except Url.DoesNotExist:
            return HttpResponse('Error')

        if link.auteur != request.user:
            return HttpResponse('Error')
            
        link.delete()
        return HttpResponse('OK')
        
    return HttpResponse('')
    
# -------------------------------------------------------------
#   Attention : Début du code de l'API
# -------------------------------------------------------------
        
def justAPIv1(request, function, format_output='text'):
    method = None
    my_function = None
    list_functions = ['public_timeline', 'home_timeline', 'popular', 'view', 'view_url', 'by_domain', 'by_user', 'post', 'edit', 'delete']
    my_ip = request.META['REMOTE_ADDR']
    
    if format_output and format_output in ['json', 'xml', 'text']:
        method = format_output
        
    api_user = request.GET.get('api_user')
    api_key = request.GET.get('api_key')
    
    if not api_user or not api_key:
        return HttpResponse('Error')
        
    try:
        access_api = API.objects.get(pseudo=api_user, cle=api_key, etat=2)
    except API.DoesNotExist:
        return HttpResponse('Error')
        
    # Update api account
    access_api.nb_rqt += 1
    access_api.last_ip = my_ip
    access_api.last_date = datetime.now()
    access_api.save()
        
    """
    Liste tous les liens au format JSON ou XML
    """
    if function == 'public_timeline':
        list_urls = Url.objects.filter(is_private=0).order_by('-pub_date')[:20]
    
        if method == 'json':
            return JsonResponse(list_urls, method='get_urls')
        else:
            return XmlResponse(list_urls, method='get_urls')
    
    """
    Liste tous les liens de l'utilisateur connecté
    """
    if function == 'home_timeline':
        list_urls = Url.objects.filter(auteur=access_api.auteur).order_by('-pub_date')
    
        if method == 'json':
            return JsonResponse(list_urls, method='get_urls')
        else:
            return XmlResponse(list_urls, method='get_urls')
    
    """
    Liste tous les liens les plus populaires au format JSON ou XML
    """
    if function == 'popular':
        list_urls = Url.objects.filter(is_private=0).order_by('-nb_clics')[:20]
    
        if method == 'json':
            return JsonResponse(list_urls, method='get_urls')
        else:
            return XmlResponse(list_urls, method='get_urls')
    """
    Voir les détails d'un lien
    """
    if function == 'view':
        min_url = request.GET.get('url_src')
        
        if not min_url:
            return HttpResponse('Error')
        
        try:
            link = Url.objects.get(url_min=min_url)
        except Url.DoesNotExist:
            return HttpResponse('Error')
            
        if method == 'json':
            return JsonResponse(Url.objects.filter(pk=link.id), method='get_url_details')
        else:
            return XmlResponse(Url.objects.filter(pk=link.id), method='get_url_details')
    """
    Liste tous les liens pour le nom de domaine POST['domain']
    """
    if function == 'by_domain':
        get_domain = request.GET.get('domain')
        
        if not get_domain:
            return HttpResponse('Error')
            
        list_urls = Url.objects.filter(is_private=0, domain=get_domain)
    
        if method == 'json':
            return JsonResponse(list_urls, method='get_urls')
        else:
            return XmlResponse(list_urls, method='get_urls')
    
    """
    Liste tous les liens de l'utilisateur POST['member']
    """
    if function == 'by_user':
        get_user = request.GET.get('user')
        
        if not get_user:
            return HttpResponse('Error')
        
        try:
            user = User.objects.get(username=get_user)
        except:
            return HttpResponse('Error')
            
        list_urls = Url.objects.filter(is_private=0, auteur=user)
    
        if method == 'json':
            return JsonResponse(list_urls, method='get_urls')
        else:
            return XmlResponse(list_urls, method='get_urls')
    
    """
    Poste un lien depuis l'API (POST['source'])
    Returne l'alias du lien si SUCCES, sinon retourne False
    """
    if function == 'post':
        source_url = request.GET.get('url_src')
        domain_app = settings.SITE_URL
        
        if not source_url:
            return HttpResponse('Error')
            
        if request.method == 'GET':
            form = UrlForm(request.GET)
            
            if form.is_valid():
                new_url = form.save(commit=False)
                data_url = extractDataFromUrl(form.cleaned_data['url_src'])
                
                if not data_url:
                    return HttpResponse('Error')
                
                new_url.domain = urlparse(form.cleaned_data['url_src']).netloc
                new_url.title = data_url['title'][0:200]
                new_url.description = data_url['description'][0:300]
                new_url.ip_post = request.META['REMOTE_ADDR']
                
                # Try to get an alias...
                if not form.cleaned_data['url_min']:
                    alias_url = makePassword(3,4)
                    try:
                        link = Url.objects.get(url_min=alias_url)
                        rand_numb = random.randint(0,9)
                        new_alias = '%s%s' % (makePassword(3,4), rand_numb)
                    except Url.DoesNotExist:
                        new_alias = alias_url
                        
                    new_url.url_min = alias_url
                    
                # Géolocalisation des urls
                gi = geoip.GeoIP('%sGeoIP.dat' % (settings.STATIC_ROOT))
                country_data = gi.country_name_by_name(request.META['REMOTE_ADDR'])
            
                if country_data:
                    try:
                        my_country = Country.objects.get(name=country_data)
                    except Country.DoesNotExist:
                        my_country = Country(name=country_data, int=country_data)
                        my_country.save()
                    my_country.nb_links += 1
                    my_country.save()
                    new_url.country = my_country
                    
                new_url.auteur = access_api.auteur  
                new_url.save()

                if method == 'text':
                    return HttpResponse('%s/%s' % (domain_app, new_url.url_min))
                elif method == 'json':
                    return JsonResponse(Url.objects.filter(pk=new_url.id), method='get_urls')
                else:
                    return XmlResponse(Url.objects.filter(pk=new_url.id), method='get_urls')
            else:
                return HttpResponse('')
        else:
            return HttpResponse('')
            
    """
    Edite un lien depuis l'API (POST['alias'] et POST['source'])
    Returne un bolean
    """
    if function == 'edit':
        source_url = request.GET.get('url_src')
        min_url = request.GET.get('url_min')
        
        if not source_url or not min_url:
            return HttpResponse('Error')
            
        try:
            link = Url.objects.get(url_min=min_url)
        except Url.DoesNotExist:
            return HttpResponse('Error')
        
        if link.auteur != access_api.auteur:
            return HttpResponse('Error')
            
        if request.method == 'GET':
            form = EditForm(request.GET, instance=link)
            
            if form.is_valid():
                data_url = extractDataFromUrl(form.cleaned_data['url_src'])
                
                if not data_url:
                    return HttpResponse('Error')
                
                link.domain = urlparse(form.cleaned_data['url_src']).netloc
                link.title = data_url['title'][0:200]
                link.description = data_url['description'][0:300]
                link.save()
            
                return HttpResponse('OK')
            else:
                return HttpResponse('Error')
        else:
            return HttpResponse('Error')
        
    """
    Supprime un lien depuis l'API (POST['alias']
    Returne un bolean
    """    
    if function == 'delete':
        alias_url = request.GET.get('url_min')
        
        if not alias_url:
            return HttpResponse('Error')
        
        try:
            link = Url.objects.get(url_min=alias_url)
        except Url.DoesNotExist:
            return HttpResponse('Error')
            
        if link.auteur != access_api.auteur:
            return HttpResponse('Error')
            
        # Delete link
        link.delete()
        
        return HttpResponse('OK')

@user_passes_test(lambda u: u.is_authenticated() and u.is_superuser)
def clean_url(request):
    "Refresh the title and description of every url"
    urls = Url.objects.all()

    list_urls = []

    for url in urls:
        try:
            data_url = extractDataFromUrl(url.url_src)
        except:
            date_url = None
        
        if not data_url:
            # Website Down
            list_urls.append({'url': url, 'fixed': False})
            #url.delete()
            pass
        else:
            url.domain = urlparse(url.url_src).netloc
            url.title = data_url['title'][0:200]
            url.description = data_url['description'][0:300]
            url.save()
            list_urls.append({'url': url, 'fixed': True})

        
    return render_to_response('clean_status.html', {'urls': list_urls})

@login_required
def delete(request, alias):
    
    url = get_object_or_404(Url, url_min=alias)

    if url.auteur != request.user and not request.user.is_superuser :
        return HttpResponseRedirect('%s?msg=31' % url.get_absolute_url())
    
    url.delete()

    return HttpResponseRedirect('/?msg=30')
