import pandas as pd
import re
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth 
from django.contrib import messages
from django.utils.text import slugify

# Apne models import karein
from .models import ServiceablePincode
from .models import Expense, Supplier, SupplierLedger
from .models import DeliveryBoy

from .models import (
    Category, Brand, Product, Coupon, Order, OrderItem,
    CustomerProfile, Banner, ProductVariant, Review, StoreSetting, ProductImage,
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
        monthly_sales=list(monthly_sales), 
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
admin.site.register(Expense)
admin.site.register(Supplier)
admin.site.register(SupplierLedger)


# -----------------------------
# 🛵 Delivery Boy Admin (Premium)
# -----------------------------
@admin.register(DeliveryBoy)
class DeliveryBoyAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile_number', 'vehicle_number', 'is_active', 'joined_date')
    list_filter = ('is_active',)
    search_fields = ('name', 'mobile_number', 'vehicle_number')
    list_editable = ('is_active',)


# -----------------------------
# Product Variant & Image Gallery Inlines
# -----------------------------
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    show_change_link = True

# 🌟 NAYA: Multiple Photos upload karne ke liye inline block
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3 # Ek baar mein 3 extra photo upload karne ki jagah dega
    show_change_link = True


# -----------------------------
# Product Admin (With Bulk Excel Import Automation)
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
    
    list_editable = ('category', 'brand', 'price', 'last_moment_discount') 
    
    readonly_fields = ('sku',)
    # 🌟 YAHAN ProductImageInline ko add kar diya gaya hai
    inlines = [ProductVariantInline, ProductImageInline]
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

    # Admin mein Excel Import ka Custom URL jorna
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-excel-import/', self.admin_site.admin_view(self.excel_import_view), name='product_bulk_excel_import'),
        ]
        return custom_urls + urls

    # Excel processing view jo spellings theek karega aur auto-create karega
    def excel_import_view(self, request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            try:
                if excel_file.name.endswith('.csv'):
                    df = pd.read_csv(excel_file)
                else:
                    df = pd.read_excel(excel_file)

                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        raw_name = str(row.get('name', ''))
                        if not raw_name or raw_name == 'nan':
                            continue
                        
                        # 1. Text Cleaning & Auto Spelling Fix (Title Case & Spacing)
                        clean_name = re.sub(r'\s+', ' ', raw_name).strip().title()
                        brand_name = re.sub(r'\s+', ' ', str(row.get('brand', 'General'))).strip().title()
                        category_name = re.sub(r'\s+', ' ', str(row.get('category', 'Essentials'))).strip().title()

                        # 2. Auto-Create or Fetch Brand & Category (Groups)
                        brand_obj, _ = Brand.objects.get_or_create(name=brand_name)
                        category_obj, _ = Category.objects.get_or_create(name=category_name)

                        # 3. Parsing numbers safely
                        price = float(row.get('price', 0))
                        mrp = float(row.get('mrp', price))
                        stock = int(row.get('stock', 10))
                        image_url = str(row.get('image_url', ''))

                        # 4. Prevent Duplicates using Slug / SKU update or create
                        product_slug = slugify(clean_name)

                        Product.objects.update_or_create(
                            slug=product_slug,
                            defaults={
                                'name': clean_name,
                                'brand': brand_obj,
                                'category': category_obj,
                                'price': price,
                                'mrp': mrp,
                                'stock': stock,
                                'image': image_url if image_url != 'nan' else '',
                            }
                        )
                        success_count += 1
                    except Exception as row_err:
                        error_count += 1

                messages.success(request, f"✨ Successfully imported/updated {success_count} products! (Errors: {error_count})")
                return HttpResponseRedirect("../")

            except Exception as e:
                messages.error(request, f"❌ Error reading file: {e}")

        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk Import Products via Excel',
        }
        return TemplateResponse(request, "admin/excel_import_form.html", context)


# -----------------------------
# Store Settings Admin
# -----------------------------
@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'phone', 'gstin')


# -----------------------------
# Coupon Admin
# -----------------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percentage', 'min_order_amount', 'is_active', 'valid_to']
    list_filter = ['is_active', 'valid_to']
    search_fields = ['code']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('code',)
        return ()


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
    list_display = ('id', 'customer_name', 'mobile_number', 'total_amount', 'status', 'delivery_boy', 'created_at')
    list_filter = ('status', 'delivery_boy', 'created_at')
    search_fields = ('customer_name', 'mobile_number', 'id')
    inlines = [OrderItemInline]
    actions = [print_shipping_labels]
    list_editable = ('status', 'delivery_boy')


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


# -----------------------------
# Serviceable Pincode Admin
# -----------------------------
@admin.register(ServiceablePincode)
class ServiceablePincodeAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'city_name', 'branch_name', 'is_serviceable', 'delivery_estimate')
    search_fields = ('pincode', 'city_name', 'branch_name')
    list_filter = ('is_serviceable', 'city_name', 'branch_name')