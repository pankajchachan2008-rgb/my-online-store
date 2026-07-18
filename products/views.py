import csv
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.http import urlencode
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.http import urlencode

from .models import Product, Category, Coupon, Order, OrderItem, CustomerProfile, Banner, Wishlist, ProductVariant
from .serializers import OrderSerializer, ProductSerializer

# 🏠 1. Homepage View
def product_list(request):
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category')
    sort = request.GET.get('sort')
    
    categories = Category.objects.all()
    products = Product.objects.all()
    banners = Banner.objects.filter(is_active=True).order_by('-id')

    if search_query:
        products = products.filter(name__icontains=search_query)
        
    if category_id:
        try:
            products = products.filter(category_id=category_id)
            active_category = int(category_id)
        except ValueError:
            active_category = None
    else:
        active_category = None
    
    if sort == 'low_to_high':
        products = products.order_by('price')
    elif sort == 'high_to_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-id')
        
    return render(request, 'products/product_list.html', {
        'products': products, 
        'categories': categories,
        'banners': banners,
        'active_category': active_category,
        'search_query': search_query,
        'current_sort': sort
    })

# 🛒 2. Add to Cart (Integrated for both Variant & Normal products)
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant_id')
    
    cart = request.session.get('cart', {})
    
    if variant_id:
        # Variant wala product
        variant = get_object_or_404(ProductVariant, id=variant_id)
        cart_key = f"{product_id}_{variant_id}"
        item_name = f"{product.name} ({variant.size_name})"
        item_price = float(variant.price)
    else:
        # Normal product (Bina variant wala)
        cart_key = str(product_id)
        item_name = product.name
        item_price = float(product.price)
    
    if cart_key in cart:
        cart[cart_key]['quantity'] += 1
    else:
        cart[cart_key] = {
            'name': item_name, 
            'price': item_price, 
            'quantity': 1
        }
    
    request.session['cart'] = cart
    messages.success(request, f"{item_name} cart mein add hua!")
    return redirect('home')

# 📊 3. Cart Detail View
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    
    for pid, item in list(cart.items()):
        if isinstance(item, dict) and 'price' in item and 'quantity' in item:
            product = get_object_or_404(Product, id=int(pid))
            total_price = item['price'] * item['quantity']
            cart_total += total_price
            cart_items.append({
                'product': product, 'quantity': item['quantity'], 'total_price': total_price
            })
        else:
            cart.pop(pid, None)
            request.session['cart'] = cart
        
    return render(request, 'products/cart_detail.html', {'cart_items': cart_items, 'cart_total': cart_total})

def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')
        
    cart_total = 0
    # Items list banane ke liye
    order_items_list = []
    
    for pid, item in list(cart.items()):
        if isinstance(item, dict) and 'price' in item:
            cart_total += item['price'] * item['quantity']
            order_items_list.append(f"- {item['name']} (x{item['quantity']}) : ₹{item['price'] * item['quantity']}")
        
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile_number')
        address = request.POST.get('address')
        
        # ... (Coupon logic waisa hi rahega)
        active_coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
        final_total = float(cart_total)
        if active_coupon:
            final_total -= (final_total * active_coupon.discount_percentage) / 100
            active_coupon.is_used = True
            active_coupon.save()

        # Order creation
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name, mobile_number=mobile, address=address,
            total_amount=final_total, applied_coupon=active_coupon, status='Pending'
        )
        
        for pid, item in cart.items():
            if isinstance(item, dict):
                OrderItem.objects.create(order=order, product_name=item['name'], price=item['price'], quantity=item['quantity'])
            
        # 💬 WhatsApp Message Construction
        items_str = "\n".join(order_items_list)
        wa_text = f"📢 *Naya Order Aaya Hai!*\n\n*Order ID:* #{order.id}\n*Customer:* {name}\n*Mobile:* {mobile}\n*Address:* {address}\n\n*Items:*\n{items_str}\n\n*Total Amount:* ₹{final_total}"
        
        # WhatsApp URL generate karein (Yahan apna WhatsApp number 91XXXXXXXXXX ki jagah likhein)
        whatsapp_url = f"https://wa.me/917357073316?{urlencode({'text': wa_text})}"

        request.session['cart'] = {}
        return render(request, 'products/order_success.html', {
            'order': order, 
            'whatsapp_url': whatsapp_url # Ye url ab template mein jayega
        })

    # ... (Initial data logic)
    return render(request, 'products/checkout.html', {'cart_total': cart_total})

# 👤 5. Premium Profile Page
@login_required(login_url='/login/')
def profile_page(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('home')
        
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Dono User aur Profile update karna
        request.user.first_name = request.POST.get('first_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.mobile_number = request.POST.get('mobile_number', '')
        profile.default_address = request.POST.get('address', '')
        profile.save()
        
        messages.success(request, "✅ Aapki profile successfully update ho gayi hai!")
        return redirect('profile')

    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/profile.html', {'profile': profile, 'orders': recent_orders})

# 🗑️ Naya Feature: Delete Account
@login_required(login_url='/login/')
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Aapka account hamesha ke liye delete kar diya gaya hai.")
        return redirect('home')
    return redirect('profile')

# 🔍 6. AJAX Coupon Check
def check_coupon_ajax(request):
    mobile = request.GET.get('mobile', '')
    coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
    if coupon:
        return JsonResponse({'status': 'found', 'discount': coupon.discount_percentage, 'code': coupon.code})
    return JsonResponse({'status': 'not_found'})

# 📄 7. Static Pages
def about_page(request): return render(request, 'products/about.html')
def contact_page(request): return render(request, 'products/contact.html')

def custom_logout(request):
    logout(request)
    return redirect('home')

def make_admin(request): return render(request, 'products/admin_trigger.html')
def trigger_import(request): return render(request, 'products/import_trigger.html')

# 🚀 8. STANDARD USERNAME/PASSWORD REGISTRATION
def register_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account successfully ban gaya hai! Ab aap username aur password se login kar sakte hain.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# 📡 9. ERP API Endpoints
@api_view(['GET'])
def get_pending_orders_api(request):
    orders = Order.objects.filter(status='Pending').order_by('-id')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def update_order_status_api(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order nahi mila'}, status=status.HTTP_404_NOT_FOUND)
        
    new_status = request.data.get('status')
    if new_status:
        order.status = new_status
        order.save()
        return Response({'message': f'Order status successfully updated to {new_status}'})
    return Response({'error': 'Invalid status data'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def sync_products_from_erp_api(request):
    product_data = request.data 
    if not isinstance(product_data, list):
        return Response({'error': 'Data list format me hona chahiye'}, status=status.HTTP_400_BAD_REQUEST)
        
    for item in product_data:
        sku = item.get('sku')
        if sku:
            Product.objects.update_or_create(
                sku=sku,
                defaults={'name': item.get('name'), 'description': item.get('description', ''), 'price': item.get('price', 0.00)}
            )
    return Response({'message': 'Product sync process successfully executed'})

# 📄 10. Download Smart PDF Invoice
@login_required(login_url='/login/')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    
    template_path = 'products/invoice_pdf.html'
    context = {'order': order, 'items': items}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CGSmart_Invoice_{order.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Invoice generate karne mein error aayi: <pre>' + html + '</pre>')
    return response

# 📥 11. EXPORT: Download products to Excel (CSV)
@login_required(login_url='/login/')
def export_products_csv(request):
    if not request.user.is_superuser:
        messages.error(request, "⛔ Access Denied! Sirf Admin is page ko access kar sakta hai.")
        return redirect('home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Bulk_Update_Products.csv"'
    writer = csv.writer(response)
    
    writer.writerow(['ID', 'Name', 'Category_ID', 'Category_Name', 'Price', 'Weight', 'Description'])
    
    products = Product.objects.all()
    for p in products:
        cat_id = p.category.id if p.category else ''
        cat_name = p.category.name if p.category else 'Uncategorized'
        writer.writerow([p.id, p.name, cat_id, cat_name, p.price, getattr(p, 'weight', ''), p.description])
        
    return response

# 📤 12. IMPORT: Upload updated Excel (CSV)
@login_required(login_url='/login/')
def import_products_csv(request):
    if not request.user.is_superuser:
        messages.error(request, "⛔ Access Denied! Sirf Admin is page ko access kar sakta hai.")
        return redirect('home')

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "❌ Error: Sirf .csv file hi upload karein!")
            return redirect('import_products')
            
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        success_count = 0
        error_count = 0
        
        for row in reader:
            try:
                product_id = row.get('ID')
                if not product_id:
                    continue
                    
                product = Product.objects.get(id=product_id)
                
                if row.get('Price'):
                    product.price = row['Price']
                    
                if row.get('Weight'):
                    product.weight = row['Weight']
                    
                cat_id = row.get('Category_ID')
                if cat_id:
                    try:
                        category = Category.objects.get(id=cat_id)
                        product.category = category
                    except Category.DoesNotExist:
                        pass 
                        
                product.save()
                success_count += 1
            except Product.DoesNotExist:
                error_count += 1
            except Exception as e:
                error_count += 1
                
        messages.success(request, f"✅ Bulk Update Complete! {success_count} products update hue. {error_count} errors ko skip kiya gaya.")
        return redirect('home')
        
    return render(request, 'products/import_csv.html')

@login_required(login_url='/login/')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Security: check karein ki kya user ne pehle se add kiya hai
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if created:
        messages.success(request, f"{product.name} aapki Wishlist mein add ho gaya!")
    else:
        messages.info(request, "Yeh product pehle se aapki Wishlist mein hai.")
    return redirect('home')

@login_required(login_url='/login/')
def view_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    return render(request, 'products/wishlist.html', {'wishlist': wishlist})

# 🔍 Product Detail View
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})