
# If the user sends a HTTP POST, with a username and password, check supplied values and allow auth.
# If not, show the sign up form

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django import forms
from django.contrib.auth import get_user_model
from accountauth.models import CustomUser
from django.http import HttpResponse


class UserCreateForm(UserCreationForm):
   
    

    class Meta:
        fields = ('username','password1','password2','is_two_factor_enabled')
        widgets = {
            'is_two_factor_enabled': forms.HiddenInput(),
        }
        model = CustomUser



def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password, is_two_factor_enabled=False)
            
            login(request, user)
            secret= user.totpdevice_set.create(confirmed=False)
            return render(request, '2fa.html', {'secret':secret.config_url})
    else:
        form = UserCreateForm()
    return render(request, 'auth/signup.html', {'form': form})

def authenticate_2fa(request):
    secret= request.user.totpdevice_set.create(confirmed=False)
    return render(request, '2fa.html', {'secret':secret.config_url})


def get_user_totp_device(self, user, confirmed=None):
    devices = devices_for_user(user, confirmed=confirmed)
    for device in devices:
        if isinstance(device, TOTPDevice):
            return device
class TOTPCreateView(views.APIView):
    """
    Use this endpoint to set up a new TOTP device
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        user.is_two_factor_enabled=False
        device = get_user_totp_device(self, user)
        if not device:
            device = user.totpdevice_set.create(confirmed=False)
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)

class TOTPVerifyView(views.APIView):
    """
    Api to verify/enable a TOTP device
    """
    permission_classes = (permissions.IsAuthenticated, )
    def post(self, request, format=None):
        user = request.user
        device = get_user_totp_device(self, user)
        
        if not device:
             return Response(dict(
           errors=['This user has not setup two factor authentication']),
                status=status.HTTP_400_BAD_REQUEST
            )
        if not device == None and device.verify_token(request.POST['verification_code']):
            if not device.confirmed:
                device.confirmed = True
                device.save()
                
                user.is_two_factor_enabled=True
                user.save()
                
            return render(request, 'verified.html',{'user':user})
        return render(request, '2fa.html', {'secret':device.config_url})