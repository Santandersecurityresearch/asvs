
# If the user sends a HTTP POST, with a username and password, check supplied values and allow auth.
# If not, show the sign up form

from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse, HttpResponseForbidden


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

# Loads the profile page for the user


def profile(request):
    if request.user.is_authenticated:
        return render(request, 'auth/profile.html')
    else:
        return HttpResponseForbidden('You need to be authenticated to see this page.')
