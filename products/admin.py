from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.html import format_html

from .models import (
    Category, Brand, Product, Coupon, Order, OrderItem,
    CustomerProfile, Banner, ProductVariant, Review, StoreSetting
)

# -----------------------------
# Basic Models Registration
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',) # ⚠️ 'created_at' hata diya kyunki models.py mein nahi tha
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',) # ⚠️ 'created_at' hata diya kyunki models.py mein nahi tha
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(CustomerProfile)
admin.site.register(Banner)
admin.site.register(ProductVariant)

# -----------------------------
# Product Variant Inline
# -----------------------------
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True

# -----------------------------
# Product Admin
# -----------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'product_image', 'name',
        'category', 'brand', 'price', 'last_moment_discount'
    )
    search_fields = ('name', 'sku', 'category__name', 'brand__name')
    list_filter = ('category', 'brand')
    list_select_related = ('category', 'brand')
    
    # 🌟 WAPAS ADD KIYA: category aur brand taaki aap bahar se ek sath update kar sakein
    list_editable = ('category', 'brand', 'price', 'last_moment_discount') 
    
    readonly_fields = ('sku',)
    inlines = [ProductVariantInline]
    list_per_page = 20

    def product_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px; height:50px; '
                'object-fit:cover; border-radius:5px;" />',
                obj.image.url
            )
        return "No Image"
    product_image.short_description = 'Image'

# -----------------------------
# Store Settings Admin
# -----------------------------
@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'store_phone', 'gstin']

# -----------------------------
# Coupon Admin
# -----------------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'min_order_amount', 'is_active', 'valid_to']
    list_filter = ['is_active', 'valid_to']
    search_fields = ['code']
    readonly_fields = ('code',)

# -----------------------------
# Custom Admin Action: Shipping Labels
# -----------------------------
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
        return HttpResponse('Error generating label')
    return response

# -----------------------------
# Order Items Inline
# -----------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

# -----------------------------
# Order Admin
# -----------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'mobile_number', 'id')
    inlines = [OrderItemInline]
    actions = [print_shipping_labels]
    list_editable = ('status',)

# -----------------------------
# Custom User Admin
# -----------------------------
class ProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# -----------------------------
# Review Admin
# -----------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')