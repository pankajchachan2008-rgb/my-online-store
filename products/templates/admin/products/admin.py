from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Category, Product, Coupon, Order, OrderItem, CustomerProfile, Banner, ProductVariant

# ==========================================
# 1. Basic Model Registrations
# ==========================================
admin.site.register(Category)
admin.site.register(CustomerProfile)
admin.site.register(Banner)  
admin.site.register(ProductVariant)

# ==========================================
# 2. Product Admin (with Variants Inline)
# ==========================================
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'price') 
    inlines = [ProductVariantInline]

# ==========================================
# 3. Coupon Admin
# ==========================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'mobile_number', 'discount_percentage', 'is_used']

# ==========================================
# 4. Order Admin & Shipping Label Action
# ==========================================
@admin.action(description="Print Shipping Labels (4x6 Thermal Format)")
def print_shipping_labels(modeladmin, request, queryset):
    template_path = 'admin/products/shipping_label.html'
    context = {'orders': queryset}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="shipping_labels.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating label: <pre>' + html + '</pre>')
    return response

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'created_at')
    inlines = [OrderItemInline]
    actions = [print_shipping_labels]

# ==========================================
# 5. User Profile Inline & UserAdmin
# ==========================================
class ProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)