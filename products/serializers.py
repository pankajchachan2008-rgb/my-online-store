from rest_framework import serializers
from .models import Order, OrderItem, Product

# 🛒 1. Order Items Serializer
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:  # <-- YAHAN 'Meta' HONA CHAHIYE (M capital)
        model = OrderItem
        fields = ['product_name', 'price', 'quantity']

# 📦 2. Main Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    # ⚠️ VERIFY: this only works if OrderItem's ForeignKey to Order has
    # related_name='items' in models.py (e.g. order = models.ForeignKey(Order,
    # related_name='items', ...)). If it doesn't, DRF will raise an
    # AttributeError at request time ("Order has no attribute 'items'").
    # If your FK uses the default reverse name instead, change this to:
    #   items = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')
    items = OrderItemSerializer(many=True, read_only=True)
    # 🌟 FIX: without default=None, this key was silently OMITTED from the
    # JSON entirely whenever an order had no coupon applied (applied_coupon
    # is None) — inconsistent API shape that could break any client code
    # expecting the key to always exist. Now it always appears, as null.
    coupon_code = serializers.CharField(source='applied_coupon.code', read_only=True, default=None, allow_null=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'mobile_number', 'address', 'total_amount', 'status', 'coupon_code', 'created_at', 'items']

# 🏷️ 3. Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'price']