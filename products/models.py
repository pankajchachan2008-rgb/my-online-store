from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary_storage.storage import VideoMediaCloudinaryStorage, MediaCloudinaryStorage
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.category.name} -> {self.name}"

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    
    color = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Black, White, Red, Blue")
    size = models.CharField(max_length=50, blank=True, null=True, help_text="General Size e.g., S, M, L, XL (Filter ke liye)")

    image = models.ImageField(
        upload_to='products/', 
        storage=MediaCloudinaryStorage(), 
        blank=True, 
        null=True
    )
    
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
    order_id = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='Pending')
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    # 🌟 FIXED SYNTAX ERROR HERE
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)
    payment_status = models.CharField(
        max_length=20, 
        default='Pending', 
        choices=[('Pending', 'Pending'), ('Paid', 'Paid')]
    )
    delivery_boy = models.ForeignKey(
        'DeliveryBoy', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_orders', 
        help_text="Is order ko kaun deliver karega?"
    )
    
    # Courier Tracking Fields
    courier_name = models.CharField(max_length=100, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.order_id:
            # 🌟 FIXED: Convert UUID to string before slicing
            self.order_id = f"CG-{str(uuid.uuid4().int)[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer_name}"

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

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_mobile_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    default_address = models.TextField(blank=True, null=True)

    def get_profile_completion_percentage(self):
        score = 0
        if self.user.first_name and self.user.last_name: score += 20
        if self.user.email: score += 20
        if self.mobile_number: score += 20
        if self.profile_photo: score += 20
        if self.is_email_verified and self.is_mobile_verified: score += 20
        return score

    def __str__(self):
        return f"{self.user.username}'s Profile"

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

class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE) 
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at'] 

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
    image = models.ImageField(
        upload_to='banners/', 
        blank=True, 
        null=True, 
        help_text="Sirf Image yahan upload karein (PNG/JPG)"
    )
    animated_file = models.FileField(
        upload_to='banners/videos/', 
        help_text="Sirf Video yahan upload karein (MP4)",
        storage=VideoMediaCloudinaryStorage(), 
        blank=True, 
        null=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='banners',
        help_text="Agar select karein, to banner click karne par is category ke products dikhenge"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    image = models.ImageField(upload_to='review_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} Stars)"

class StoreSetting(models.Model):
    store_name = models.CharField(max_length=255, default="Chachan General Store")
    tagline = models.CharField(max_length=255, default="Premium Corporate Retail & Essentials", blank=True, null=True)
    owner_name = models.CharField(max_length=100, default="Proprietor", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True, default="Nohar, Rajasthan")
    gstin = models.CharField(max_length=50, blank=True, null=True, help_text="GST Number")
    receipt_footer = models.CharField(max_length=255, default="Thank you, please visit again!")

    def __str__(self):
        return self.store_name

class CustomerLedger(models.Model):
    customer_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    TRANSACTION_TYPES = (
        ('DEBIT', 'Udhaar (Given)'),
        ('CREDIT', 'Jama (Received)'),
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True, default='POS Sale / Khata Entry')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.transaction_type} - ₹{self.amount}"

class ServiceablePincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True, db_index=True)
    city_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100, default='Nohar Main Hub')
    is_serviceable = models.BooleanField(default=True)
    delivery_estimate = models.CharField(max_length=100, default='10 Mins - 1 Hour')
    shipping_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.pincode} - {self.city_name} ({self.branch_name})"

class Expense(models.Model):
    EXPENSE_CATEGORIES = (
        ('Salary', 'Staff Salary'),
        ('Bills', 'Electricity/Water/Internet Bills'),
        ('Maintenance', 'Shop Maintenance/Repair'),
        ('Tea/Snacks', 'Chai & Snacks'),
        ('Fuel', 'Petrol/Travel'),
        ('Other', 'Other/Miscellaneous'),
    )
    
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, help_text="Kharcha kis cheez ke liye hua?")
    date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category} - ₹{self.amount} on {self.date}"

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.company_name:
            return f"{self.name} ({self.company_name})"
        return self.name

class SupplierLedger(models.Model):
    TRANSACTION_TYPES = (
        ('DEBIT', 'Payment Given (Jama kiya)'),
        ('CREDIT', 'Goods Received (Maal Udhaar liya)'),
    )
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='ledger_entries')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, help_text="Bill No. ya Payment details")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.supplier.name} - {self.get_transaction_type_display()} - ₹{self.amount}"

class DeliveryBoy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15, unique=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True, help_text="Bike ya Gaadi ka number")
    is_active = models.BooleanField(default=True, help_text="Agar staff chhutti par hai toh isko untick karein")
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.mobile_number}"