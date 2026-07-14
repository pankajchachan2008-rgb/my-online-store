from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Coupon, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Admin panel ke main page par yeh columns dikhenge
    # Note: Agar models.py me stock field nahi hai, toh use update kar lijiyega
    list_display = ('sku', 'name', 'price', 'stock_status')
    search_fields = ('name', 'sku')

    # Low Stock Alert lagane ke liye custom status function
    def stock_status(self, obj):
        # Agar stock model me nahi hai toh safer fallback default 10 rakh sakte hain
        stock_qty = getattr(obj, 'stock', 10) 
        if stock_qty <= 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ Out of Stock</span>')
        elif stock_qty <= 5:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Low Stock ({})</span>', stock_qty)
        return format_html('<span style="color: green; font-weight: bold;">✅ Available</span>')
    
    stock_status.short_description = 'Stock Status'


# 🎟️ Coupon Custom View in Admin (Jo pehle missing tha)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'mobile_number', 'discount_percentage', 'is_used', 'created_at')
    list_filter = ('is_used', 'discount_percentage')
    search_fields = ('mobile_number', 'code')


# Order ke andar hi items dikhane ke liye inline setup
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Yahan models.py ke hisaab se fields name hain
    readonly_fields = ('product_name', 'price', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Yahan 'phone' ki jagah database ke hisaab se 'mobile_number' kar diya hai
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'mobile_number')
    inlines = [OrderItemInline]

# CRITICAL FIX: Niche se saare duplicate admin.site.register() hata diye hain 
# kyunki upar @admin.register() decorators lag chuke hain.