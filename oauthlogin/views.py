from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.core.urlresolvers import reverse
from oauth import oauth
from utils import *
from models import Account
from shr.functions import *

def connection(request):
    if request.user.is_anonymous():
        token = get_unauthorized_token()
        request.session['token'] = token.to_string()
        return HttpResponseRedirect(get_authorization_url(token))
    else:
        return HttpResponseRedirect('/?msg=1')

def callback(request):
    error = False
    token = request.session.get('token', None)
    if not token: error = True
        
    token = oauth.OAuthToken.from_string(token)
    if token.key != request.GET.get('oauth_token', 'no-token'): error = True
    token = get_authorized_token(token)

    # Actually login
    obj = is_authorized(token)
    if obj is None: error = True
    
    if error:
        return HttpResponseRedirect('/?msg=2')
    
    username_twitter = obj['screen_name']

    try: # Connexion au compte existant
        u = User.objects.get(username=username_twitter)
        user = Account.objects.get(user=u)
        new_id = u.id
        password_value = user.password
    except User.DoesNotExist: # Creation du compte
        password_value = makePassword(39,40)
        new_user = User.objects.create_user(username=username_twitter, email='root@shr.im', password=password_value)
        new_user.first_name = obj['name']
        new_user.is_staff = False
        new_user.is_superuser = False
        new_user.save()
        usermod = new_user
        new_id = new_user.id
        user = Account(user=new_user)
        user.password = password_value
        
    user.oauth_token = token.key
    user.oauth_token_secret = token.secret
    user.url = obj['url']
    user.location = obj['location']
    user.description = obj['description']
    user.avatar_url = obj['profile_image_url']
    user.save()
        
    userco = authenticate(username=username_twitter, password=password_value)

    if userco is not None:
        login(request, userco)
        return HttpResponseRedirect('/?msg=2')
    else:
        return HttpResponseRedirect('/?msg=1')

def disconnect(request):
    if not request.user.is_anonymous():
        logout(request)
    return HttpResponseRedirect('/?msg=3')