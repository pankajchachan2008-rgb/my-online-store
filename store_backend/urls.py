from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views
from products.views import login_request_otp, login_verify_otp

# Views functions imports
from products.views import (
    product_list, add_to_cart, cart_detail, checkout_page,
    check_coupon_ajax, about_page, contact_page,
    custom_logout, register_page, profile_page,
    make_admin, trigger_import,
    get_pending_orders_api, update_order_status_api, sync_products_from_erp_api,
    download_invoice,
    export_products_csv, import_products_csv  # 👈 Naye import
)

urlpatterns = [
    path('secret-cgs-main/', admin.site.urls),
    path('', product_list, name='home'),
    
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('checkout/', checkout_page, name='checkout'),
    path('check-coupon-ajax/', check_coupon_ajax, name='check_coupon_ajax'),
    
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    
    path('login/', login_request_otp, name='login'),
    path('login/verify/', login_verify_otp, name='login_verify_otp'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register_page, name='register'),
    path('profile/', profile_page, name='profile'),
    
    path('secret-create-admin-xyz/', make_admin, name='secret_make_admin'),
    path('secret-import-products-xyz/', trigger_import, name='secret_trigger_import'),
    
    # 📥 📤 Naye CSV Export/Import URLs
    path('export-products/', export_products_csv, name='export_products'),
    path('import-products/', import_products_csv, name='import_products'),

    # API Endpoints
    path('api/orders/pending/', get_pending_orders_api, name='api_pending_orders'),
    path('api/orders/update/<int:order_id>/', update_order_status_api, name='api_update_order'),
    path('api/products/sync/', sync_products_from_erp_api, name='api_sync_products'),

    # 📄 Naya Invoice Download URL
    path('invoice/<int:order_id>/download/', download_invoice, name='download_invoice'),
    
    # 🌟 FIX: Live server (Render) par Banners aur Images serve karne ka code
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]