import csv
import json 
import random
import qrcode
import barcode
import requests
import os
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden # 🌟 Added HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from django.db.models import Avg
# 🌟 FIX: OrderSerializer was used below but never imported anywhere — this
# caused a NameError (500 crash) every time get_pending_orders_api was hit.
# Update the import path below to wherever your OrderSerializer actually lives
# (commonly products/serializers.py).
from .serializers import OrderSerializer
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.http import urlencode
from django.core.mail import send_mail
from .models import OTPVerification
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .forms import CustomRegisterForm
from django.utils import timezone 

from .models import Product, Category, SubCategory, Coupon, Order, OrderItem, CustomerProfile, Banner, Wishlist, ProductVariant, Address, WalletTransaction, StoreSetting, Brand, Review

# --- HELPER FUNCTION FOR BREVO API ---
def send_brevo_api_email(subject, message, to_email):
    api_key = os.environ.get('BREVO_API_KEY') 
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"email": "support@cgsmart.in", "name": "CGSmart Store"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": message
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code
    except Exception as e:
        print(f"Email API error: {e}")
        return None

# 🏠 1. Updated Homepage View (With Pagination Fix)
def product_list(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()
    # 🌟 FIX: select_related/prefetch_related avoids one extra query per
    # product for brand/category/variants (N+1 query problem)
    products = Product.objects.select_related('brand', 'category').prefetch_related('variants')
    banners = Banner.objects.filter(is_active=True).order_by('-id')

    search_query = request.GET.get('search', '').strip(' .')
    sort = request.GET.get('sort')
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    sub_category_id = request.GET.get('sub_category')
    
    discount = request.GET.get('discount')
    rating = request.GET.get('rating')
    availability = request.GET.get('availability')
    color = request.GET.get('color')
    size = request.GET.get('size')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if search_query:
        products = products.filter(name__icontains=search_query)

    active_category = None
    if category_id:
        try:
            products = products.filter(category_id=category_id)
            active_category = int(category_id)
        except ValueError:
            pass

    if sub_category_id:
        try:
            products = products.filter(sub_category_id=sub_category_id)
        except ValueError:
            pass

    active_brand = None
    if brand_id:
        try:
            products = products.filter(brand_id=brand_id)
            active_brand = int(brand_id)
        except ValueError:
            pass

    if discount:
        try: products = products.filter(discount_percentage__gte=discount)
        except: pass
        
    if rating:
        try:
            # 🌟 FIX: was matching products with AT LEAST ONE review >= rating
            # (so a product with a single 5-star review among many 1-stars
            # would incorrectly show up under "4★ & Above"). Now filters on
            # the product's actual average rating.
            products = products.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=float(rating))
        except (ValueError, TypeError):
            pass
        
    if availability == 'in_stock':
        try: products = products.filter(stock__gt=0)
        except: pass
        
    if color:
        try: products = products.filter(color__icontains=color)
        except: pass
        
    if size:
        try: products = products.filter(size__icontains=size)
        except: pass
        
    # 🌟 FIX: previously required BOTH min_price AND max_price to be present,
    # so entering only one of them silently did nothing. Now each works alone.
    if min_price:
        try: products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError): pass
    if max_price:
        try: products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError): pass

    products = products.distinct()

    if sort == 'low_to_high':
        products = products.order_by('price')
    elif sort == 'high_to_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-id')
    
    paginator = Paginator(products, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 🌟 Pagination ke liye saare filters ko ek sath jodna
    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()
        
    context = {
        'products': page_obj,  
        'categories': categories,
        'brands': brands, 
        'banners': banners,
        'active_category': active_category,
        'active_brand': active_brand, 
        'search_query': search_query,
        'current_sort': sort,
        'active_discount': discount,
        'active_rating': rating,
        'active_availability': availability,
        'active_color': color,
        'active_size': size,
        'min_price': min_price,
        'max_price': max_price,
        'querystring': querystring,
    }
    return render(request, 'products/product_list.html', context)

# 🛒 2. Add to Cart (Standard)
# 🌟 FIX: this view mutates session cart state but had no method
# restriction — wishlist.html was calling it via a plain GET <a> link,
# the same link-prefetch/crawler risk fixed earlier in cart_detail.html.
# product_detail.html already submits via a real POST form, so this only
# blocks the unsafe GET usage.
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant_id')
    cart = request.session.get('cart', {})
    
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        cart_key = f"{product_id}_{variant_id}"
        item_name = f"{product.name} ({variant.size_name})"
        item_price = float(variant.price)
    else:
        cart_key = str(product_id)
        item_name = product.name
        item_price = float(product.price)
    
    if cart_key in cart:
        cart[cart_key]['quantity'] += 1
    else:
        cart[cart_key] = {'name': item_name, 'price': item_price, 'quantity': 1}
    
    request.session['cart'] = cart
    messages.success(request, f"{item_name} cart mein add hua!")
    return redirect('home')

# 📊 3. Cart Detail
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    cart_modified = False
    
    for pid, item in list(cart.items()):
        if isinstance(item, dict) and 'price' in item and 'quantity' in item:
            try:
                product_id = int(str(pid).split('_')[0])
                product = Product.objects.get(id=product_id)
                total_price = item['price'] * item['quantity']
                cart_total += total_price
                
                cart_items.append({
                    'key': str(pid), 
                    'product': product, 
                    'name': item['name'],
                    'unit_price': item['price'],
                    'quantity': item['quantity'], 
                    'total_price': total_price
                })
            except (Product.DoesNotExist, ValueError):
                cart.pop(pid, None)
                cart_modified = True
        else:
            cart.pop(pid, None)
            cart_modified = True
            
    if cart_modified:
        request.session['cart'] = cart
        request.session.modified = True
        
    return render(request, 'products/cart_detail.html', {'cart_items': cart_items, 'cart_total': cart_total})

# 🛍️ 4. Checkout
def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')
        
    subtotal = 0; total_mrp = 0; hidden_discount_total = 0
    order_items_list = []
    profile = None; wallet_balance = 0
    
    if request.user.is_authenticated:
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        wallet_balance = profile.wallet_balance
    
    for pid, item in list(cart.items()):
        if isinstance(item, dict) and 'price' in item:
            item_qty = item['quantity']
            item_price = item['price']
            subtotal += item_price * item_qty
            
            product_id = int(str(pid).split('_')[0])
            try:
                product = Product.objects.get(id=product_id)
                if product.mrp: total_mrp += float(product.mrp) * item_qty
                else: total_mrp += item_price * item_qty 
                if product.last_moment_discount > 0:
                    hidden_discount_total += float(product.last_moment_discount) * item_qty
            except Product.DoesNotExist:
                total_mrp += item_price * item_qty
                
            order_items_list.append(f"- {item['name']} (x{item_qty}) : ₹{item_price * item_qty}")
    
    regular_discount = total_mrp - subtotal
    payable_subtotal = subtotal - hidden_discount_total
    
    if payable_subtotal < 500: delivery_fee = 30
    elif 500 <= payable_subtotal <= 699: delivery_fee = 20
    elif 700 <= payable_subtotal <= 999: delivery_fee = 15
    else: delivery_fee = 0
        
    final_total = payable_subtotal + delivery_fee
    total_savings = regular_discount + hidden_discount_total
        
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if address_id:
            # 🌟 FIX: unhandled Address.DoesNotExist previously caused a 500
            # error if someone tampered with the address_id in the form.
            selected_address = get_object_or_404(Address, id=address_id, user=request.user)
            name = selected_address.name; mobile = selected_address.mobile_number
            address = f"{selected_address.full_address}, {selected_address.locality}, {selected_address.city}, {selected_address.state} - {selected_address.pincode}"
        else:
            name = request.POST.get('name'); mobile = request.POST.get('mobile_number'); address = request.POST.get('address')
        
        promo_code = request.POST.get('promo_code', '').strip().upper()
        active_coupon = None; coupon_discount_applied = 0
        
        if promo_code:
            coupon = Coupon.objects.filter(code=promo_code, is_active=True).first()
            if coupon:
                now = timezone.now()
                if (not coupon.valid_from or now >= coupon.valid_from) and (not coupon.valid_to or now <= coupon.valid_to) and (final_total >= coupon.min_order_amount):
                    coupon_discount_applied = (final_total * coupon.discount_percentage) / 100
                    if coupon.max_discount_amount and coupon_discount_applied > float(coupon.max_discount_amount):
                        coupon_discount_applied = float(coupon.max_discount_amount)
                    final_total -= coupon_discount_applied
                    active_coupon = coupon

        use_wallet = request.POST.get('use_wallet')
        wallet_deducted = 0
        if use_wallet == 'on' and profile and profile.wallet_balance > 0:
            if profile.wallet_balance >= final_total:
                wallet_deducted = final_total; profile.wallet_balance -= final_total; final_total = 0
            else:
                wallet_deducted = profile.wallet_balance; final_total -= profile.wallet_balance; profile.wallet_balance = 0
            profile.save()

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name, mobile_number=mobile, address=address,
            total_amount=final_total, applied_coupon=active_coupon, status='Pending'
        )

        if wallet_deducted > 0:
            WalletTransaction.objects.create(user=request.user, transaction_type='DEBIT', amount=wallet_deducted, description=f"Used for Order #{order.id}")
        
        for pid, item in cart.items():
            if isinstance(item, dict): OrderItem.objects.create(order=order, product_name=item['name'], price=item['price'], quantity=item['quantity'])
            
        items_str = "\n".join(order_items_list)
        coupon_text = f"\n*Coupon Discount:* ₹{coupon_discount_applied}" if coupon_discount_applied > 0 else ""
        wa_text = f"📢 *Naya Order Aaya Hai!*\n\n*Order ID:* #{order.id}\n*Customer:* {name}\n*Mobile:* {mobile}\n*Address:* {address}\n\n*Items:*\n{items_str}\n*Delivery Charge:* ₹{delivery_fee}{coupon_text}\n*Wallet Used:* ₹{wallet_deducted}\n*Total Payable:* ₹{final_total}"
        whatsapp_url = f"https://wa.me/917357073316?{urlencode({'text': wa_text})}"

        if request.user.is_authenticated and request.user.email:
            send_brevo_api_email(f"Order Confirmation - Order #{order.id}", f"<h3>Hello {name},</h3><p>Aapka order <strong>#{order.id}</strong> receive ho gaya hai!</p><p><strong>Total Amount:</strong> ₹{final_total}</p>", request.user.email)

        request.session['cart'] = {}
        return render(request, 'products/order_success.html', {'order': order, 'whatsapp_url': whatsapp_url})

    saved_addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'products/checkout.html', {
        'cart_total': subtotal, 'total_mrp': total_mrp, 'regular_discount': regular_discount, 'hidden_discount_total': hidden_discount_total,
        'delivery_fee': delivery_fee, 'final_total': final_total, 'total_savings': total_savings, 'saved_addresses': saved_addresses, 'profile': profile,
    })

# 👤 5. Premium Profile
@login_required(login_url='/login/')
def profile_page(request):
    if request.user.is_staff or request.user.is_superuser: return redirect('home')
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', ''); request.user.last_name = request.POST.get('last_name', ''); request.user.email = request.POST.get('email', '')
            request.user.save()
            profile.mobile_number = request.POST.get('mobile_number', '')
            if 'profile_photo' in request.FILES: profile.profile_photo = request.FILES['profile_photo']
            profile.save()
            messages.success(request, "✅ Profile updated successfully!")
        elif action == 'add_address':
            Address.objects.create(user=request.user, name=request.POST.get('name'), mobile_number=request.POST.get('mobile'), pincode=request.POST.get('pincode'), locality=request.POST.get('locality'), full_address=request.POST.get('full_address'), city=request.POST.get('city'), state=request.POST.get('state'), address_type=request.POST.get('address_type', 'Home'))
            messages.success(request, "✅ New address added!")
        return redirect('profile')

    return render(request, 'products/profile.html', {
        'profile': profile, 'orders': Order.objects.filter(user=request.user).order_by('-created_at'),
        'addresses': Address.objects.filter(user=request.user), 'transactions': WalletTransaction.objects.filter(user=request.user).order_by('-created_at')
    })

@login_required(login_url='/login/')
def delete_account(request):
    if request.method == 'POST':
        user = request.user; logout(request); user.delete()
        messages.success(request, "Aapka account hamesha ke liye delete kar diya gaya hai.")
        return redirect('home')
    return redirect('profile')

def check_coupon_ajax(request):
    code = request.GET.get('code', '').strip().upper()
    try: cart_total = float(request.GET.get('cart_total', 0))
    except ValueError: cart_total = 0

    if not code: return JsonResponse({'status': 'not_found', 'message': 'Please enter a coupon code.'})
    coupon = Coupon.objects.filter(code=code, is_active=True).first()
    if not coupon: return JsonResponse({'status': 'not_found', 'message': 'Invalid or expired coupon code.'})

    now = timezone.now()
    if coupon.valid_from and now < coupon.valid_from: return JsonResponse({'status': 'error', 'message': 'Coupon is not yet active.'})
    if coupon.valid_to and now > coupon.valid_to: return JsonResponse({'status': 'error', 'message': 'Coupon has expired.'})
    if cart_total < coupon.min_order_amount: return JsonResponse({'status': 'error', 'message': f'Min. order amount of ₹{coupon.min_order_amount} required.'})

    discount_amount = (cart_total * coupon.discount_percentage) / 100
    if coupon.max_discount_amount and discount_amount > float(coupon.max_discount_amount): discount_amount = float(coupon.max_discount_amount)

    return JsonResponse({'status': 'found', 'discount_percentage': coupon.discount_percentage, 'discount_amount': discount_amount, 'message': f'Coupon {code} applied successfully!'})

def about_page(request): return render(request, 'products/about.html')
# 🌟 FIX: this view previously ignored POST entirely — the contact form
# silently discarded every submission with no email sent and no feedback
# to the user. Now it actually processes and emails the message.
def contact_page(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and subject and message:
            email_body = (
                f"<h3>Naya Contact Form Message</h3>"
                f"<p><strong>Name:</strong> {name}</p>"
                f"<p><strong>Email:</strong> {email}</p>"
                f"<p><strong>Subject:</strong> {subject}</p>"
                f"<p><strong>Message:</strong><br>{message}</p>"
            )
            send_brevo_api_email(f"Contact Form: {subject}", email_body, 'support@cgsmart.in')
            messages.success(request, "✅ Aapka message humein mil gaya hai! Hum jald hi aapse sampark karenge.")
        else:
            messages.error(request, "Kripya saare fields bharein.")
        return redirect('contact')

    return render(request, 'products/contact.html')
def privacy_policy(request): return render(request, 'policies/privacy.html')
def terms_conditions(request): return render(request, 'policies/terms.html')
def refund_policy(request): return render(request, 'policies/refund.html')
def custom_logout(request): logout(request); return redirect('home')

# 🛡️ --- SECURE VERSION of make_admin --- 🛡️
def make_admin(request):
    setup_secret = os.environ.get('SETUP_SECRET_KEY')

    # Agar env variable set hi nahi hai, to feature completely band rahega
    if not setup_secret:
        return HttpResponseForbidden("Setup disabled.")

    provided_secret = request.GET.get('secret')

    if provided_secret != setup_secret:
        # Generic error — attacker ko ye pata nahi chalna chahiye ki admin
        # exist karta hai ya nahi, ya secret galat hai ya missing hai
        return HttpResponseForbidden("Forbidden.")

    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@cgsmart.in', 'Admin@1234')
        return HttpResponse(
            "<div style='text-align:center; margin-top:50px;'>"
            "<h2>✅ Admin Created!</h2>"
            "<a href='/secret-cgs-main/'>Go to Admin</a></div>"
        )

    return HttpResponse(
        "<div style='text-align:center; margin-top:50px;'>"
        "<h2>⚠️ Admin Exists!</h2>"
        "<a href='/secret-cgs-main/'>Go to Admin</a></div>"
    )

def trigger_import(request): return render(request, 'products/import_trigger.html')

def register_page(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False); user.is_active = False; user.save()
            otp = str(random.randint(100000, 999999)); OTPVerification.objects.create(user=user, otp=otp)
            send_brevo_api_email('CGSmart - Account Verification OTP', f'Aapka OTP hai: {otp}', user.email)
            request.session['verify_user_id'] = user.id
            messages.success(request, 'Account successfully ban gaya hai! Kripya OTP daalein.')
            return redirect('verify_otp')
    else: form = CustomRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# 🌟 FIX: all 3 APIs below were publicly callable by anyone with no auth at
# all — exposing customer names/mobiles/addresses, allowing anyone to change
# order status, and allowing anyone to inject/overwrite products. Now locked
# to authenticated staff/admin accounts via TokenAuthentication.
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def get_pending_orders_api(request):
    return Response(OrderSerializer(Order.objects.filter(status='Pending').order_by('-id'), many=True).data)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def update_order_status_api(request, order_id):
    try: order = Order.objects.get(id=order_id)
    except Order.DoesNotExist: return Response({'error': 'Order nahi mila'}, status=status.HTTP_404_NOT_FOUND)
    if new_status := request.data.get('status'): order.status = new_status; order.save(); return Response({'message': f'Updated to {new_status}'})
    return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdminUser])
def sync_products_from_erp_api(request):
    if not isinstance(request.data, list): return Response({'error': 'Data list format me hona chahiye'}, status=status.HTTP_400_BAD_REQUEST)
    for item in request.data:
        if sku := item.get('sku'): Product.objects.update_or_create(sku=sku, defaults={'name': item.get('name'), 'description': item.get('description', ''), 'price': item.get('price', 0.00)})
    return Response({'message': 'Product sync process successfully executed'})

@login_required(login_url='/login/')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id); items = OrderItem.objects.filter(order=order)
    store = StoreSetting.objects.first()
    bill_no = f"#INV-2026-{order.id}"

    qr = qrcode.make(bill_no); qr_buffer = BytesIO(); qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")

    bc = barcode.get_barcode_class('code128')(bill_no, writer=ImageWriter()); bc_buffer = BytesIO()
    bc.write(bc_buffer, options={'write_text': False}); barcode_base64 = base64.b64encode(bc_buffer.getvalue()).decode("utf-8")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CGSmart_Bill_{order.id}.pdf"'
    # 🌟 FIX: invoice_pdf.html uses customer_phone, customer_address, date,
    # status, gstin, store_address, store_phone, and tagline — none of these
    # were ever being passed here, so every generated invoice had blank
    # "Billed To", "Document Details", and "Dispatched From" sections.
    context = {
        'order': order,
        'items': items,
        'company_name': store.company_name if store else 'Chachan General Store',
        'tagline': store.tagline if store else 'Premium Corporate Retail & Essentials',
        'gstin': store.gstin if store else '',
        'store_address': store.store_address if store else '',
        'store_phone': store.store_phone if store else '',
        'bill_no': bill_no,
        'customer_phone': order.mobile_number,
        'customer_address': order.address,
        'date': order.created_at,
        'status': order.status,
        'qr_code_base64': qr_base64,
        'barcode_base64': barcode_base64,
    }
    html = get_template('products/invoice_pdf.html').render(context)
    if pisa.CreatePDF(html, dest=response).err: return HttpResponse('Error generating PDF')
    return response

@login_required(login_url='/login/')
def export_products_csv(request):
    if not request.user.is_superuser: return redirect('home')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Bulk_Update.csv"'
    writer = csv.writer(response); writer.writerow(['ID', 'Name', 'Category_ID', 'Category_Name', 'Price'])
    for p in Product.objects.all(): writer.writerow([p.id, p.name, p.category.id if p.category else '', p.category.name if p.category else '', p.price])
    return response

@login_required(login_url='/login/')
def import_products_csv(request):
    if not request.user.is_superuser: return redirect('home')
    if request.method == 'POST' and request.FILES.get('csv_file'):
        reader = csv.DictReader(request.FILES['csv_file'].read().decode('utf-8').splitlines())
        for row in reader:
            if row.get('SKU'): Product.objects.update_or_create(sku=row.get('SKU'), defaults={'name': row.get('Product_Name', 'Unknown'), 'price': row.get('Price') or 0})
        messages.success(request, "✅ Import Complete!")
        return redirect('home')
    return render(request, 'products/import_csv.html')

@login_required(login_url='/login/')
def add_to_wishlist(request, product_id):
    Wishlist.objects.get_or_create(user=request.user, product=get_object_or_404(Product, id=product_id))
    messages.success(request, "Added to Wishlist!")
    return redirect('home')

@login_required(login_url='/login/')
def view_wishlist(request): return render(request, 'products/wishlist.html', {'wishlist': Wishlist.objects.filter(user=request.user)})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id); reviews = product.reviews.all().order_by('-created_at')
    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        if rating := request.POST.get('rating'): Review.objects.create(product=product, user=request.user, rating=int(rating), comment=request.POST.get('comment'))
        return redirect('product_detail', product_id=product.id)
    return render(request, 'products/product_detail.html', {'product': product, 'reviews': reviews, 'avg_rating': round(sum(r.rating for r in reviews)/reviews.count(), 1) if reviews else 0, 'review_count': reviews.count()})

@require_POST
def update_cart_item(request, item_key, action):
    cart = request.session.get('cart', {})
    if item_key in cart:
        # 🌟 FIX: previously, decreasing at quantity=1 fell through to the
        # `else` branch and silently DELETED the item entirely (the "-"
        # button is only disabled client-side via CSS, so a stale page,
        # cached link, or back-button navigation could still trigger this).
        # Now each action is explicit, and decreasing at the minimum does
        # nothing instead of wiping the item out.
        if action == 'increase':
            cart[item_key]['quantity'] += 1
        elif action == 'decrease':
            if cart[item_key]['quantity'] > 1:
                cart[item_key]['quantity'] -= 1
            # else: already at 1, do nothing
        elif action == 'remove':
            cart.pop(item_key, None)
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart_detail')

@login_required(login_url='/login/')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending': order.status = 'Cancelled'; order.save(); messages.success(request, "Order Cancelled.")
    return redirect('profile')

@login_required(login_url='/login/')
# 🌟 FIX: this permanently deletes data but had no method restriction —
# profile.html called it via a plain GET <a> link. Browser link-prefetching
# or accidental navigation could silently delete a saved address with no
# confirmation (the confirm() dialog is JS-only and never runs on a
# prefetch). Now requires an actual POST submission.
@require_POST
def delete_address(request, address_id): get_object_or_404(Address, id=address_id, user=request.user).delete(); return redirect('profile')

@login_required(login_url='/login/')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.name = request.POST.get('name'); address.mobile_number = request.POST.get('mobile'); address.full_address = request.POST.get('full_address'); address.save(); return redirect('profile')
    return render(request, 'products/edit_address.html', {'address': address})

def verify_otp(request):
    if not (user_id := request.session.get('verify_user_id')): return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        try:
            otp_obj = OTPVerification.objects.get(user=user, otp=request.POST.get('otp')); otp_obj.is_verified = True; otp_obj.save(); user.is_active = True; user.save(); del request.session['verify_user_id']; return redirect('login')
        except: messages.error(request, 'Galat OTP!')
    return render(request, 'products/verify_otp.html', {'email': user.email})

# --- AJAX CART ---
def cart_summary_ajax(request):
    cart = request.session.get('cart', {})
    items = sum(item['quantity'] for item in cart.values() if isinstance(item, dict) and 'quantity' in item)
    total = sum(float(item['price']) * int(item['quantity']) for item in cart.values() if isinstance(item, dict) and 'price' in item)
    return JsonResponse({'items': items, 'total': total})

# 🌟 FIX: @csrf_exempt removed — the JS already sends X-CSRFToken correctly,
# so this decorator was only weakening security for no benefit.
def add_to_cart_ajax(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart = request.session.get('cart', {})
        try: data = json.loads(request.body); qty = int(data.get('quantity', 1)); variant_id = data.get('variant_id') 
        except: qty = 1; variant_id = None
            
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            cart_key = f"{product_id}_{variant_id}"; item_name = f"{product.name} ({variant.size_name})"; item_price = float(variant.price)
        else: cart_key = str(product_id); item_name = product.name; item_price = float(product.price)
        
        if cart_key in cart: cart[cart_key]['quantity'] += qty
        else: cart[cart_key] = {'name': item_name, 'price': item_price, 'quantity': qty}
        request.session['cart'] = cart; request.session.modified = True
        return cart_summary_ajax(request)

def remove_from_cart_ajax(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(product_id) in cart: cart.pop(str(product_id), None); request.session['cart'] = cart; request.session.modified = True
        return cart_summary_ajax(request)

# --- FORGOT PASSWORD ---
def forgot_password(request):
    if request.method == 'POST':
        # 🌟 FIX: .get() would raise MultipleObjectsReturned (500 crash) if
        # any duplicate-email accounts already exist from before the
        # CustomRegisterForm uniqueness fix. filter().first() degrades
        # gracefully instead of crashing.
        user = User.objects.filter(email__iexact=request.POST.get('email', '')).first()
        if user:
            otp = str(random.randint(100000, 999999)); OTPVerification.objects.filter(user=user).delete(); OTPVerification.objects.create(user=user, otp=otp, is_verified=False)
            send_brevo_api_email('Password Reset', f'OTP: {otp}', user.email)
            request.session['reset_user_email'] = user.email; return redirect('reset_verify_otp')
        else:
            messages.error(request, 'Account nahi mila.')
    return render(request, 'registration/forgot_password.html')

def reset_verify_otp(request):
    if not (email := request.session.get('reset_user_email')): return redirect('forgot_password')
    if request.method == 'POST':
        try:
            otp_obj = OTPVerification.objects.get(user=User.objects.get(email=email), otp=request.POST.get('otp')); otp_obj.is_verified = True; otp_obj.save(); request.session['can_reset_password'] = True; return redirect('set_new_password')
        except: messages.error(request, 'Galat OTP!')
    return render(request, 'registration/reset_verify_otp.html', {'email': email})

def set_new_password(request):
    if not request.session.get('can_reset_password'): return redirect('forgot_password')
    if request.method == 'POST':
        pwd = request.POST.get('password')
        if pwd != request.POST.get('confirm_password'): messages.error(request, 'Passwords mismatch')
        else:
            user = User.objects.get(email=request.session.get('reset_user_email')); user.set_password(pwd); user.save(); OTPVerification.objects.filter(user=user).delete()
            del request.session['reset_user_email']; del request.session['can_reset_password']; messages.success(request, 'Password changed!'); return redirect('login')
    return render(request, 'registration/set_new_password.html')

# 🤖 AI ASSISTANT CHAT LOGIC (Super Smart & Accurate - Llama 3.1)
# 🌟 FIX: @csrf_exempt removed — base.html's JS already sends X-CSRFToken.
def ai_assistant_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'response': 'Kripya apna sawal puchein.'})

            api_key = os.environ.get('GROQ_API_KEY')
            if not api_key:
                return JsonResponse({'response': '🛑 Error: Render par GROQ_API_KEY set nahi hai.'})

            system_prompt = (
                "Aapka naam 'CGSMART Assistant' hai. Aap 'Chachan General Store' (jise CGSMART bhi kehte hain) ke official customer support AI hain.\n"
                "AAPKO STRICTLY IN FACTS KO FOLLOW KARNA HAI (Apni taraf se kuch guess nahi karna):\n"
                "1. Store Name: Chachan General Store (Is naam ko kabhi Chandan ya kuch aur mat likhna).\n"
                "2. Location: Nohar, Rajasthan.\n"
                "3. Customer Care / WhatsApp Number: +91 7357073316.\n"
                "4. Delivery Policy: ₹999 se upar ke orders par Free Home Delivery available hai.\n"
                "5. Payment Options: Cash on Delivery (COD), UPI, aur Credit/Debit Cards.\n"
                "6. Promo Code: Checkout par 'CGSMART10' code lagane se extra discount milta hai.\n\n"
                "Rules for talking:\n"
                "- Hamesha polite aur friendly Hinglish (Hindi written in English alphabet) mein reply dein.\n"
                "- Reply chota aur to-the-point rakhein (max 2-3 lines).\n"
                "- Agar user aisi baat pooche jo aapko nahi pata, toh politely kahein: 'Kripya is jankari ke liye humein 7357073316 par WhatsApp karein.'"
            )

            url = "https://api.groq.com/openai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 150
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                ai_reply = response.json()['choices'][0]['message']['content']
                return JsonResponse({'response': ai_reply})
            else:
                return JsonResponse({'response': f"🛑 Groq API Error: {response.text}"})

        except Exception as e:
            return JsonResponse({'response': f"🛑 System Error: {str(e)}"})

    return JsonResponse({'error': 'Invalid request'}, status=400)