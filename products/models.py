from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
# 🌟 NAYA: MediaCloudinaryStorage ko import mein add kiya
from cloudinary_storage.storage import VideoMediaCloudinaryStorage, MediaCloudinaryStorage

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# 👇 🌟 YEH NAYA SUBCATEGORY MODEL ADD KIYA HAI 🌟 👇
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.category.name} -> {self.name}"
# 👆 -------------------------------------------- 👆

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # 👇 🌟 NAYA: PRODUCT KO SUBCATEGORY SE JODNE WALI FIELD 🌟 👇
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    # 👆 ---------------------------------------------------- 👆
    
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    description = models.TextField(blank=True, null=True)
    
    # MRP Field add kiya for real calculations
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    
    # 🌟 GAMECHANGER: Cloudinary Storage add kiya taaki images kabhi delete na hon
    image = models.ImageField(
        upload_to='products/', 
        storage=MediaCloudinaryStorage(), 
        blank=True, 
        null=True
    )
    
    # 🌟 GAMECHANGER FIELD
    last_moment_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        help_text="Checkout par surprise discount dene ke liye amount set karein"
    )

    @property
    def discount_percentage(self):
        if self.mrp and self.price and self.mrp > self.price:
            return int(((self.mrp - self.price) / self.mrp) * 100)
        return 0

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size_name = models.CharField(max_length=50)  
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} ({self.size_name})"

# 🌟 NAYA: Universal Promo Code Model
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="e.g., WELCOME50, DIWALI20")
    discount_percentage = models.PositiveIntegerField(help_text="Discount in % (e.g., 10 for 10%)")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount limit (e.g., 500)")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum cart value to apply this coupon")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% OFF"

class Order(models.Model):
    STATUS_CHOICES = (
        ('Processing', 'Processing'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Processing')
    # 🌟 NAYA: Editable Tracking Details
    courier_name = models.CharField(max_length=100, blank=True, null=True, help_text="E.g., Trackon, Delivery, etc.")
    tracking_id = models.CharField(max_length=100, blank=True, null=True, help_text="Courier Tracking ID/AWB")
    tracking_url = models.URLField(max_length=500, blank=True, null=True, help_text="Paste direct tracking link here")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

# 1. Upgarded CustomerProfile Model 
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    
    # 🌟 Naye Premium Features
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_mobile_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    # Old field (Backward compatibility ke liye chhod rahe hain)
    default_address = models.TextField(blank=True, null=True)

    def get_profile_completion_percentage(self):
        """Profile completion calculate karne ka smart logic"""
        score = 0
        if self.user.first_name and self.user.last_name: score += 20
        if self.user.email: score += 20
        if self.mobile_number: score += 20
        if self.profile_photo: score += 20
        if self.is_email_verified and self.is_mobile_verified: score += 20
        return score

    def __str__(self):
        return f"{self.user.username}'s Profile"


# 2. NAYA Address Model (Multiple Addresses ke liye)
class Address(models.Model):
    ADDRESS_TYPES = (
        ('Home', 'Home (All day delivery)'),
        ('Office', 'Office (Delivery between 10 AM - 5 PM)'),
        ('Other', 'Other')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100, help_text="Full name of the receiver")
    mobile_number = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    locality = models.CharField(max_length=200)
    full_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='Home')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.city}"


# 3. NAYA RecentlyViewed Model 
class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at'] # Sabse naya view sabse upar

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_superuser and not instance.is_staff:
        CustomerProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'customerprofile'):
        instance.customerprofile.save()

class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    
    # 🌟 Image Banner ke liye (PNG/JPG) - Yeh default Image Storage use karega
    image = models.ImageField(
        upload_to='banners/', 
        blank=True, 
        null=True, 
        help_text="Sirf Image yahan upload karein (PNG/JPG)"
    )
    
    # 🌟 Video Banner ke liye (MP4) - Yeh strict Video Storage use karega
    animated_file = models.FileField(
        upload_to='banners/videos/', 
        help_text="Sirf Video yahan upload karein (MP4)",
        storage=VideoMediaCloudinaryStorage(), 
        blank=True, 
        null=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🌟 YEH FIX HUA HAI TAQI BINA TITLE WALE BANNERS CRASH NA HON 🌟
    def __str__(self):
        if self.title:
            return self.title
        return f"Banner #{self.id}"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

# 🌟 NAYA: Wallet Transaction History Model
class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('CREDIT', 'Credit (Money Added)'),
        ('DEBIT', 'Debit (Money Used)'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, help_text="e.g., Used for Order #123, Welcome Bonus, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} | {self.transaction_type} | ₹{self.amount}"

# 🌟 NAYA: Store Settings Model (Admin se Invoice Customize karne ke liye)
class StoreSetting(models.Model):
    company_name = models.CharField(max_length=255, default="Chachan General Store")
    tagline = models.CharField(max_length=255, default="Premium Corporate Retail & Essentials")
    store_address = models.TextField(blank=True, null=True, help_text="Full address to print on Bill of Supply")
    store_phone = models.CharField(max_length=20, blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True, help_text="GST Number")
    
    def __str__(self):
        return "Store Configuration Settings"

class OTPVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} Stars)"