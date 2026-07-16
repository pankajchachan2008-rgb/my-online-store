from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
# 👇 FIX: Yahan Banner ko import list mein add kar diya gaya hai
from .models import Category, Product, Coupon, Order, OrderItem, CustomerProfile, Banner

# 🌟 Category, OrderItem, CustomerProfile, aur Banner ko normally register karein
admin.site.register(Category)
admin.site.register(OrderItem)
admin.site.register(CustomerProfile)
admin.site.register(Banner)  # 👈 Banner ab Admin Panel mein show hoga

# 👇 Jo models niche @admin.register() se custom design ho rahe hain, 
# unhe upar wale simple register se hata diya gaya hai.

# 1. Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'price') 

# 2. Coupon Admin
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'mobile_number', 'discount_percentage', 'is_used']

# 3. Order Admin with Inlines
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'created_at')
    inlines = [OrderItemInline]

# 4. CRITICAL: UserAdmin Registration (Fixes 500 Error)
class ProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)