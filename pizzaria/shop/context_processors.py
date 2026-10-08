def cart_count(request):
    """Add cart count to all templates"""
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return {'cart_count': count}