# Basic setup for allowing users to sign up using a username and a password. 

from django.urls import re_path
from django.contrib.auth.views import LoginView, LogoutView
from .views import signup, TOTPVerifyView, authenticate_2fa, profile, modify_password, custom_logout, modify_username, removefromproject, unauthenticate_device

from .import views
handler404 = 'asvs.views.handler404'
handler500 = 'asvs.views.handler500'

urlpatterns = [
    re_path(r'^totp/create/$', views.TOTPCreateView.as_view(), name='totp-create'),
    re_path(r'^totp/login/$', views.TOTPVerifyView.as_view() , name='totp-login'),
    re_path(r'^authenticate_2fa/$',authenticate_2fa, name='authenticate_2fa'),
    re_path(r'^signup/$', signup, name='signup'),
    re_path(r'login$', LoginView.as_view(
        template_name="auth/login.html"), name="login"),
    re_path(r'logout$', custom_logout, name="logout"),
    re_path(r'profile', profile, name="profile"),
    re_path(r'modify_password$', modify_password, name="modify_password"),  
    re_path(r'modify_username$', modify_username, name="modify_username"),
    re_path(r'^removefromproject/(?P<projectid>\S+)$', removefromproject, name="removefromproject"),
    re_path(r'^unauthenticate_device/(?P<device>[\w\s(),.:;/<>_-]+)$', unauthenticate_device, name="unauthenticate_device"),
    
]
