from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Admin panel ke main page par yeh columns dikhenge
    list_display = ('name', 'sku', 'price', 'stock', 'stock_status')
    search_fields = ('name', 'sku')
    list_filter = ('stock',)

    # Low Stock Alert lagane ke liye custom status function
    def stock_status(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ Out of Stock</span>')
        elif obj.stock <= 5:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Low Stock ({})</span>', obj.stock)
        return format_html('<span style="color: green;">✅ Available ({})</span>', obj.stock)
    
    stock_status.short_description = 'Stock Status'


# Order ke andar hi items dikhane ke liye inline setup
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone')
    inlines = [OrderItemInline]