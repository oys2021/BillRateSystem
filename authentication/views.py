import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in!")
            logger.info(f"User '{username}' logged in successfully.")
            return redirect('authentication:register')  
        else:
            messages.error(request, "Invalid username or password.")
            logger.warning(f"Failed login attempt for username: {username}")
    
    return render(request, "authentication/login.html")


def register_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            logger.warning(f"User '{username}' registration failed: Passwords do not match.")
            return redirect('authentication:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            logger.warning(f"User registration failed: Username '{username}' already exists.")
            return redirect('authentication:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            logger.warning(f"User registration failed: Email '{email}' already registered.")
            return redirect('authentication:register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        user.save()
        
        messages.success(request, "Registration successful! You can now log in.")
        logger.info(f"New user registered: {username} ({email})")
        return redirect('authentication:login')
    
    return render(request, "authentication/register.html")


def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, "You have been logged out.")
    logger.info(f"User '{username}' logged out.")
    return redirect('authentication:login')
