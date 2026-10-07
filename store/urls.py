from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Pages
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<slug:category_slug>/', views.catalog, name='catalog_by_category'),
    path('spirit/<slug:slug>/', views.product_detail, name='product_detail'),
    path('heritage/', views.heritage_view, name='heritage'),
    path('contact/', views.contact_view, name='contact'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('order/success/<str:order_number>/', views.order_success, name='order_success'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    
    # AJAX API Endpoints
    path('api/cart/add/', views.api_cart_add, name='api_cart_add'),
    path('api/cart/update/', views.api_cart_update, name='api_cart_update'),
    path('api/cart/remove/', views.api_cart_remove, name='api_cart_remove'),
    path('api/cart/clear/', views.api_cart_clear, name='api_cart_clear'),
    path('api/cart/coupon/', views.api_apply_coupon, name='api_apply_coupon'),
    path('api/cart/data/', views.api_cart_data, name='api_cart_data'),
    path('api/wishlist/toggle/', views.api_wishlist_toggle, name='api_wishlist_toggle'),
    path('api/newsletter/subscribe/', views.api_newsletter_subscribe, name='api_newsletter_subscribe'),
]
