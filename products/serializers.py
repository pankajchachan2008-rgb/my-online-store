from rest_framework import serializers
from .models import Order, OrderItem, Product

# 🛒 1. Order Items Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:  # <-- YAHAN 'Meta' HONA CHAHIYE (M capital)
        model = OrderItem
        fields = ['product_name', 'price', 'quantity']

# 📦 2. Main Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    coupon_code = serializers.CharField(source='applied_coupon.code', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'mobile_number', 'address', 'total_amount', 'status', 'coupon_code', 'created_at', 'items']

# 🏷️ 3. Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'price']