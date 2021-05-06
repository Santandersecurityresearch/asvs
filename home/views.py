from django.shortcuts import render, redirect
from user_agents import parse
from django.contrib.auth.decorators import user_passes_test



def home_page(request):
    request.user.is_two_factor_enabled=False
    if request.user:
        if request.user.is_authenticated:
            
            if request.user.totpdevice_set.all():
                devices=list(request.user.totpdevice_set.all())
                
                verified_devices=[]
                for d in devices:
                    
                    if d.confirmed==True:
                        verified_devices.append(d)
                
                for t in verified_devices:
                
                    if (str(parse(request.META['HTTP_USER_AGENT'])) in str(t)):
                        
                        request.user.is_two_factor_enabled=True 
                        
            request.user.save()
    if request.user.is_authenticated and request.user.is_two_factor_enabled is False:
            return redirect("authenticate_2fa")
    return render(request, 'home/home.html')
