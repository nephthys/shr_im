from shr.oauthlogin.models import *
from django.contrib import admin

class AccountAdmin(admin.ModelAdmin):
    list_display = ('oauth_token', 'oauth_token_secret', 'avatar_url', 'location', 'url', 'description',)
    
admin.site.register(Account, AccountAdmin)