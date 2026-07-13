from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Hamare views se saare zaroori functions import kiye
from products.views import product_list, add_to_cart, cart_detail, make_admin, trigger_import

urlpatterns = [
    # Django Admin Panel Route
    path('admin/', admin.site.urls),
    
    # Website Main Homepage
    path('', product_list, name='home'),
    
    # Add to Cart Dynamic Logic Action
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    
    # Shopping Cart Detail Page
    path('cart/', cart_detail, name='cart_detail'),
    
    # Hidden Web Triggers (Bina '#' ke, taaki yeh chalu rahein)
    path('secret-create-admin-xyz/', make_admin, name='secret_make_admin'),
    path('secret-import-products-xyz/', trigger_import, name='secret_trigger_import'),
]

# Media files (Product Photos) display karne ke liye
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)