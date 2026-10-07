from django.contrib import admin
from .models import Category, Product, ProductReview, Order, OrderItem, NewsletterSubscriber, ContactInquiry, Coupon


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ['created_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    ordering = ['order', 'name']

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'original_price', 'badge', 'abv', 'stock', 'rating', 'is_featured', 'is_active']
    list_filter = ['category', 'badge', 'is_featured', 'is_active', 'abv', 'created_at']
    list_editable = ['price', 'original_price', 'stock', 'is_featured', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'short_description', 'full_description', 'origin', 'nose_notes', 'palate_notes']
    inlines = [ProductReviewInline]
    fieldsets = (
        ('General Information', {
            'fields': ('name', 'slug', 'category', 'price', 'original_price', 'currency', 'stock', 'is_featured', 'is_active')
        }),
        ('Imagery & Badges', {
            'fields': ('image_url', 'secondary_image_url', 'badge', 'badge_text')
        }),
        ('Spirit Specifications', {
            'fields': ('abv', 'volume', 'age_years', 'origin')
        }),
        ('Tasting Profile', {
            'fields': ('short_description', 'full_description', 'nose_notes', 'palate_notes', 'finish_notes', 'rating', 'review_count')
        }),
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'price', 'quantity', 'item_total']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'customer_email', 'total', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'shipping_address', 'city']
    readonly_fields = ['order_number', 'subtotal', 'shipping_cost', 'discount', 'total', 'coupon_code', 'created_at', 'updated_at']
    inlines = [OrderItemInline]

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'author_name', 'rating', 'title', 'is_verified_buyer', 'created_at']
    list_filter = ['rating', 'is_verified_buyer', 'created_at']
    search_fields = ['author_name', 'title', 'comment', 'product__name']

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'is_active']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']

@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'inquiry_type', 'is_resolved', 'created_at']
    list_filter = ['inquiry_type', 'is_resolved', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_resolved']

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'recipient_email', 'recipient_name', 'is_active', 'times_used', 'max_uses', 'created_at']
    list_filter = ['discount_percent', 'is_active', 'created_at']
    search_fields = ['code', 'recipient_email', 'recipient_name', 'description']
    list_editable = ['is_active']
    actions = ['send_voucher_email', 'deactivate_coupons', 'activate_coupons']
    fieldsets = (
        ('Voucher Details', {
            'fields': ('code', 'discount_percent', 'is_active', 'description')
        }),
        ('User Email & Recipient', {
            'fields': ('recipient_email', 'recipient_name'),
            'description': 'Specify user email if you want to generate and issue this exclusive voucher to a specific customer.'
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'times_used', 'expires_at')
        }),
    )

    def send_voucher_email(self, request, queryset):
        from django.core.mail import send_mail
        from django.conf import settings
        
        sent_count = 0
        for coupon in queryset:
            if coupon.recipient_email:
                subject = f"Exclusive {coupon.discount_percent}% VIP Cellar Voucher - Aura Spirits"
                message = (
                    f"Dear {coupon.recipient_name or 'VIP Member'},\n\n"
                    f"Aura Spirits management has issued an exclusive {coupon.discount_percent}% cellar discount voucher for your account.\n\n"
                    f"Your Exclusive Voucher Code: {coupon.code}\n"
                    f"Discount Tier: {coupon.discount_percent}% Off Entire Order\n\n"
                    f"Apply this code at checkout on Aura Spirits to enjoy your cellar privilege.\n\n"
                    f"Warm regards,\n"
                    f"Aura Spirits Cellar Management"
                )
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'concierge@auraspirits.com',
                        [coupon.recipient_email],
                        fail_silently=True
                    )
                    sent_count += 1
                except Exception:
                    pass
        self.message_user(request, f"Voucher code email successfully dispatched to {sent_count} recipient(s).")
    send_voucher_email.short_description = "Send selected voucher code(s) to recipient email"

    def deactivate_coupons(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected vouchers deactivated.")
    deactivate_coupons.short_description = "Deactivate selected vouchers"

    def activate_coupons(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected vouchers activated.")
    activate_coupons.short_description = "Activate selected vouchers"
