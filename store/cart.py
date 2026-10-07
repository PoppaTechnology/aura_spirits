from decimal import Decimal
from django.conf import settings
from .models import Product, Coupon


class Cart:
    FREE_SHIPPING_THRESHOLD = Decimal('150.00')
    STANDARD_SHIPPING = Decimal('15.00')

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_code = self.session.get('applied_coupon', None)

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = max(1, int(quantity))
        else:
            self.cart[product_id]['quantity'] += max(1, int(quantity))

        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session['applied_coupon'] = None
        self.save()

    def get_coupon_obj(self):
        if not self.coupon_code:
            return None
        return Coupon.objects.filter(code__iexact=self.coupon_code).first()

    def apply_coupon(self, code):
        code = code.strip().upper()
        if not code:
            return False, "Please enter a voucher code."

        coupon = Coupon.objects.filter(code__iexact=code).first()
        if not coupon:
            return False, "Invalid VIP voucher code. Exclusive coupon codes are issued directly by the cellar administrator."

        is_valid, msg = coupon.is_valid()
        if not is_valid:
            return False, msg

        if coupon.discount_percent not in (10, 20, 50):
            return False, "Invalid discount tier on voucher."

        self.session['applied_coupon'] = coupon.code
        self.coupon_code = coupon.code
        self.save()
        return True, f"VIP Voucher '{coupon.code}' applied: {coupon.discount_percent}% discount on your order!"

    def remove_coupon(self):
        self.session['applied_coupon'] = None
        self.coupon_code = None
        self.save()

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}

        for pid, item_data in self.cart.items():
            if pid in product_map:
                prod = product_map[pid]
                price = Decimal(str(item_data['price']))
                qty = int(item_data['quantity'])
                yield {
                    'product': prod,
                    'quantity': qty,
                    'price': price,
                    'total_price': price * qty,
                }

    def __len__(self):
        return sum(int(item['quantity']) for item in self.cart.values())

    def get_subtotal(self):
        return sum(Decimal(str(item['price'])) * int(item['quantity']) for item in self.cart.values())

    def get_discount(self):
        subtotal = self.get_subtotal()
        if not self.coupon_code or subtotal <= 0:
            return Decimal('0.00')

        coupon = self.get_coupon_obj()
        if not coupon or not coupon.is_active:
            return Decimal('0.00')

        if coupon.discount_percent in (10, 20, 50):
            return (subtotal * Decimal(str(coupon.discount_percent))) / Decimal('100.00')
        return Decimal('0.00')

    def get_shipping_cost(self):
        subtotal = self.get_subtotal()
        if subtotal == Decimal('0.00'):
            return Decimal('0.00')
        if subtotal >= self.FREE_SHIPPING_THRESHOLD:
            return Decimal('0.00')
        return self.STANDARD_SHIPPING

    def get_total_price(self):
        subtotal = self.get_subtotal()
        if subtotal == Decimal('0.00'):
            return Decimal('0.00')
        discount = self.get_discount()
        shipping = self.get_shipping_cost()
        return max(Decimal('0.00'), (subtotal - discount) + shipping)

    def get_free_shipping_progress(self):
        subtotal = self.get_subtotal()
        if subtotal >= self.FREE_SHIPPING_THRESHOLD:
            return 100, Decimal('0.00')
        needed = self.FREE_SHIPPING_THRESHOLD - subtotal
        percent = int((subtotal / self.FREE_SHIPPING_THRESHOLD) * 100)
        return percent, needed

    def to_dict(self):
        items_list = []
        for item in self:
            prod = item['product']
            items_list.append({
                'id': prod.id,
                'name': prod.name,
                'slug': prod.slug,
                'price': float(item['price']),
                'formatted_price': f"₦{item['price']:,.2f}",
                'quantity': item['quantity'],
                'total_price': float(item['total_price']),
                'formatted_total': f"₦{item['total_price']:,.2f}",
                'image_url': prod.image_url,
                'category': prod.category.name,
                'volume': prod.volume,
            })
        
        progress_pct, amount_needed = self.get_free_shipping_progress()
        return {
            'items': items_list,
            'count': len(self),
            'subtotal': float(self.get_subtotal()),
            'formatted_subtotal': f"₦{self.get_subtotal():,.2f}",
            'discount': float(self.get_discount()),
            'formatted_discount': f"₦{self.get_discount():,.2f}",
            'shipping': float(self.get_shipping_cost()),
            'formatted_shipping': 'FREE' if self.get_shipping_cost() == 0 else f"₦{self.get_shipping_cost():,.2f}",
            'total': float(self.get_total_price()),
            'formatted_total': f"₦{self.get_total_price():,.2f}",
            'coupon_code': self.coupon_code,
            'free_shipping_progress': progress_pct,
            'free_shipping_needed': float(amount_needed),
        }
