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
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from django.db.models import Avg, F, ExpressionWrapper, FloatField
from django.views.decorators.cache import never_cache
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from datetime import timedelta

# 🌟 100% SAFE SMART SEARCH IMPORTS
from django.db.models import Q
import difflib

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

from .models import Product, Category, SubCategory, Coupon, Order, OrderItem, CustomerProfile, Banner, Wishlist, ProductVariant, Address, WalletTransaction, StoreSetting, Brand, Review, CustomerLedger

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

# 🏠 1. Homepage View (With Safe Smart Search & Typo Handling)
def product_list(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()
    products = Product.objects.select_related('brand', 'category').prefetch_related('variants')
    banners = Banner.objects.filter(is_active=True).select_related('category').order_by('-id')

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

    # 🌟 SAFE SMART SEARCH (Typo / Spelling Mistake Handler)
    if search_query:
        exact_matches = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(brand__name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

        if exact_matches.exists():
            products = exact_matches
        else:
            all_product_names = Product.objects.values_list('name', flat=True)
            closest_matches = difflib.get_close_matches(search_query, all_product_names, n=4, cutoff=0.4)
            
            if closest_matches:
                products = products.filter(name__in=closest_matches)
            else:
                products = exact_matches

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

    # 🌟 ADVANCED DISCOUNT FILTER
    if discount:
        try:
            discount_val = float(discount)
            products = products.filter(mrp__isnull=False, mrp__gt=0).annotate(
                calc_discount=ExpressionWrapper(
                    (F('mrp') - F('price')) * 100.0 / F('mrp'),
                    output_field=FloatField()
                )
            ).filter(calc_discount__gte=discount_val)
        except (ValueError, TypeError):
            pass
        
    if rating:
        try:
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

# 🛒 2. Add to Cart (With "Buy Now" Smart Logic)
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

    # 🌟 "Buy Now" Button ka Logic
    if request.POST.get('buy_now'):
        return redirect('checkout')
        
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
@never_cache   
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

# 📡 APIs
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
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    store = StoreSetting.objects.first()
    bill_no = f"#INV-2026-{order.id}"

    qr = qrcode.make(bill_no)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")

    bc = barcode.get_barcode_class('code128')(bill_no, writer=ImageWriter())
    bc_buffer = BytesIO()
    bc.write(bc_buffer, options={'write_text': False})
    barcode_base64 = base64.b64encode(bc_buffer.getvalue()).decode("utf-8")
    
    total_amt = float(order.total_amount)
    subtotal = total_amt / 1.18
    cgst = (total_amt - subtotal) / 2
    sgst = cgst
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CGSmart_Bill_{order.id}.pdf"'
    
    context = {
        'order': order,
        'items': items,
        'company_name': store.store_name if store else 'Chachan General Store',
        'tagline': store.tagline if store else 'Premium Corporate Retail & Essentials',
        'gstin': store.gstin if store else '',
        'store_address': store.address if store else '',
        'store_phone': store.phone if store else '',
        'bill_no': bill_no,
        'customer_phone': order.mobile_number,
        'customer_address': order.address,
        'date': order.created_at,
        'status': order.status,
        'qr_code_base64': qr_base64,
        'barcode_base64': barcode_base64,
        'subtotal': subtotal,
        'cgst': cgst,
        'sgst': sgst,
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

@login_required(login_url='/login/')
@require_POST
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, "Item wishlist se hata diya gaya!")
    return redirect('view_wishlist')

# 📝 Product Detail View
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by('-created_at')
    
    similar_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4] if product.category else Product.objects.none()

    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        review_image = request.FILES.get('review_image')

        if rating: 
            Review.objects.create(
                product=product, 
                user=request.user, 
                rating=int(rating), 
                comment=comment,
                image=review_image
            )
            messages.success(request, "✅ Aapka review submit ho gaya!")
        return redirect('product_detail', product_id=product.id)
    
    return render(request, 'products/product_detail.html', {'product': product, 'reviews': reviews, 'similar_products': similar_products, 'avg_rating': round(sum(r.rating for r in reviews)/reviews.count(), 1) if reviews else 0, 'review_count': reviews.count()})

@require_POST
def update_cart_item(request, item_key, action):
    cart = request.session.get('cart', {})
    if item_key in cart:
        if action == 'increase':
            cart[item_key]['quantity'] += 1
        elif action == 'decrease':
            if cart[item_key]['quantity'] > 1:
                cart[item_key]['quantity'] -= 1
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
@require_POST
def delete_address(request, address_id): get_object_or_404(Address, id=address_id, user=request.user).delete(); return redirect('profile')

@login_required(login_url='/login/')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.name = request.POST.get('name'); address.mobile_number = request.POST.get('mobile'); address.full_address = request.POST.get('full_address'); address.save(); return redirect('profile')
    return render(request, 'products/edit_address.html', {'address': address})

def verify_otp(request):
    if not (user_id := request.session.get('verify_user_id')): 
        return redirect('login')
    user = User.objects.get(id=user_id)
    if request.method == 'POST':
        try:
            otp_obj = OTPVerification.objects.get(user=user, otp=request.POST.get('otp'))
            otp_obj.is_verified = True
            otp_obj.save()
            user.is_active = True
            user.save()
            del request.session['verify_user_id']
            return redirect('login')
        except OTPVerification.DoesNotExist: 
            messages.error(request, 'Galat OTP!')
    return render(request, 'products/verify_otp.html', {'email': user.email})

# --- AJAX CART ---
def cart_summary_ajax(request):
    cart = request.session.get('cart', {})
    items = sum(item['quantity'] for item in cart.values() if isinstance(item, dict) and 'quantity' in item)
    total = sum(float(item['price']) * int(item['quantity']) for item in cart.values() if isinstance(item, dict) and 'price' in item)
    return JsonResponse({'items': items, 'total': total})

@csrf_exempt
def add_to_cart_ajax(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        cart = request.session.get('cart', {})
        try: 
            data = json.loads(request.body)
            qty = int(data.get('quantity', 1))
            variant_id = data.get('variant_id') 
        except (json.JSONDecodeError, ValueError, TypeError): 
            qty = 1
            variant_id = None
            
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
            cart[cart_key]['quantity'] += qty
        else: 
            cart[cart_key] = {'name': item_name, 'price': item_price, 'quantity': qty}
        request.session['cart'] = cart
        request.session.modified = True
        return cart_summary_ajax(request)

@csrf_exempt
def remove_from_cart_ajax(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(product_id) in cart: 
            cart.pop(str(product_id), None)
            request.session['cart'] = cart
            request.session.modified = True
        return cart_summary_ajax(request)

# --- FORGOT PASSWORD ---
def forgot_password(request):
    if request.method == 'POST':
        user = User.objects.filter(email__iexact=request.POST.get('email', '')).first()
        if user:
            otp = str(random.randint(100000, 999999))
            OTPVerification.objects.filter(user=user).delete()
            OTPVerification.objects.create(user=user, otp=otp, is_verified=False)
            send_brevo_api_email('Password Reset', f'OTP: {otp}', user.email)
            request.session['reset_user_email'] = user.email
            return redirect('reset_verify_otp')
        else:
            messages.error(request, 'Account nahi mila.')
    return render(request, 'registration/forgot_password.html')

def reset_verify_otp(request):
    if not (email := request.session.get('reset_user_email')): return redirect('forgot_password')
    if request.method == 'POST':
        try:
            user = User.objects.get(email=email)
            otp_obj = OTPVerification.objects.get(user=user, otp=request.POST.get('otp'))
            otp_obj.is_verified = True
            otp_obj.save()
            request.session['can_reset_password'] = True
            return redirect('set_new_password')
        except (OTPVerification.DoesNotExist, User.DoesNotExist): 
            messages.error(request, 'Galat OTP!')
    return render(request, 'registration/reset_verify_otp.html', {'email': email})

def set_new_password(request):
    if not request.session.get('can_reset_password'): return redirect('forgot_password')
    if request.method == 'POST':
        pwd = request.POST.get('password')
        if pwd != request.POST.get('confirm_password'): messages.error(request, 'Passwords mismatch')
        else:
            user = User.objects.get(email=request.session.get('reset_user_email'))
            user.set_password(pwd)
            user.save()
            OTPVerification.objects.filter(user=user).delete()
            del request.session['reset_user_email']
            del request.session['can_reset_password']
            messages.success(request, 'Password changed!')
            return redirect('login')
    return render(request, 'registration/set_new_password.html')

# 🤖 AI ASSISTANT CHAT LOGIC
@csrf_exempt
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
                print(f"Groq API Error: {response.text}")
                return JsonResponse({'response': "Maafi chahunga, abhi system thoda busy hai. Kripya humein WhatsApp par message karein!"})

        except Exception as e:
            print(f"System Error in AI Chat: {str(e)}")
            return JsonResponse({'response': "Technical error aaya hai, humari team isey theek kar rahi hai. Kripya WhatsApp par sampark karein."})

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ==========================================
# 🏢 CUSTOM ERP / ADMIN DASHBOARD SECTION
# ==========================================

@staff_member_required(login_url='/login/')
def erp_dashboard(request):
    total_orders = Order.objects.count()
    total_sales = Order.objects.filter(status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_orders = Order.objects.filter(status='Pending').count()
    total_customers = User.objects.filter(is_staff=False).count()

    recent_orders = Order.objects.all().order_by('-created_at')[:10]

    context = {
        'total_orders': total_orders,
        'total_sales': total_sales,
        'pending_orders': pending_orders,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
    }
    return render(request, 'erp/dashboard.html', context)

@staff_member_required(login_url='/login/')
def erp_update_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        courier_name = request.POST.get('courier_name')
        tracking_id = request.POST.get('tracking_id')
        tracking_url = request.POST.get('tracking_url')

        if new_status: order.status = new_status
        if courier_name: order.courier_name = courier_name
        if tracking_id: order.tracking_id = tracking_id
        if tracking_url: order.tracking_url = tracking_url
            
        order.save()
        return redirect('erp_dashboard')
    
    return render(request, 'erp/update_order.html', {'order': order})

# 🏢 ERP Product Master & Bulk Update
@staff_member_required(login_url='/login/')
def erp_products(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids[]')
        for p_id in product_ids:
            new_name = request.POST.get(f'name_{p_id}')
            new_stock = request.POST.get(f'stock_{p_id}')
            new_price = request.POST.get(f'price_{p_id}')

            product = Product.objects.filter(id=p_id).first()
            if product:
                if new_name: product.name = new_name
                if new_stock is not None and new_stock != '': product.stock = int(new_stock)
                if new_price is not None and new_price != '': product.price = float(new_price)
                product.save()
        
        return redirect('erp_products')

    products = Product.objects.all().order_by('-id')
    return render(request, 'erp/products.html', {'products': products})

@staff_member_required(login_url='/login/')
def erp_add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description', '')
        hsn_code = request.POST.get('hsn_code', '')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        category = Category.objects.filter(id=category_id).first()

        Product.objects.create(
            name=name, price=price, stock=stock, description=description,
            hsn_code=hsn_code, category=category, image=image
        )
        return redirect('erp_products')
    
    categories = Category.objects.all()
    return render(request, 'erp/add_product.html', {'categories': categories})

# 🏢 ERP Billing & POS Screen
@staff_member_required(login_url='/login/')
def erp_pos_billing(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    store_setting = StoreSetting.objects.first()
    context = {
        'products': products,
        'categories': categories,
        'store_setting': store_setting,
    }
    return render(request, 'erp/pos.html', context)

# 📒 ERP Customer Ledger & Khata View
@staff_member_required(login_url='/login/')
def erp_customer_ledger(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        mobile_number = request.POST.get('mobile_number')
        transaction_type = request.POST.get('transaction_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description')

        CustomerLedger.objects.create(
            customer_name=customer_name,
            mobile_number=mobile_number,
            transaction_type=transaction_type,
            amount=amount,
            description=description
        )
        return redirect('erp_ledger')

    ledgers = CustomerLedger.objects.all().order_by('-created_at')
    
    total_udhaar = CustomerLedger.objects.filter(transaction_type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_jama = CustomerLedger.objects.filter(transaction_type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
    net_balance = total_udhaar - total_jama

    context = {
        'ledgers': ledgers,
        'total_udhaar': total_udhaar,
        'total_jama': total_jama,
        'net_balance': net_balance,
    }
    return render(request, 'erp/ledger.html', context)

# 🏢 ERP Store Settings View
@staff_member_required(login_url='/login/')
def erp_store_settings(request):
    setting, created = StoreSetting.objects.get_or_create(pk=1)
    if request.method == 'POST':
        setting.store_name = request.POST.get('store_name', setting.store_name)
        setting.owner_name = request.POST.get('owner_name', setting.owner_name)
        setting.phone = request.POST.get('phone', setting.phone)
        setting.address = request.POST.get('address', setting.address)
        setting.gstin = request.POST.get('gstin', setting.gstin)
        setting.receipt_footer = request.POST.get('receipt_footer', setting.receipt_footer)
        setting.save()
        return redirect('erp_settings')
    
    return render(request, 'erp/settings.html', {'setting': setting})

def search_suggestions(api_request):
    query = api_request.GET.get('q', '').strip()
    results = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand__name__icontains=query)
        )[:6]  # Top 6 results
        
        for p in products:
            results.append({
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'url': f"/product/{p.id}/",
                'image': p.image.url if p.image else ''
            })
    return JsonResponse({'products': results})