
# If the user sends a HTTP POST, with a username and password, check supplied values and allow auth.
# If not, show the sign up form

from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from accountauth.models import CustomUser
from django.http import HttpResponseForbidden
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import logout
from projects.models import Projects
from projects.storage import load_project_template, save_project_template
from user_agents import parse


class UserCreateForm(UserCreationForm):

    class Meta:
        fields = ('username','password1','password2')
        model = CustomUser


def device_name(request):
    return str(parse(request.META.get('HTTP_USER_AGENT', 'unknown')))


def current_totp_device(user, request, confirmed=None):
    devices = user.totpdevice_set.all()
    if confirmed is not None:
        devices = devices.filter(confirmed=confirmed)
    name = device_name(request)
    for device in devices:
        if name == device.name:
            return device
    return None


def get_or_create_current_totp_device(user, request):
    device = current_totp_device(user, request)
    if device:
        return device
    return user.totpdevice_set.create(confirmed=False, name=device_name(request))


def has_verified_2fa(user):
    return user.is_authenticated and user.is_two_factor_enabled


def request_has_verified_2fa(request):
    return (
        request.user.is_authenticated
        and request.user.is_two_factor_enabled
        and current_totp_device(request.user, request, confirmed=True) is not None
    )


def signup(request):     
    if request.method == 'POST':
        form = UserCreateForm(request.POST)

        if form.is_valid() and not CustomUser.objects.filter(username=form.cleaned_data.get('username')).exists():
                user = form.save(commit=False)
                user.is_superuser = False
                user.is_staff = False
                user.is_two_factor_enabled = False
                user.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(request, username=username, password=raw_password)
                login(request, user)
                secret= get_or_create_current_totp_device(user, request)
                return render(request, '2fa.html', {'secret':secret.config_url}) 
        else:
            return render(request, 'auth/signup.html', {'form': form, 'message': 'User already exists or the form is invalid'})
    else:
        form = UserCreateForm()
        return render(request, 'auth/signup.html', {'form': form})

@login_required
def authenticate_2fa(request):
    secret= get_or_create_current_totp_device(request.user, request)
    return render(request, '2fa.html', {'secret':secret.config_url})

class TOTPCreateView(views.APIView):
    """
    Use this endpoint to set up a new TOTP device
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, format=None):
        user = request.user
        device = get_or_create_current_totp_device(user, request)
        url = device.config_url
        return Response(url, status=status.HTTP_201_CREATED)

class TOTPVerifyView(views.APIView):
    """
    Api to verify/enable a TOTP device
    """
    permission_classes = (permissions.IsAuthenticated, )
    def post(self, request, format=None):
        user = request.user
        device = current_totp_device(user, request)

        if not device:
             return Response(dict(
           errors=['This user has not setup two factor authentication']),
                status=status.HTTP_400_BAD_REQUEST
            )
        if device.verify_token(request.POST.get('verification_code', '')):
            if not device.confirmed:
                device.confirmed = True
                device.save()
                user.is_two_factor_enabled=True
                user.save() 
            
            return render(request, 'verified.html',{'user':user})
        return render(request, '2fa.html', {'secret':device.config_url})


@login_required
def profile(request):
    if request_has_verified_2fa(request):
        projects = Projects.objects.visible_to(request.user)
        devices=list(request.user.totpdevice_set.all())
        verified_devices=[]
        for d in devices:
            if d.confirmed==True:
                verified_devices.append(d)

        return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices})
    else:
        return redirect("authenticate_2fa")

@login_required
def modify_password(request):
    if not request_has_verified_2fa(request):
        return redirect("authenticate_2fa")

    #Getting user info
    projects = Projects.objects.visible_to(request.user)
        
    devices=list(request.user.totpdevice_set.all())
    verified_devices=[]
    for d in devices:
        if d.confirmed==True:
            verified_devices.append(d)

    data = dict()
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid() and request.POST.get('new_password2') == request.POST.get('new_password1') :
            form.save()
            data['form_is_valid'] = True
            update_session_auth_hash(request, form.user)
            message = "Your password was changed"
        else:
            data['form_is_valid'] = False
            message = "Your password was not changed"
    else:
        form = PasswordChangeForm(user=request.user)
        message = ""
    return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices,'message':message})

def custom_logout(request):
    logout(request)
    return redirect('home')

@login_required
def unauthenticate_device(request,device):

    devices = request.user.totpdevice_set.all()
    for t in devices:
        if (str(t)==device):
            t.delete()

    if device_name(request) in device:
        return custom_logout(request)
    return redirect('home')

@login_required
def modify_username(request):
    if not request_has_verified_2fa(request):
        return redirect("authenticate_2fa")
    #Getting user prjects and devices
    projects = Projects.objects.visible_to(request.user)

        
    devices=list(request.user.totpdevice_set.all())
    verified_devices=[]
    for d in devices:
        if d.confirmed==True:
            verified_devices.append(d)
    
    #Modify and render
    if request.method == 'POST':
        new_username= request.POST.get('new_username1', '').strip()
        if not new_username:
            return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices,'message':"Username cannot be empty"})
        if not CustomUser.objects.filter(username=new_username).exists():
            for p in projects:
                if p.project_owner == request.user.username or request.user.username in p.allowed_viewer_names():
                    project_change=Projects.objects.get(id=p.id)
                    project = load_project_template(project_change)
                    #If its the owner of the project modify project owner with the new username (for the project and its template)
                    if project['project_owner']==request.user.username:
                        project['project_owner']=new_username
                        project_change.project_owner=new_username
                    #If he is an allowed user for the project, change the username (for the project and its template)
                    if request.user.username in p.allowed_viewer_names():
                        changed_list = [
                            new_username if viewer == request.user.username else viewer
                            for viewer in p.allowed_viewer_names()
                        ]
                        project['project_allowed_viewers']= ",".join(changed_list)
                        project_change.project_allowed_viewers= ",".join(changed_list)
                    #We update template and project    
                    save_project_template(project_change, project)
                    project_change.save()   
                    

            user=CustomUser.objects.get(username=request.user.username)   
            user.username=new_username
            user.save()
            request.user=user
            request.user.save()
        else: 
            return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices,'message':"Username already exists, the username wasnt changed"})
        return render(request, 'auth/profile.html', {'projects':projects,'devices':verified_devices,'message':"Username changed to "+ request.POST.get('new_username1')})

@login_required
def removefromproject(request,projectid):
    if not request_has_verified_2fa(request):
        return redirect("authenticate_2fa")
    change = Projects.objects.get(id=projectid)
    if not change.can_view(request.user):
        return HttpResponseForbidden('You are not allowed to modify this project.')
    project = load_project_template(change)
    
    allowed_users = change.allowed_viewer_names()
    if change.project_owner!=request.user.username:
        if request.user.username in allowed_users:
            allowed_users.remove(request.user.username)
        new_allowed_viewers = ",".join(allowed_users)

        change.project_allowed_viewers= new_allowed_viewers
        project['project_allowed_viewers']= new_allowed_viewers
        change.save()
        save_project_template(change, project)
    return redirect('profile') 
