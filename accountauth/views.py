
# If the user sends a HTTP POST, with a username and password, check supplied values and allow auth.
# If not, show the sign up form

from django.contrib.auth import login, authenticate, update_session_auth_hash
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
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout
from projects.models import Projects
from django.db.models import Q
import hashlib
from user_agents import parse


class UserCreateForm(UserCreationForm):
   
    

    class Meta:
        fields = ('username','password1','password2','is_two_factor_enabled','is_superuser')
        widgets = {
            'is_two_factor_enabled': forms.HiddenInput(),
            'is_superuser': forms.HiddenInput(),
        }
        model = CustomUser



def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password, is_two_factor_enabled=False, is_superuser=False)
            
            login(request, user)
            secret= user.totpdevice_set.create(confirmed=False,name=str(parse(request.META['HTTP_USER_AGENT'])))
            return render(request, '2fa.html', {'secret':secret.config_url})
    else:
        form = UserCreateForm()
    return render(request, 'auth/signup.html', {'form': form})

def authenticate_2fa(request):
    secret= request.user.totpdevice_set.create(confirmed=False,name=str(parse(request.META['HTTP_USER_AGENT'])))
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
        
        devices=list(request.user.totpdevice_set.all())
        
        device = user.totpdevice_set.create(confirmed=True,name=str(parse(request.META['HTTP_USER_AGENT'])))
   
        device.confirmed=True   
        user.is_two_factor_enabled=True   
        user.save() 
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)

class TOTPVerifyView(views.APIView):
    """
    Api to verify/enable a TOTP device
    """
    permission_classes = (permissions.IsAuthenticated, )
    def post(self, request, format=None):
        user = request.user
        
        devices=list(request.user.totpdevice_set.all())
        verified_devices=[]
        for d in devices:
            if str(parse(request.META['HTTP_USER_AGENT'])) in str(d):
                device=d
        
                device.confirmed = True
                device.save()   
                user.is_two_factor_enabled=True
                user.save()

        if not device:
             return Response(dict(
           errors=['This user has not setup two factor authentication']),
                status=status.HTTP_400_BAD_REQUEST
            )
        if device.verify_token(request.POST['verification_code']):
            if not device.confirmed:
                device.confirmed = True
                device.save()
                if user.username=="admin":
                    user.is_superuser=True
            user.is_two_factor_enabled=True
            user.save()    
                
            return render(request, 'verified.html',{'user':user})
        return render(request, '2fa.html', {'secret':device.config_url})


def profile(request):
    if request.user.is_authenticated and request.user.is_two_factor_enabled:
        if request.user.is_superuser:
            projects = Projects.objects.all().values()
        else:
            projects = Projects.objects.filter(Q(project_owner=request.user.username) | Q(
                project_allowed_viewers__icontains=request.user.username)).values()
               
        devices=list(request.user.totpdevice_set.all())
        verified_devices=[]
        for d in devices:
            if d.confirmed==True:
                verified_devices.append(d)

        return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices})
    else:
        if request.user.is_authenticated  and not request.user.is_two_factor_enabled:
            return redirect("authenticate_2fa") 
        else:    
            return HttpResponseForbidden('You need to be authenticated to see this page.')

def modify_password(request):
    data = dict()
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid() and request.POST.get('password2') == request.POST.get('password1') :
            form.save()
            data['form_is_valid'] = True
            update_session_auth_hash(request, form.user)
        else:
            data['form_is_valid'] = False
    else:
        form = PasswordChangeForm(user=request.user)
    return redirect('profile')     

def custom_logout(request):
    print('Loggin out {}'.format(request.user))



    logout(request)
    print(request.user)
    return redirect('home')

def unauthenticate_device(request,device):

    devices = request.user.totpdevice_set.all()
    for t in devices:
        if (str(t)==device):
            t.delete()

    if str(parse(request.META['HTTP_USER_AGENT'])) in device:
        custom_logout(request)    
    return redirect('home')

def modify_username(request):
    data = dict()
    if request.method == 'POST':
        new_username= request.POST.get('new_username1')
        request.user.username = new_username
        request.user.save()
    return redirect('profile') 

def removefromproject(request,projectid):
    phash = (hashlib.sha3_256('{0}{1}'.format(
            request.user.username, projectid).encode('utf-8')).hexdigest())
    change = Projects.objects.get(id=projectid)
    allowed_users = change.project_allowed_viewers.split(",")
    if change.project_owner!=request.user.username:
        allowed_users.remove(request.user.username)
        new_allowed_viewers=""
        for u in allowed_users:
            new_allowed_viewers+= u+","

        change.project_allowed_viewers= new_allowed_viewers[:-1]
        change.save()
    return redirect('profile') 
 