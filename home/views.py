from django.shortcuts import render, redirect
from user_agents import parse
from django.contrib.auth.decorators import user_passes_test

def is_2fa_authenticated(user):
    try:
        return user.is_authenticated and user.is_two_factor_enabled is True and len(user.totpdevice_set.all())>0
    except user.DoesNotExist:
        return False


def home_page(request):
    request.user.is_two_factor_enabled=False
    if request.user.is_authenticated:
        
        if request.user.totpdevice_set.all():
            devices = request.user.totpdevice_set.all()
           
            for t in devices:

                if (str(parse(request.META['HTTP_USER_AGENT'])) in str(t)):
                    request.user.is_two_factor_enabled=True 

    if request.user.is_authenticated and request.user.is_two_factor_enabled is False:
            return redirect("authenticate_2fa")
    return render(request, 'home/home.html')
