from django.shortcuts import render, redirect
from user_agents import parse



def home_page(request):
    if request.user.is_authenticated:
        request.user.is_two_factor_enabled = False
        verified_devices = request.user.totpdevice_set.filter(confirmed=True)
        current_device_name = str(parse(request.META.get('HTTP_USER_AGENT', 'unknown')))
        for device in verified_devices:
            if current_device_name == device.name:
                request.user.is_two_factor_enabled = True
                break
        request.user.save(update_fields=['is_two_factor_enabled'])
    if request.user.is_authenticated and request.user.is_two_factor_enabled is False:
            return redirect("authenticate_2fa")
    return render(request, 'home/home.html')
