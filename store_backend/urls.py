from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Views components functions standard extraction imports
from products.views import (
    product_list, 
    add_to_cart, 
    cart_detail, 
    checkout_page,
    check_coupon_ajax,
    about_page, 
    contact_page,
    custom_logout,
    register_page,
    make_admin, 
    trigger_import
)

urlpatterns = [
    # 🔐 Django Native Control Desk Panel
    path('admin/', admin.site.urls),
    
    # 🏠 Standard Global Landing Route (Homepage)
    path('', product_list, name='home'),
    
    # 🛒 Dynamic Core Transaction Pipelines
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    path('checkout/', checkout_page, name='checkout'),
    path('check-coupon-ajax/', check_coupon_ajax, name='check_coupon_ajax'),
    
    # 📄 Static Content Sub-blocks
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    
    # 👤 Authentication Safe Gates Control Block
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register_page, name='register'),
    
    # 🤫 Custom Corporate Backend Core Controls 
    path('secret-create-admin-xyz/', make_admin, name='secret_make_admin'),
    path('secret-import-products-xyz/', trigger_import, name='secret_trigger_import'),
]

# Media pipeline engine asset management attachment
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)