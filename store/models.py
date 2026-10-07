from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='ph-drop', help_text='Phosphor icon class name')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:catalog_by_category', kwargs={'category_slug': self.slug})

class Product(models.Model):
    BADGE_CHOICES = [
        ('', 'None'),
        ('limited', 'Limited Edition'),
        ('new', 'New Arrival'),
        ('award', 'Award Winner'),
        ('sale', 'On Sale'),
        ('rare', 'Rare Cellar Find'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Original price before discount if on sale')
    currency = models.CharField(max_length=10, default='₦')
    short_description = models.TextField(help_text='Short description shown in catalog cards')
    full_description = models.TextField(blank=True, help_text='Detailed overview for product details')
    image_url = models.URLField(max_length=800, help_text='Primary high-res image URL')
    secondary_image_url = models.URLField(max_length=800, blank=True, help_text='Secondary tasting/bottle image')
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True)
    badge_text = models.CharField(max_length=50, blank=True, help_text='Custom badge display text like "Limited", "97 pts", "Award Winner"')
    
    # Spirit Specifications
    abv = models.DecimalField(max_digits=4, decimal_places=1, default=40.0, help_text='Alcohol by Volume (%)')
    volume = models.CharField(max_length=20, default='750ml')
    age_years = models.PositiveIntegerField(null=True, blank=True, help_text='Cask aging in years (e.g., 12, 18, 25)')
    origin = models.CharField(max_length=150, default='Highlands, Scotland', help_text='Region and Country of origin')
    
    # Tasting Notes
    nose_notes = models.CharField(max_length=255, blank=True, default='Caramelized orange, vanilla bean, subtle oak smoke', help_text='Aromas on the nose')
    palate_notes = models.CharField(max_length=255, blank=True, default='Rich toffee, dark cocoa, baked orchard fruit, gentle peat', help_text='Flavors on the palate')
    finish_notes = models.CharField(max_length=255, blank=True, default='Long, warming spice with lingering honeyed tobacco', help_text='Finish characteristics')
    
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.8)
    review_count = models.PositiveIntegerField(default=12)
    stock = models.PositiveIntegerField(default=25)
    is_featured = models.BooleanField(default=False, help_text='Show in Curated Selection on Home Page')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.badge_text and self.badge:
            badge_dict = dict(self.BADGE_CHOICES)
            self.badge_text = badge_dict.get(self.badge, '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (₦{self.price:,.2f})"

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})

    @property
    def is_on_sale(self):
        return bool(self.original_price and self.original_price > self.price)

    @property
    def discount_percent(self):
        if self.is_on_sale:
            saving = self.original_price - self.price
            return int((saving / self.original_price) * 100)
        return 0

    @property
    def formatted_price(self):
        return f"{self.currency}{self.price:,.2f}"

    @property
    def formatted_original_price(self):
        if self.original_price:
            return f"{self.currency}{self.original_price:,.2f}"
        return ""

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField()
    is_verified_buyer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.author_name} for {self.product.name} ({self.rating}/5)"

class Order(models.Model):
    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Preparing', 'Cellar Preparation'),
        ('Shipped', 'Dispatched for Courier Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    customer_name = models.CharField(max_length=120)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=30)
    shipping_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    delivery_notes = models.TextField(blank=True)
    
    payment_method = models.CharField(max_length=50, default='Credit Card')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Processing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"AUR-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer_name} (₦{self.total:,.2f})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_image = models.URLField(max_length=800, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    item_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} in #{self.order.order_number}"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email

class ContactInquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    inquiry_type = models.CharField(max_length=50, default='General Inquiry', choices=[
        ('General Inquiry', 'General Inquiry'),
        ('Private Tasting', 'Private Tasting & Event'),
        ('Cellar Advisory', 'Cellar Advisory & Rare Spirits'),
        ('Wholesale', 'Wholesale & Hospitality'),
    ])
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Contact Inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} from {self.name} ({self.email})"

class Coupon(models.Model):
    PERCENT_CHOICES = [
        (10, '10% Discount'),
        (20, '20% Discount'),
        (50, '50% Discount'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Admin-issued VIP voucher code")
    discount_percent = models.PositiveSmallIntegerField(
        choices=PERCENT_CHOICES, 
        default=10, 
        help_text="Discount percentage (limited strictly to 10%, 20%, or 50%)"
    )
    recipient_email = models.EmailField(blank=True, help_text="Email of the user this voucher is generated for and sent to")
    recipient_name = models.CharField(max_length=120, blank=True, help_text="Optional recipient name")
    description = models.CharField(max_length=255, blank=True, help_text="Internal notes or reason for issuing")
    is_active = models.BooleanField(default=True, help_text="Whether this coupon can currently be redeemed")
    max_uses = models.PositiveIntegerField(default=1, help_text="Maximum number of times this code can be redeemed (0 for unlimited)")
    times_used = models.PositiveIntegerField(default=0, help_text="Number of times redeemed")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        if not self.is_active:
            return False, "This VIP voucher code is currently deactivated."
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False, "This VIP voucher code has already been redeemed."
        return True, "Valid voucher"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"AURA-{self.discount_percent}-{uuid.uuid4().hex[:6].upper()}"
        else:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        email_str = f" for {self.recipient_email}" if self.recipient_email else ""
        return f"[{self.code}] {self.discount_percent}% Off{email_str} ({'Active' if self.is_active else 'Inactive'})"
