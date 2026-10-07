from .cart import Cart
from .models import Category, Product
from django.conf import settings


def cart_and_store_context(request):
    cart = Cart(request)
    wishlist = request.session.get(settings.WISHLIST_SESSION_ID, [])
    categories = Category.objects.all()
    
    return {
        'cart': cart,
        'cart_count': len(cart),
        'cart_subtotal': cart.get_subtotal(),
        'cart_total': cart.get_total_price(),
        'categories': categories,
        'wishlist_count': len(wishlist),
        'wishlist_ids': wishlist,
    }
