from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.http import HttpResponse  
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

# App Imports
from products import views
from products.views import search_suggestions, check_delivery
from products.sitemaps import ProductSitemap, StaticViewSitemap
from django.urls import path
from products import views

# 🌟 Specific View Imports for cleaner path definitions
from products.views import (
    product_list, add_to_cart, cart_detail, checkout_page,
    check_coupon_ajax, about_page, contact_page,
    custom_logout, register_page, profile_page,
    delete_account, add_to_wishlist, view_wishlist,
    remove_from_wishlist, trigger_import,
    get_pending_orders_api, update_order_status_api, sync_products_from_erp_api,
    download_invoice, export_products_csv, import_products_csv,
    product_detail, update_cart_item, cancel_order, 
    delete_address, edit_address, privacy_policy, terms_conditions, refund_policy,
)

def ping(request):
    return HttpResponse("OK", status=200)

sitemaps = {
    'products': ProductSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # ==========================================
    # 🔐 ADMIN & SYSTEM HEALTH
    # ==========================================
    path('secret-cgs-main/', admin.site.urls),
    path('ping/', ping, name='ping'),

    # ==========================================
    # 🏠 HOMEPAGE & CATALOG
    # ==========================================
    path('', product_list, name='home'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('api/search-suggestions/', search_suggestions, name='search_suggestions'),
    path('api/check-delivery/', check_delivery, name='check_delivery'),

    # ==========================================
    # 🛒 CART & CHECKOUT
    # ==========================================
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/update/<str:item_key>/<str:action>/', update_cart_item, name='update_cart_item'),
    
    # 🛠️ FIX 1: Changed <int:product_id> to <str:cart_key> to fix variant deletion bug!
    path('cart-ajax/remove/<str:cart_key>/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
    
    path('cart-ajax/summary/', views.cart_summary_ajax, name='cart_summary_ajax'),
    path('cart-ajax/add/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    
    path('checkout/', checkout_page, name='checkout'),
    path('check-coupon-ajax/', check_coupon_ajax, name='check_coupon_ajax'),

    # ==========================================
    # 👤 AUTHENTICATION & PROFILE
    # ==========================================
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html', 
        next_page='profile', 
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register_page, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-verify-otp/', views.reset_verify_otp, name='reset_verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    
    path('profile/', profile_page, name='profile'),
    path('profile/delete/', delete_account, name='delete_account'),
    path('profile/change-password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html', 
        success_url='/profile/'
    ), name='password_change'),
    
    path('delete-address/<int:address_id>/', delete_address, name='delete_address'),
    path('edit-address/<int:address_id>/', edit_address, name='edit_address'),

    # ==========================================
    # ❤️ WISHLIST
    # ==========================================
    path('wishlist/', view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),

    # ==========================================
    # 📦 ORDERS & INVOICES
    # ==========================================
    path('track-order/', views.track_order_page, name='track_order'),
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('invoice/<int:order_id>/download/', download_invoice, name='download_invoice'),
    path('erp/resend-otp/<int:order_id>/', views.resend_delivery_otp, name='resend_delivery_otp'),

    # ==========================================
    # 📄 STATIC PAGES & SEO
    # ==========================================
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('terms-conditions/', terms_conditions, name='terms_conditions'),
    path('refund-policy/', refund_policy, name='refund_policy'),
    
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('manifest.json', TemplateView.as_view(template_name="manifest.json", content_type="application/json")),

    # ==========================================
    # 🤖 AI & UTILITIES
    # ==========================================
    path('ai-assistant/', views.ai_assistant_chat, name='ai_assistant_chat'),
    path('trigger-import/', trigger_import, name='trigger_import'),
    path('export-products/', export_products_csv, name='export_products'),
    path('import-products/', import_products_csv, name='import_products'),

    # ==========================================
    # 📡 APIs (REST FRAMEWORK)
    # ==========================================
    path('api/orders/pending/', get_pending_orders_api, name='api_pending_orders'),
    path('api/orders/update/<int:order_id>/', update_order_status_api, name='api_update_order'),
    path('api/products/sync/', sync_products_from_erp_api, name='api_sync_products'),

    # ==========================================
    # 🏢 CUSTOM ERP / ADMIN DASHBOARD ROUTES
    # ==========================================
    path('cgs-erp/dashboard/', views.erp_dashboard, name='erp_dashboard'),
    path('cgs-erp/products/', views.erp_products, name='erp_products'),
    path('cgs-erp/products/add/', views.erp_add_product, name='erp_add_product'),
    path('cgs-erp/pos/', views.erp_pos_billing, name='erp_pos'),
    path('cgs-erp/ledger/', views.erp_customer_ledger, name='erp_ledger'),
    path('cgs-erp/settings/', views.erp_store_settings, name='erp_settings'),
    path('cgs-erp/expenses/', views.erp_expenses, name='erp_expenses'),
    path('cgs-erp/supplier-ledger/', views.erp_supplier_ledger, name='erp_supplier_ledger'),
    path('cgs-erp/gst-report/', views.erp_gst_report, name='erp_gst_report'),
    path('cgs-erp/export-ca-report/', views.export_ca_accounting_report, name='export_ca_report'),
    
    path('cgs-erp/order/update/<int:order_id>/', views.erp_update_order, name='erp_update_order'),
    path('erp/api/barcode-lookup/', views.erp_barcode_lookup, name='erp_barcode_lookup'),
    path('erp/ledger/whatsapp/<str:mobile>/', views.send_customer_khata_whatsapp, name='send_customer_khata_whatsapp'),

    # ==========================================
    # 🛵 DELIVERY BOY MOBILE PORTAL
    # ==========================================
    path('delivery-dashboard/', views.delivery_boy_dashboard, name='delivery_boy_dashboard'),
    path('delivery/mark-collected/<int:order_id>/', views.delivery_mark_collected, name='delivery_mark_collected'),
    path('admin-panel/confirm-payment/<int:order_id>/', views.admin_confirm_payment, name='admin_confirm_payment'),
    path('delivery/mark-collected/<int:order_id>/', views.delivery_mark_collected, name='delivery_mark_collected'),
]

# 🌟 Best Practice: Serve media files efficiently.
# In DEBUG mode, Django serves them. In Production, Nginx/Apache should serve them.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Fallback for production if Nginx isn't configured to serve media yet
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]