from django.urls import path
from .api import signup, verifyotp, login, createsession, validatesession, logout, createuserbyadmin, getusers

urlpatterns = [
    path('signup/', signup),
    path('verify-otp/', verifyotp),
    path('login/', login),
    path('create-session/', createsession),
    path('validate-session/', validatesession),
    path('logout/', logout),
    path('create-user/', createuserbyadmin),
    path('get-users/', getusers),
]