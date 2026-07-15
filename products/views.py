from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Coupon, Order, OrderItem, CustomerProfile
from .serializers import OrderSerializer, ProductSerializer
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


# 🏠 1. Homepage View (Combined with Search, Category, and Sorting)
def product_list(request):
    search_query = request.GET.get('search', '').strip()
    category = request.GET.get('category')
    sort = request.GET.get('sort')
    
    # Base Queryset
    products = Product.objects.all()

    # A. Search Filter
    if search_query:
        products = products.filter(name__icontains=search_query)
        
    # B. Category Filter
    if category:
        products = products.filter(category=category)
    
    # C. Price Sorting Logic
    if sort == 'low_to_high':
        products = products.order_by('price')
    elif sort == 'high_to_low':
        products = products.order_by('-price')
    else:
        # Default: Latest products first
        products = products.order_by('-id')
        
    return render(request, 'products/product_list.html', {
        'products': products, 
        'active_category': category
    })

# 🛒 2. Add to Cart
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    product_id_str = str(product_id)
    if product_id_str in cart:
        if isinstance(cart[product_id_str], dict):
            cart[product_id_str]['quantity'] += 1
        else:
            cart[product_id_str] = {'name': product.name, 'price': float(product.price), 'quantity': 1}
    else:
        cart[product_id_str] = {'name': product.name, 'price': float(product.price), 'quantity': 1}
    
    request.session['cart'] = cart
    messages.success(request, f"{product.name} cart me add ho gaya hai!")
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

# 💳 4. Checkout Page with Smart Auto-fill
def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')
        
    cart_total = 0
    for pid, item in list(cart.items()):
        if isinstance(item, dict) and 'price' in item:
            cart_total += item['price'] * item['quantity']
        
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile_number')
        address = request.POST.get('address')
        
        active_coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
        final_total = float(cart_total)
        
        if active_coupon:
            discount_amount = (final_total * active_coupon.discount_percentage) / 100
            final_total -= discount_amount
            active_coupon.is_used = True
            active_coupon.save()

        # 🌟 SMART PROFILE UPDATE
        if request.user.is_authenticated:
            profile, created = CustomerProfile.objects.get_or_create(user=request.user)
            if not profile.default_address:
                profile.default_address = address
                profile.mobile_number = mobile
                profile.save()

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name, mobile_number=mobile, address=address,
            total_amount=final_total, applied_coupon=active_coupon, status='Pending'
        )
        
        for pid, item in cart.items():
            if isinstance(item, dict):
                OrderItem.objects.create(
                    order=order, product_name=item['name'], price=item['price'], quantity=item['quantity']
                )
            
        new_coupon = None
        if final_total >= 999:
            new_coupon = Coupon.objects.create(code=f"CGS10-{order.id}", mobile_number=mobile, discount_percentage=10)
        elif final_total >= 699:
            new_coupon = Coupon.objects.create(code=f"CGS08-{order.id}", mobile_number=mobile, discount_percentage=8)

        request.session['cart'] = {}
        return render(request, 'products/order_success.html', {'order': order, 'new_coupon': new_coupon})

    # 🌟 SMART AUTO-FILL
    initial_data = {}
    if request.user.is_authenticated:
        profile, created = CustomerProfile.objects.get_or_create(user=request.user)
        initial_data = {
            'name': request.user.username,
            'mobile': profile.mobile_number or "",
            'address': profile.default_address or ""
        }

    return render(request, 'products/checkout.html', {'cart_total': cart_total, 'initial_data': initial_data})

# 👤 5. Profile Page (Order History & Settings)
@login_required
def profile_page(request):
    # Agar admin hai, toh use profile dikhane ki zaroorat nahi
    if request.user.is_staff or request.user.is_superuser:
        return redirect('home')
        
    # Sirf normal user ke liye profile fetch karein
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.mobile_number = request.POST.get('mobile_number')
        profile.default_address = request.POST.get('address')
        profile.save()
        messages.success(request, "Aapki profile update ho gayi!")
        return redirect('profile')

    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'products/profile.html', {'profile': profile, 'orders': recent_orders})

# 🔍 6. AJAX Coupon Check
def check_coupon_ajax(request):
    mobile = request.GET.get('mobile', '')
    coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
    if coupon:
        return JsonResponse({'status': 'found', 'discount': coupon.discount_percentage, 'code': coupon.code})
    return JsonResponse({'status': 'not_found'})

# 📄 7. Static & Auth Pages
def about_page(request): return render(request, 'products/about.html')
def contact_page(request): return render(request, 'products/contact.html')

def custom_logout(request):
    logout(request)
    return redirect('home')

def register_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account successfully ban gaya hai! Ab aap login kar sakte hain.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'products/register.html', {'form': form})

def make_admin(request): return render(request, 'products/admin_trigger.html')
def trigger_import(request): return render(request, 'products/import_trigger.html')

# 📡 8. ERP API Endpoints
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

# 📄 Download Smart PDF Invoice
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Template jise PDF mein convert karna hai
    template_path = 'products/invoice_pdf.html'
    context = {'order': order}
    
    # Response ko PDF format mein set karein
    response = HttpResponse(content_type='application/pdf')
    # Attachment property browser ko file download karne ka signal deti hai
    response['Content-Disposition'] = f'attachment; filename="CGSmart_Invoice_{order.id}.pdf"'
    
    # HTML ko render karein
    template = get_template(template_path)
    html = template.render(context)
    
    # PDF Create karein
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Invoice generate karne mein error aayi: <pre>' + html + '</pre>')
    return response