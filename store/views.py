import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Avg
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings

from .models import Category, Product, ProductReview, Order, OrderItem, NewsletterSubscriber, ContactInquiry, Coupon
from .cart import Cart


def home(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    if not featured_products.exists():
        featured_products = Product.objects.filter(is_active=True)[:6]
        
    categories = Category.objects.all()[:6]
    recent_reviews = ProductReview.objects.select_related('product').all()[:4]
    
    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'recent_reviews': recent_reviews,
    })

def catalog(request, category_slug=None):
    category = None
    products_list = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all()

    # Category filter
    selected_cat_slug = category_slug or request.GET.get('category')
    if selected_cat_slug and selected_cat_slug != 'all':
        category = get_object_or_404(Category, slug=selected_cat_slug)
        products_list = products_list.filter(category=category)

    # Search query
    query = request.GET.get('q', '').strip()
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) |
            Q(short_description__icontains=query) |
            Q(full_description__icontains=query) |
            Q(origin__icontains=query) |
            Q(nose_notes__icontains=query) |
            Q(palate_notes__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Price range filter
    max_price_param = request.GET.get('max_price')
    if max_price_param:
        try:
            max_price_val = float(max_price_param)
            products_list = products_list.filter(price__lte=max_price_val)
        except (ValueError, TypeError):
            pass

    # Badge / Tag filter
    badge_param = request.GET.get('badge')
    if badge_param:
        products_list = products_list.filter(badge=badge_param)

    # Sorting
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price-asc':
        products_list = products_list.order_by('price')
    elif sort_by == 'price-desc':
        products_list = products_list.order_by('-price')
    elif sort_by == 'rating':
        products_list = products_list.order_by('-rating', '-review_count')
    elif sort_by == 'newest':
        products_list = products_list.order_by('-created_at')
    else:
        # featured default
        products_list = products_list.order_by('-is_featured', '-rating', '-created_at')

    # Total match count
    total_count = products_list.count()

    # Pagination
    paginator = Paginator(products_list, 9)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'category': category,
        'selected_category_slug': selected_cat_slug or 'all',
        'categories': categories,
        'products': products,
        'query': query,
        'sort_by': sort_by,
        'max_price': max_price_param or '500',
        'badge_filter': badge_param or '',
        'total_count': total_count,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return render(request, 'store/includes/product_grid.html', context)

    return render(request, 'store/catalog.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:3]
    
    if not related_products.exists():
        related_products = Product.objects.filter(is_active=True).exclude(id=product.id)[:3]

    reviews = product.reviews.all()

    if request.method == 'POST' and 'submit_review' in request.POST:
        author_name = request.POST.get('author_name', '').strip()
        rating = int(request.POST.get('rating', 5))
        title = request.POST.get('title', '').strip()
        comment = request.POST.get('comment', '').strip()

        if author_name and comment:
            ProductReview.objects.create(
                product=product,
                author_name=author_name,
                rating=rating,
                title=title,
                comment=comment,
                is_verified_buyer=True
            )
            # Update product rating average
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
            if avg_rating:
                product.rating = round(avg_rating, 1)
                product.review_count = product.reviews.count()
                product.save()
            messages.success(request, "Your tasting review has been recorded. Thank you for your review!")
            return redirect('store:product_detail', slug=product.slug)

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
    })

def cart_view(request):
    cart = Cart(request)
    return render(request, 'store/cart.html', {
        'cart': cart,
    })

@require_POST
def api_cart_add(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        override = bool(data.get('override', False))

        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = Cart(request)
        cart.add(product=product, quantity=quantity, override_quantity=override)

        return JsonResponse({
            'success': True,
            'message': f'"{product.name}" added to your cellar cart',
            'product_name': product.name,
            'cart': cart.to_dict(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@require_POST
def api_cart_update(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        if quantity > 0:
            cart.add(product=product, quantity=quantity, override_quantity=True)
        else:
            cart.remove(product)

        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'cart': cart.to_dict(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@require_POST
def api_cart_remove(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        product_id = data.get('product_id')

        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        cart.remove(product)

        return JsonResponse({
            'success': True,
            'message': f'"{product.name}" removed from cart',
            'cart': cart.to_dict(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@require_POST
def api_cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return JsonResponse({
        'success': True,
        'message': 'Your cellar cart has been cleared',
        'cart': cart.to_dict(),
    })

@require_POST
def api_apply_coupon(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        code = str(data.get('code', '')).strip()
        cart = Cart(request)
        if not code:
            cart.remove_coupon()
            return JsonResponse({
                'success': True,
                'message': 'VIP Voucher removed from your cart.',
                'cart': cart.to_dict(),
            })
        success, message = cart.apply_coupon(code)
        return JsonResponse({
            'success': success,
            'message': message,
            'cart': cart.to_dict(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def api_cart_data(request):
    cart = Cart(request)
    return JsonResponse(cart.to_dict())

def wishlist_view(request):
    wishlist_ids = request.session.get(settings.WISHLIST_SESSION_ID, [])
    products = Product.objects.filter(id__in=wishlist_ids, is_active=True)
    return render(request, 'store/wishlist.html', {
        'products': products,
    })

@require_POST
def api_wishlist_toggle(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        product_id = int(data.get('product_id'))
        product = get_object_or_404(Product, id=product_id)

        wishlist = request.session.get(settings.WISHLIST_SESSION_ID, [])
        if product_id in wishlist:
            wishlist.remove(product_id)
            in_wishlist = False
            message = f'"{product.name}" removed from wishlist'
        else:
            wishlist.append(product_id)
            in_wishlist = True
            message = f'"{product.name}" saved to your wishlist'

        request.session[settings.WISHLIST_SESSION_ID] = wishlist
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': message,
            'count': len(wishlist),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def checkout_view(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cellar cart is empty. Add bottles before checking out.")
        return redirect('store:catalog')

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'United States').strip()
        payment_method = request.POST.get('payment_method', 'Direct Admin Settlement (Concierge Transfer)').strip()
        delivery_notes = request.POST.get('delivery_notes', '').strip()

        if not all([customer_name, customer_email, shipping_address, city, postal_code]):
            messages.error(request, "Please fill in all required shipping and contact information.")
            return render(request, 'store/checkout.html', {'cart': cart})

        # Create Order
        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            payment_method=payment_method,
            delivery_notes=delivery_notes,
            subtotal=cart.get_subtotal(),
            shipping_cost=cart.get_shipping_cost(),
            discount=cart.get_discount(),
            total=cart.get_total_price(),
            coupon_code=cart.coupon_code or '',
            status='Processing'
        )

        # Create OrderItems
        for item in cart:
            product = item['product']
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_image=product.image_url,
                price=item['price'],
                quantity=item['quantity'],
                item_total=item['total_price']
            )
            # Update stock if available
            if product.stock >= item['quantity']:
                product.stock -= item['quantity']
                product.save()

        # Update coupon usage if applied
        if cart.coupon_code:
            applied_coupon = Coupon.objects.filter(code__iexact=cart.coupon_code).first()
            if applied_coupon:
                applied_coupon.times_used += 1
                applied_coupon.save()

        # Clear cart
        cart.clear()

        return redirect('store:order_success', order_number=order.order_number)

    return render(request, 'store/checkout.html', {
        'cart': cart,
    })

def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'store/order_success.html', {
        'order': order,
    })

@require_POST
def api_newsletter_subscribe(request):
    try:
        data = json.loads(request.body) if request.body else request.POST
        email = data.get('email', '').strip().lower()

        if not email or '@' not in email:
            return JsonResponse({'success': False, 'message': 'Please enter a valid email address.'}, status=400)

        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            message = "Welcome to The Cellar Club! Your VIP membership is confirmed."
        else:
            message = "You are already subscribed to The Cellar Club updates."

        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def heritage_view(request):
    return render(request, 'store/heritage.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        inquiry_type = request.POST.get('inquiry_type', 'General Inquiry').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactInquiry.objects.create(
                name=name,
                email=email,
                subject=subject or f"Inquiry from {name}",
                inquiry_type=inquiry_type,
                message=message
            )
            messages.success(request, "Your message has been received by our concierge. We will respond within 24 hours.")
            return redirect('store:contact')
        else:
            messages.error(request, "Please provide your name, email, and inquiry details.")

    return render(request, 'store/contact.html')
