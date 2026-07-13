from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Hamare views se saare functions import kiye
from products.views import (
    product_list, 
    add_to_cart, 
    cart_detail, 
    make_admin, 
    trigger_import, 
    about_page, 
    contact_page
)

urlpatterns = [
    # 🔐 Django Admin Panel
    path('admin/', admin.site.urls),
    
    # 🏠 Website Main Homepage
    path('', product_list, name='home'),
    
    # 🛒 Cart System
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart_detail, name='cart_detail'),
    
    # 📄 Naye Pages (About, Contact, Login, Logout)
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 🤫 Hidden Web Triggers (Admin aur Excel ke liye)
    path('secret-create-admin-xyz/', make_admin, name='secret_make_admin'),
    path('secret-import-products-xyz/', trigger_import, name='secret_trigger_import'),
]

# 🖼️ Media files (Product Photos) display karne ke liye
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)