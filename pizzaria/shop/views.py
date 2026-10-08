from django.shortcuts import render,redirect, get_object_or_404
from .models import Category,MenuItem , Order
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
# Create your views here.

def home(request):
    popular_items = MenuItem.objects.filter(is_popular=True, is_available=True)[:8]
    
    print(f"Popular items count: {popular_items.count()}")  # Debug line
    
    categories = Category.objects.filter(is_active=True)
    
   
        
    return render(request,'home.html',{
                  'popular_items': popular_items,
        'categories': categories
    })


def menu(request):
    """Menu page with category filtering"""
    # Get all active categories
    categories = Category.objects.filter(is_active=True)
    
    # Get filter parameter from URL
    category_slug = request.GET.get('category')
    
    # Base queryset
    items = MenuItem.objects.filter(is_available=True)
    
    # Filter by category if provided
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        items = items.filter(category=category)
    
    return render(request, 'menu.html', {
        'items': items,
        'categories': categories,
        'selected_category': category_slug
    })

def item_detail(request, slug):
    """Show details for a single item"""
    item = get_object_or_404(MenuItem, slug=slug, is_available=True)
    return render(request, 'item_detail.html', {'item': item})

def cart(request):
    """Display shopping cart"""
    cart = request.session.get('cart', {})
    
    items = []
    total = 0
    
    for item_id, item_data in cart.items():
        subtotal = item_data['price'] * item_data['quantity']
        total += subtotal
        items.append({
            'id': item_id,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'subtotal': subtotal
        })
    
    return render(request, 'cart.html', {
        'items': items,
        'total': total
    })


@csrf_exempt  # ← TEMPORARY for testing - we'll fix later
def add_to_cart(request):
    """Add item to cart via AJAX"""
    if request.method == 'GET':
        item_id = request.GET.get('item_id')
        quantity = int(request.GET.get('quantity', 1))
    else:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
    
    if not item_id:
        return JsonResponse({'error': 'Item ID required'}, status=400)
    
    try:
        # Get the item
        item = get_object_or_404(MenuItem, id=item_id, is_available=True)
        
        # Get cart from session
        cart = request.session.get('cart', {})
        item_id_str = str(item_id)
        
        if item_id_str in cart:
            cart[item_id_str]['quantity'] += quantity
        else:
            cart[item_id_str] = {
                'name': item.name,
                'price': float(item.price),
                'quantity': quantity
            }
        
        # Save cart to session
        request.session['cart'] = cart
        request.session.modified = True
        
        # Calculate total items
        total_items = sum(item['quantity'] for item in cart.values())
        
        return JsonResponse({
            'status': 'success',
            'message': f'{item.name} added to cart!',
            'cart_count': total_items
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

@csrf_exempt
def update_cart(request):
    """Update cart item quantity via AJAX"""
    if request.method not in ['GET', 'POST']:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Get data from GET or POST
    if request.method == 'GET':
        item_id = request.GET.get('item_id')
        action = request.GET.get('action')
    else:
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
    
    if not item_id:
        return JsonResponse({'error': 'Item ID required'}, status=400)
    
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)
    
    if item_id_str not in cart:
        return JsonResponse({'error': 'Item not in cart'}, status=404)
    
    if action == 'increase':
        cart[item_id_str]['quantity'] += 1
    elif action == 'decrease':
        cart[item_id_str]['quantity'] -= 1
        if cart[item_id_str]['quantity'] <= 0:
            del cart[item_id_str]
    elif action == 'remove':
        del cart[item_id_str]
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    # Save cart
    request.session['cart'] = cart
    request.session.modified = True
    
    # Calculate totals
    total_items = sum(item['quantity'] for item in cart.values())
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    
    return JsonResponse({
        'status': 'success',
        'cart_count': total_items,
        'total': total_price,
        'cart': cart
    })


# ===== CLEAR CART =====
@csrf_exempt
def clear_cart(request):
    """Clear all items from cart"""
    if request.method == 'GET':
        # Clear the cart
        request.session['cart'] = {}
        request.session.modified = True
        
        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared successfully!',
            'cart_count': 0
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


  # ← Add Order import

# ... your existing views (home, menu, add_to_cart, update_cart, clear_cart) ...

# ===== CHECKOUT =====
def checkout(request):
    """Checkout page"""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('shop:menu')
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    delivery_fee = 0
    total = subtotal + delivery_fee
    
    # Pre-fill user info if logged in
    user_info = {}
    if request.user.is_authenticated:
        user_info = {
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'phone': request.user.profile.phone if hasattr(request.user, 'profile') else '',
            'address': request.user.profile.address if hasattr(request.user, 'profile') else '',
        }
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        instructions = request.POST.get('instructions', '')
        payment_method = request.POST.get('payment_method', 'cash')
        
        # Validate required fields
        if not all([name, email, phone, address]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'shop/checkout.html', {
                'cart_items': cart.values(),
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'total': total,
                'user_info': user_info
            })
        
        # Create order - SAVE THE USER!
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,  # ← This saves the user!
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            delivery_address=address,
            items=cart,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            payment_method=payment_method,
            special_instructions=instructions
        )
        
        # Clear cart
        request.session['cart'] = {}
        request.session.modified = True
        
        messages.success(request, f'✅ Order #{order.order_number} placed successfully!')
        return redirect('shop:order_confirmation', order_number=order.order_number)
    
    return render(request, 'checkout.html', {
        'cart_items': cart.values(),
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'user_info': user_info
    })

# ===== ORDER CONFIRMATION =====
def order_confirmation(request, order_number):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'order_confirmation.html', {'order': order})

# ===== ORDER HISTORY (for logged-in users) =====
def order_history(request):
    """Show user's order history"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your orders.')
        return redirect('users:login')
    
    orders = request.user.orders.all()
    return render(request, 'order_history.html', {'orders': orders})




@staff_member_required
def admin_dashboard(request):
    """Admin dashboard with stats"""
    # Get date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Total orders
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    week_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
    
    # Revenue
    total_revenue = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
    today_revenue = Order.objects.filter(created_at__date=today).aggregate(Sum('total'))['total__sum'] or 0
    week_revenue = Order.objects.filter(created_at__date__gte=week_ago).aggregate(Sum('total'))['total__sum'] or 0
    
    # Order status breakdown
    status_counts = Order.objects.values('status').annotate(count=Count('status'))
    
    # Recent orders
    recent_orders = Order.objects.all()[:10]
    
    # Popular items (extract from JSON)
    all_items = Order.objects.all()
    item_counts = {}
    for order in all_items:
        for item_id, item_data in order.items.items():
            name = item_data.get('name', 'Unknown')
            if name in item_counts:
                item_counts[name] += item_data.get('quantity', 1)
            else:
                item_counts[name] = item_data.get('quantity', 1)
    
    # Sort by count
    popular_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    context = {
        'total_orders': total_orders,
        'today_orders': today_orders,
        'week_orders': week_orders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'week_revenue': week_revenue,
        'status_counts': status_counts,
        'recent_orders': recent_orders,
        'popular_items': popular_items,
        'today': today,
        'week_ago': week_ago,
    }
    
    return render(request, 'dashboard.html', context)

@staff_member_required
def admin_orders(request):
    """Admin order management"""
    orders = Order.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Search
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'orders.html', context)

@staff_member_required
def admin_order_detail(request, order_number):
    """View single order details"""
    order = get_object_or_404(Order, order_number=order_number)
    
    # Calculate item totals in the view
    order_items = []
    for item_id, item in order.items.items():
        item_total = item['price'] * item['quantity']
        order_items.append({
            'id': item_id,
            'name': item['name'],
            'quantity': item['quantity'],
            'price': item['price'],
            'total': item_total
        })
    
    if request.method == 'POST':
        # Update order status
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}')
            return redirect('shop:admin_order_detail', order_number=order.order_number)
    
    context = {
        'order': order,
        'order_items': order_items,  # ← Pass calculated items
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'order_detail.html', context)


def menu_item_detail(request, slug):
    """Display detailed view of a single menu item"""
    item = get_object_or_404(MenuItem, slug=slug, is_available=True)
    
    # Get related items (same category, excluding current item)
    related_items = MenuItem.objects.filter(
        category=item.category, 
        is_available=True
    ).exclude(id=item.id)[:4]
    
    context = {
        'item': item,
        'related_items': related_items,
    }
    
    return render(request, 'menu_item_detail.html', context)