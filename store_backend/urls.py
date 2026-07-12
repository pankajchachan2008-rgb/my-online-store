from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from products.views import product_list, add_to_cart, cart_detail

urlpatterns = [
    # 🔐 1. Django Admin Panel Route
    path('admin/', admin.site.urls),
    
    # 🏠 2. Website Main Homepage (Shows Products with Search Bar)
    path('', product_list, name='home'),
    
    # 🛒 3. Add to Cart Dynamic Logic Action
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    
    # 📑 4. Shopping Cart Detail Page & Checkout Submit Form
    path('cart/', cart_detail, name='cart_detail'),
]

# ==============================================================================
# 🖼️ MEDIA URL ROUTING PATTERN (Added)
# ==============================================================================
# Yeh logic tabhi chalti hai jab settings me DEBUG=True ho (development environment).
# Isse browser product photo ke media links ko successfully display kar pata hai.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)