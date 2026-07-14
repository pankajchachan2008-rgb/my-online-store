from django.db import models
from django.contrib.auth.models import User

# 📦 1. Product Model (Website ke items save karne ke liye)
class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True, default="PROD-000")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

# 🎟️ 2. Coupon Model (Scratch Card Data Save Karne Ke Liye)
class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    mobile_number = models.CharField(max_length=15)
    discount_percentage = models.IntegerField(default=8) # 8% ya 10%
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.mobile_number} ({self.discount_percentage}%)"

# 📦 3. Order Model (ERP me Data Bhejne Ke Liye)
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending') # Pending, Confirmed, Completed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.mobile_number} (₹{self.total_amount})"

# 🛒 4. Order Items Model (Ek Order me kya-kya samaan hai)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"