from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from .forms import RegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_online = True
            user.save()
            login(request, user)
            return redirect('user_list')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('user_list')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        request.user.is_online = False
        request.user.last_seen = timezone.now()
        request.user.save()
    logout(request)
    return redirect('login')
