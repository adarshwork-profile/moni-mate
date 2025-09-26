from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # prevents login until approval
            user.save()
            messages.success(request, "Account created successfully. Wait for the approval.")

            # collect notify email 
            UserProfile.objects.create(user=user, notify_email = request.POST.get('notify_email'))

            # Notify admin
            send_mail(
                'New Signup Request - Moni-Mate',
                f'A new user "{user.username}" has signed up and is awaiting approval.',
                settings.DEFAULT_FROM_EMAIL,
                ['freelance.blackfly123@gmail.com']
            )
            return render(request, 'core/signup_processing.html') # request being processed page.
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('expense:dashboard')
        else:
            messages.error(request, "Invalid credentials")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully")
    return redirect('core:login')
