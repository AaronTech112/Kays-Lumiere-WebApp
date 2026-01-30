from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignUpForm, EmailAuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailBackend')
            messages.success(request, "Registration successful.")
            return redirect('home')
        else:
            messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in.")
                return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
    
    # Get user orders
    from orders.models import Order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'profile.html', {'profile': profile, 'orders': orders})
