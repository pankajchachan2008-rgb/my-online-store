from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Category, Brand, Product, Coupon, Order, OrderItem, CustomerProfile, Banner, ProductVariant, Review
from .models import StoreSetting
from django.utils.html import format_html

# Basic Models Registration
admin.site.register(Category)
admin.site.register(Brand)  # 🌟 NAYA: Brand model yahan register kiya
admin.site.register(CustomerProfile)
admin.site.register(Banner)  
admin.site.register(ProductVariant)

# Product Variant ko Inline banaya taaki Product ke andar hi add kar sakein
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 🌟 NAYA: 'product_image' ko list_display mein 2nd number par add kiya
    list_display = ('sku', 'product_image', 'name', 'category', 'brand', 'price', 'last_moment_discount') 
    
    search_fields = ('name', 'sku', 'category__name', 'brand__name')
    list_filter = ('category', 'brand')
    list_select_related = ('category', 'brand')
    
    # Category, brand aur prices yahan se directly edit honge
    list_editable = ('category', 'brand', 'price', 'last_moment_discount')
    
    inlines = [ProductVariantInline]
    list_per_page = 15  # Server crash se bachane ke liye limit

    # 🌟 NAYA FUNCTION: Har product ki choti photo dikhane ke liye
    def product_image(self, obj):
        if obj.image:
            # 50x50 size ki round-corner photo dikhayega
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    
    # Admin panel mein column ka naam 'Image' set karne ke liye
    product_image.short_description = 'Image'

@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'store_phone', 'gstin']

# Updated Coupon Admin
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'min_order_amount', 'is_active', 'valid_to']
    list_filter = ['is_active']
    search_fields = ['code']

# Custom Admin Action for Shipping Labels
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

# Order Items ko Order ke andar Inline dikhane ke liye
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_name', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at') 
    search_fields = ('customer_name', 'mobile_number', 'id') 
    inlines = [OrderItemInline]
    actions = [print_shipping_labels]

# Custom User Admin setup (Profile ko inline merge karne ke liye)
class ProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username')