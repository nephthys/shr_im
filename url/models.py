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

from django import forms
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from datetime import datetime
from shr.settings import MANAGERS

class Url(models.Model):
    auteur = models.ForeignKey(User, null=True, blank=True)
    url_src = models.URLField('source')
    url_min = models.CharField(max_length=20, null=True, blank=True, unique=True)
    domain = models.CharField(max_length=50)
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True, verbose_name='description')
    pub_date = models.DateTimeField(default=datetime.now, auto_now_add=True, verbose_name='created at')
    ip_post = models.IPAddressField(null=True, blank=True, verbose_name='IP', default='0.0.0.0')
    nb_clics = models.IntegerField(null=True, blank=True, default=0)
    is_private = models.BooleanField(default=0)
    country = models.ForeignKey('Country', null=True, blank=True)
    
    def __str__(self):
        return self.url_src
        
    def get_absolute_redir(self):
		return '/%s' % (self.url_min)
        
    def get_absolute_url(self):
		return '/s/%s/' % (self.url_min)
        
class UrlForm(forms.ModelForm):
    url_min = forms.CharField(max_length=20, required=False)
    is_private = forms.BooleanField(required=False)
    
    class Meta:
        model = Url
        fields = ['url_src', 'url_min', 'is_private']
        
    def clean_url_src(self):
        source_url = self.cleaned_data['url_src']
        if not source_url.startswith('http://') and not source_url.startswith('https://'):
            return 'http://%s' % (source_url)
        return source_url
 
    def clean_url_min(self):
        alias_url = self.cleaned_data['url_min']
        try:
            Url.objects.get(url_min__exact=alias_url)
            raise forms.ValidationError('This alias is already token!')
        except Url.DoesNotExist:
            return alias_url

        raise forms.ValidationError('This alias is already token!')
        
class EditForm(forms.ModelForm):
    is_private = forms.BooleanField(required=False)
    
    class Meta:
        model = Url
        fields = ['url_src', 'is_private']
        
    def clean_url_src(self):
        source_url = self.cleaned_data['url_src']
        if not source_url.startswith('http://') and not source_url.startswith('https://'):
            return 'http://%s' % (source_url)
        return source_url
		
class API(models.Model):
    LIST_ETAT = (
		(2, 'Actif'),
		(1, 'En attente'),
		(0, 'Désactivé'),
	)
    
    auteur = models.ForeignKey(User)
    pseudo = models.CharField(max_length=30)
    cle = models.CharField(max_length=30, verbose_name='Clé')
    etat = models.IntegerField(max_length=1, choices=LIST_ETAT, default=1)
    nb_rqt = models.IntegerField(null=True, blank=True, default=0, verbose_name='Nombre de requêtes')
    last_ip = models.IPAddressField(null=False, blank=False, verbose_name='IP', default='0.0.0.0')
    date_propose = models.DateTimeField(verbose_name='Date de soumission', null=True, blank=True)
    last_date = models.DateTimeField(verbose_name='Dernière activité', null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'API'
        
class Country(models.Model):
    name = models.CharField(max_length=50)
    int = models.CharField(max_length=50)
    nb_clics = models.IntegerField(null=True, blank=True, default=0)
    nb_links = models.IntegerField(null=True, blank=True, default=0)
    
    def __str__(self):
        return self.name
    
class Geoloc(models.Model):
    link = models.ForeignKey(Url)
    country = models.ForeignKey(Country)
    nb_clics = models.IntegerField(null=True, blank=True, default=0)
    
class Clic(models.Model):
    url = models.ForeignKey(Url)
    pub_date = models.DateTimeField(default=datetime.now, auto_now_add=True, verbose_name='created at')
    ip_post = models.IPAddressField(null=True, blank=True, verbose_name='IP', default='0.0.0.0')
    referer = models.URLField(null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    
class ContactForm(forms.Form):
    pseudo = forms.CharField(label='Name', required=False)
    mail = forms.EmailField(label='Email')
    objet  = forms.CharField(label='Topic', required=False)
    message = forms.CharField(label='Content',widget=forms.Textarea)

    def send(self, mails=[]):
        if self.is_valid():
            if not mails:
                mails = [a[1] for a in MANAGERS]
            # Codage de l'envoi
            subject = u'%s' % (self.cleaned_data['objet'])
            msg = EmailMessage(subject, self.cleaned_data['message'], self.cleaned_data['mail'], mails)
            try:
                msg.send()
            except:
                return False

            return True

        return False
        
