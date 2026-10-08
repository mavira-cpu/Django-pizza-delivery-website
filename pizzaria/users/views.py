from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm
from .models import UserProfile
from shop.models import Order

def register(request):
    """User registration page"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! 🍕')
            return redirect('shop:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """User login page"""
    if request.user.is_authenticated:
        return redirect('shop:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}! 🍕')
                return redirect('shop:home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('shop:home')

@login_required
def profile(request):
    """User profile page"""
    # Get or create profile
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, 'Profile created! Please update your details.')
    
    orders = request.user.orders.all().order_by('-created_at')[:10]
    
    if request.method == 'POST':
        # Update profile
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.city = request.POST.get('city', profile.city)
        profile.postal_code = request.POST.get('postal_code', profile.postal_code)
        profile.save()
        
        # Update user info
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()
        
        messages.success(request, 'Profile updated successfully! ✅')
        return redirect('users:profile')
    
    return render(request, 'profile.html', {
        'profile': profile,
        'orders': orders
    })

@login_required
def order_detail(request, order_number):
    """View specific order details"""
    # Get the order and ensure it belongs to the current user
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Calculate item totals
    order_items = []
    for item_id, item in order.items.items():
        order_items.append({
            'id': item_id,
            'name': item.get('name', 'Unknown'),
            'quantity': item.get('quantity', 1),
            'price': item.get('price', 0),
            'total': item.get('price', 0) * item.get('quantity', 1)
        })
    
    # Get status history
    status_history = getattr(order, 'status_history', [])
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_history': status_history,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'order_detail.html', context)

@login_required
def order_history(request):
    """User's order history"""
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})