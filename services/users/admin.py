from django.contrib import admin
from .models import Role, UserProfile, UserAuthToken, UserSession, EmailOTP 


admin.site.register([Role, UserProfile, UserAuthToken, UserSession, EmailOTP])