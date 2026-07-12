from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Product Name")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU/Barcode")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price (INR)")
    stock = models.IntegerField(default=0, verbose_name="Current Stock")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image = models.ImageField(upload_to='product_photos/', blank=True, null=True, verbose_name="Product Image")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

class Order(models.Model):
    customer_name = models.CharField(max_length=255, verbose_name="Customer Name")
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    address = models.TextField(verbose_name="Shipping Address")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Pending') # Pending, Shipped, Delivered

    def __str__(self):
        return f"Order #{self.id} by {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"