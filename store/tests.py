from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from .models import Category, Product, ProductReview, Order, OrderItem, NewsletterSubscriber, ContactInquiry, Coupon
from .cart import Cart


class AuraSpiritsModelAndCartTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Whisky',
            slug='whisky',
            description='Fine handcrafted single malts'
        )
        self.product = Product.objects.create(
            name='Oak Reserve Bourbon',
            slug='oak-reserve-bourbon',
            category=self.category,
            price=Decimal('85.00'),
            original_price=Decimal('100.00'),
            currency='₦',
            short_description='Aged 12 years in charred American oak.',
            full_description='Crafted in small batches.',
            image_url='https://example.com/whisky.jpg',
            badge='limited',
            badge_text='Limited',
            abv=Decimal('45.0'),
            volume='750ml',
            age_years=12,
            origin='Kentucky, USA',
            stock=20,
            is_featured=True,
            rating=Decimal('4.8')
        )
        # Create Admin VIP Coupons
        self.coupon_10 = Coupon.objects.create(
            code='VIP10',
            discount_percent=10,
            recipient_email='collector@auraspirits.com',
            is_active=True
        )
        self.coupon_20 = Coupon.objects.create(
            code='VIP20',
            discount_percent=20,
            recipient_email='collector@auraspirits.com',
            is_active=True
        )
        self.coupon_50 = Coupon.objects.create(
            code='VIP50',
            discount_percent=50,
            recipient_email='collector@auraspirits.com',
            is_active=True
        )

    def test_product_properties(self):
        self.assertTrue(self.product.is_on_sale)
        self.assertEqual(self.product.discount_percent, 15)
        self.assertEqual(self.product.formatted_price, '₦85.00')
        self.assertEqual(self.product.formatted_original_price, '₦100.00')

    def test_home_page_status_and_content(self):
        response = self.client.get(reverse('store:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oak Reserve Bourbon')
        self.assertContains(response, 'Distilled to Perfection')
        self.assertContains(response, 'Aura')

    def test_catalog_page_filtering_and_search(self):
        # All catalog
        response = self.client.get(reverse('store:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oak Reserve Bourbon')

        # Category filter
        response = self.client.get(reverse('store:catalog_by_category', kwargs={'category_slug': 'whisky'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oak Reserve Bourbon')

        # Search query match
        response = self.client.get(reverse('store:catalog') + '?q=Oak')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oak Reserve Bourbon')

        # Search query non-match
        response = self.client.get(reverse('store:catalog') + '?q=NonExistentSpirit')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No spirits found')

    def test_product_detail_and_review(self):
        url = reverse('store:product_detail', kwargs={'slug': 'oak-reserve-bourbon'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kentucky, USA')
        self.assertContains(response, '45.0% ABV')

        # Submit review
        post_response = self.client.post(url, {
            'submit_review': '1',
            'author_name': 'Sir Arthur',
            'rating': '5',
            'title': 'Stunning complexity',
            'comment': 'Smooth and rich caramel notes.'
        }, follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertTrue(ProductReview.objects.filter(author_name='Sir Arthur').exists())

    def test_cart_api_operations_and_vip_coupons(self):
        # Add to cart (2 bottles @ 85.00 = 170.00)
        add_response = self.client.post(
            reverse('store:api_cart_add'),
            data=json.dumps({'product_id': self.product.id, 'quantity': 2}),
            content_type='application/json'
        )
        self.assertEqual(add_response.status_code, 200)
        data = add_response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart']['count'], 2)
        self.assertEqual(data['cart']['subtotal'], 170.0)

        # Update cart quantity to 1 bottle @ 85.00
        upd_response = self.client.post(
            reverse('store:api_cart_update'),
            data=json.dumps({'product_id': self.product.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(upd_response.status_code, 200)
        self.assertEqual(upd_response.json()['cart']['count'], 1)

        # Test invalid coupon
        invalid_coupon = self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': 'FAKEDISCOUNT'}),
            content_type='application/json'
        )
        self.assertEqual(invalid_coupon.status_code, 200)
        self.assertFalse(invalid_coupon.json()['success'])

        # Apply valid VIP 10% coupon (10% of 85.00 = 8.50)
        coupon_response = self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': 'VIP10'}),
            content_type='application/json'
        )
        self.assertEqual(coupon_response.status_code, 200)
        self.assertTrue(coupon_response.json()['success'])
        self.assertEqual(coupon_response.json()['cart']['discount'], 8.5)

        # Apply VIP 20% coupon (20% of 85.00 = 17.00)
        coupon_20_res = self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': 'VIP20'}),
            content_type='application/json'
        )
        self.assertEqual(coupon_20_res.status_code, 200)
        self.assertEqual(coupon_20_res.json()['cart']['discount'], 17.0)

        # Apply VIP 50% coupon (50% of 85.00 = 42.50)
        coupon_50_res = self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': 'VIP50'}),
            content_type='application/json'
        )
        self.assertEqual(coupon_50_res.status_code, 200)
        self.assertEqual(coupon_50_res.json()['cart']['discount'], 42.5)

        # Fetch cart data
        cart_data_response = self.client.get(reverse('store:api_cart_data'))
        self.assertEqual(cart_data_response.status_code, 200)
        self.assertEqual(cart_data_response.json()['coupon_code'], 'VIP50')

        # Test remove coupon by sending empty code
        remove_coupon_res = self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': ''}),
            content_type='application/json'
        )
        self.assertEqual(remove_coupon_res.status_code, 200)
        self.assertEqual(remove_coupon_res.json()['cart']['discount'], 0.0)
        self.assertIsNone(remove_coupon_res.json()['cart']['coupon_code'])

        # Remove from cart
        rem_response = self.client.post(
            reverse('store:api_cart_remove'),
            data=json.dumps({'product_id': self.product.id}),
            content_type='application/json'
        )
        self.assertEqual(rem_response.status_code, 200)
        self.assertEqual(rem_response.json()['cart']['count'], 0)

    def test_wishlist_api_toggle(self):
        toggle_response = self.client.post(
            reverse('store:api_wishlist_toggle'),
            data=json.dumps({'product_id': self.product.id}),
            content_type='application/json'
        )
        self.assertEqual(toggle_response.status_code, 200)
        self.assertTrue(toggle_response.json()['in_wishlist'])
        self.assertEqual(toggle_response.json()['count'], 1)

        # View wishlist
        wishlist_view_res = self.client.get(reverse('store:wishlist'))
        self.assertEqual(wishlist_view_res.status_code, 200)
        self.assertContains(wishlist_view_res, 'Oak Reserve Bourbon')

        # Untoggle
        untoggle_response = self.client.post(
            reverse('store:api_wishlist_toggle'),
            data=json.dumps({'product_id': self.product.id}),
            content_type='application/json'
        )
        self.assertFalse(untoggle_response.json()['in_wishlist'])
        self.assertEqual(untoggle_response.json()['count'], 0)

    def test_checkout_and_order_success(self):
        # Add product to cart
        self.client.post(
            reverse('store:api_cart_add'),
            data=json.dumps({'product_id': self.product.id, 'quantity': 1}),
            content_type='application/json'
        )

        # Apply 20% coupon
        self.client.post(
            reverse('store:api_apply_coupon'),
            data=json.dumps({'code': 'VIP20'}),
            content_type='application/json'
        )

        # Checkout post with typed location
        checkout_response = self.client.post(reverse('store:checkout'), {
            'customer_name': 'Lord Sterling',
            'customer_email': 'sterling@luxury.co.uk',
            'customer_phone': '+234 800 123 4567',
            'shipping_address': '10 Victoria Island Promenade',
            'city': 'Lagos',
            'state': 'Lagos State',
            'postal_code': '101241',
            'country': 'Nigeria',
            'payment_method': 'Direct Admin Settlement (Concierge Transfer)',
            'delivery_notes': 'Please ring the side cellar bell.'
        }, follow=True)

        self.assertEqual(checkout_response.status_code, 200)
        order = Order.objects.filter(customer_email='sterling@luxury.co.uk').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product_name, 'Oak Reserve Bourbon')
        self.assertEqual(order.coupon_code, 'VIP20')
        self.assertContains(checkout_response, 'Order Ticket')
        self.assertContains(checkout_response, order.order_number)

    def test_newsletter_and_contact(self):
        # Newsletter subscribe
        sub_response = self.client.post(
            reverse('store:api_newsletter_subscribe'),
            data=json.dumps({'email': 'collector@auraspirits.com'}),
            content_type='application/json'
        )
        self.assertEqual(sub_response.status_code, 200)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='collector@auraspirits.com').exists())

        # Contact submission
        contact_response = self.client.post(reverse('store:contact'), {
            'name': 'Lady Genevieve',
            'email': 'genevieve@estates.com',
            'subject': 'Private Tasting for 12',
            'inquiry_type': 'Private Tasting',
            'message': 'We would like to book the Speyside tasting room in December.'
        }, follow=True)
        self.assertEqual(contact_response.status_code, 200)
        self.assertTrue(ContactInquiry.objects.filter(email='genevieve@estates.com').exists())
