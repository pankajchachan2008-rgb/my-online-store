from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views

# Views functions imports
from products.views import (
    product_list, add_to_cart, cart_detail, checkout_page,
    check_coupon_ajax, about_page, contact_page,
    custom_logout, register_page, profile_page,
    delete_account, add_to_wishlist, view_wishlist,
    make_admin, trigger_import,
    get_pending_orders_api, update_order_status_api, sync_products_from_erp_api,
    download_invoice,
    export_products_csv, import_products_csv
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
    
    # 🔐 Standard Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register_page, name='register'),
    path('profile/', profile_page, name='profile'),
    path('profile/delete/', delete_account, name='delete_account'),
    path('profile/change-password/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/profile/'), name='password_change'),
    
    # ❤️ Wishlist (Ab urlpatterns ke andar hai)
    path('wishlist/', view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    
    # 🔧 Admin & Sync
    path('secret-create-admin-xyz/', make_admin, name='secret_make_admin'),
    path('export-products/', export_products_csv, name='export_products'),
    path('import-products/', import_products_csv, name='import_products'),

    # 📡 API Endpoints
    path('api/orders/pending/', get_pending_orders_api, name='api_pending_orders'),
    path('api/orders/update/<int:order_id>/', update_order_status_api, name='api_update_order'),
    path('api/products/sync/', sync_products_from_erp_api, name='api_sync_products'),

    # 📄 Invoices
    path('invoice/<int:order_id>/download/', download_invoice, name='download_invoice'),
    
    # 🌟 Static & Media
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]