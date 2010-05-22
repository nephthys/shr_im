from django.contrib.auth.models import User
from django.db import models
from oauth import oauth
import re, httplib, simplejson
from utils import *

class Account(models.Model):
    user = models.ForeignKey(User, unique=True, primary_key=True)
    password = models.CharField(max_length=40)
    oauth_token = models.CharField(max_length=200)
    oauth_token_secret = models.CharField(max_length=200)
    avatar_url = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=160, blank=True, null=True)
    
    def get_absolute_url(self):
		return '/u/%s/' % (self.user.username)
        
    def validate(self):
        errors = []
        if self.username and not re.compile('^[a-zA-Z0-9_]{1,40}$').match( \
            self.username):
            errors += ['username']
        if self.email and not re.compile( \
            '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$').match( \
            self.email):
            errors += ['email']
        return errors

    # django.core.context_processors.auth assumes that an object attached
    # to request.user is always a django.contrib.auth.models.User, which
    # is completely broken but easy to work around
    def get_and_delete_messages(self): pass

    def token(self):
        return oauth.OAuthToken(self.oauth_token, self.oauth_token_secret)

    def is_authorized(self): return is_authorized(self.token())
    
    def can_tweet(self):
        if self.oauth_token and self.oauth_token_secret:
            return True
        else:
            return False
            
    def tweet(self, status):
        return api(
            'https://twitter.com/statuses/update.json',
            self.token(),
            http_method='POST',
            status=status
        )