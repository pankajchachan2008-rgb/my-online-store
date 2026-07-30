from django.contrib import admin
from django.http import HttpResponse
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth # 🌟 NAYA: Chart ke liye import add kiya

from .models import (
    Category, Brand, Product, Coupon, Order, OrderItem,
    CustomerProfile, Banner, ProductVariant, Review, StoreSetting
)

# -----------------------------
# 🌟 CUSTOM ERP DASHBOARD INTEGRATION
# -----------------------------
# Premium Admin Headers
admin.site.site_header = "CGSMART ERP Dashboard"
admin.site.site_title = "CGSMART Admin"
admin.site.index_title = "Welcome to CGSMART Admin"

# Default get_urls ko save karke usme apna naya dashboard URL jodna
original_get_urls = admin.site.get_urls

def custom_get_urls():
    urls = original_get_urls()
    custom_urls = [
        path('dashboard/', admin.site.admin_view(dashboard_view), name="dashboard"),
    ]
    return custom_urls + urls

def dashboard_view(request):
    # Sales summary
    sales_total = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    order_count = Order.objects.count()

    # Top products (OrderItem se sum nikalna kyunki product_name CharField hai)
    top_products = OrderItem.objects.values('product_name').annotate(sold=Sum('quantity')).order_by('-sold')[:5]

    # Coupon usage
    coupon_usage = Coupon.objects.filter(is_active=True).count()

    # 📈 Monthly sales trend (Chart Data)
    monthly_sales = (
        Order.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'))
        .order_by('month')
    )

    context = dict(
        admin.site.each_context(request),
        sales_total=sales_total,
        order_count=order_count,
        top_products=top_products,
        coupon_usage=coupon_usage,
        monthly_sales=list(monthly_sales), # 🌟 NAYA: Chart ka data template mein bheja
    )
    return TemplateResponse(request, "admin/dashboard.html", context)

# Naye URLs ko default admin par set karna
admin.site.get_urls = custom_get_urls


# -----------------------------
# Basic Models Registration
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',) 
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',) 
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