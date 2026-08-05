from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views
from django.http import HttpResponse  

from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from products.sitemaps import ProductSitemap, StaticViewSitemap
from products.views import search_suggestions

from products import views
from products.views import check_delivery

# 🌟 FIX: Removed 'make_admin' from here!
from products.views import (
    product_list, add_to_cart, cart_detail, checkout_page,
    check_coupon_ajax, about_page, contact_page,
    custom_logout, register_page, profile_page,
    delete_account, add_to_wishlist, view_wishlist,
    remove_from_wishlist,
    trigger_import,
    get_pending_orders_api, update_order_status_api, sync_products_from_erp_api,
    download_invoice,
    export_products_csv, import_products_csv,
    product_detail, 
    update_cart_item, 
    cancel_order, 
    delete_address, edit_address,
    privacy_policy, terms_conditions, refund_policy,
)

def ping(request):
    return HttpResponse("OK", status=200)

sitemaps = {
    'products': ProductSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('secret-cgs-main/', admin.site.urls),
    path('', product_list, name='home'),

    path('api/check-delivery/', check_delivery, name='check_delivery'),
    
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('api/search-suggestions/', search_suggestions, name='search_suggestions'),
    
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    
    path('cart/update/<str:item_key>/<str:action>/', update_cart_item, name='update_cart_item'),
    path('erp/api/barcode-lookup/', views.erp_barcode_lookup, name='erp_barcode_lookup'),
    path('checkout/', checkout_page, name='checkout'),
    path('check-coupon-ajax/', check_coupon_ajax, name='check_coupon_ajax'),
    path('erp/gst-report/', views.erp_gst_report, name='erp_gst_report'),
    
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('ai-assistant/', views.ai_assistant_chat, name='ai_assistant_chat'),

    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('terms-conditions/', terms_conditions, name='terms_conditions'),
    path('refund-policy/', refund_policy, name='refund_policy'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('manifest.json', TemplateView.as_view(template_name="manifest.json", content_type="application/json")),
    
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html', 
        next_page='profile', 
        redirect_authenticated_user=True
    ), name='login'),

    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register_page, name='register'),
    path('profile/', profile_page, name='profile'),
    path('profile/delete/', delete_account, name='delete_account'),
    path('profile/change-password/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/profile/'), name='password_change'),
    path('delete-address/<int:address_id>/', delete_address, name='delete_address'),
    path('edit-address/<int:address_id>/', edit_address, name='edit_address'),
    path('track-order/', views.track_order_page, name='track_order'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-verify-otp/', views.reset_verify_otp, name='reset_verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    
    path('cancel-order/<int:order_id>/', cancel_order, name='cancel_order'),
    
    # ❤️ Wishlist
    path('wishlist/', view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    
    path('export-products/', export_products_csv, name='export_products'),
    path('import-products/', import_products_csv, name='import_products'),

    path('api/orders/pending/', get_pending_orders_api, name='api_pending_orders'),
    path('api/orders/update/<int:order_id>/', update_order_status_api, name='api_update_order'),
    path('api/products/sync/', sync_products_from_erp_api, name='api_sync_products'),

    path('cart-ajax/summary/', views.cart_summary_ajax, name='cart_summary_ajax'),
    path('cart-ajax/add/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('cart-ajax/remove/<int:product_id>/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),

    path('invoice/<int:order_id>/download/', download_invoice, name='download_invoice'),
    
    path('ping/', ping, name='ping'),
# 🏢 Custom ERP Routes
    path('cgs-erp/dashboard/', views.erp_dashboard, name='erp_dashboard'),
    path('cgs-erp/order/update/<int:order_id>/', views.erp_update_order, name='erp_update_order'),
    path('cgs-erp/products/', views.erp_products, name='erp_products'),
    path('cgs-erp/products/add/', views.erp_add_product, name='erp_add_product'),
    path('cgs-erp/pos/', views.erp_pos_billing, name='erp_pos'),
    path('cgs-erp/ledger/', views.erp_customer_ledger, name='erp_ledger'),
    path('cgs-erp/settings/', views.erp_store_settings, name='erp_settings'),
    
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]