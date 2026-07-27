import csv
import random
import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
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
from .models import OTPVerification
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .forms import CustomRegisterForm
from django.utils import timezone # 🌟 NAYA IMPORT

from .models import Product, Category, Coupon, Order, OrderItem, CustomerProfile, Banner, Wishlist, ProductVariant, Address, WalletTransaction, StoreSetting

def ping(request):
    return HttpResponse("OK", status=200)

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
    
    paginator = Paginator(products, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'products/product_list.html', {
        'products': page_obj,  
        'categories': categories,
        'banners': banners,
        'active_category': active_category,
        'search_query': search_query,
        'current_sort': sort
    })

# 🛒 2. Add to Cart
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
            except Product.DoesNotExist:
                cart.pop(pid, None)
                cart_modified = True
            except ValueError:
                cart.pop(pid, None)
                cart_modified = True
        else:
            cart.pop(pid, None)
            cart_modified = True
            
    if cart_modified:
        request.session['cart'] = cart
        request.session.modified = True
        
    return render(request, 'products/cart_detail.html', {'cart_items': cart_items, 'cart_total': cart_total})

# 🛍️ 4. Checkout Page
def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')
        
    subtotal = 0
    total_mrp = 0
    hidden_discount_total = 0
    order_items_list = []
    
    profile = None
    wallet_balance = 0
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
                if product.mrp:
                    total_mrp += float(product.mrp) * item_qty
                else:
                    total_mrp += item_price * item_qty 
                    
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
            selected_address = Address.objects.get(id=address_id, user=request.user)
            name = selected_address.name
            mobile = selected_address.mobile_number
            address = f"{selected_address.full_address}, {selected_address.locality}, {selected_address.city}, {selected_address.state} - {selected_address.pincode}"
        else:
            name = request.POST.get('name')
            mobile = request.POST.get('mobile_number')
            address = request.POST.get('address')
        
        # 🌟 NAYA LOGIC: Promo Code Verification Backend Side
        promo_code = request.POST.get('promo_code', '').strip().upper()
        active_coupon = None
        coupon_discount_applied = 0
        
        if promo_code:
            coupon = Coupon.objects.filter(code=promo_code, is_active=True).first()
            if coupon:
                now = timezone.now()
                if (not coupon.valid_from or now >= coupon.valid_from) and \
                   (not coupon.valid_to or now <= coupon.valid_to) and \
                   (final_total >= coupon.min_order_amount):
                    
                    coupon_discount_applied = (final_total * coupon.discount_percentage) / 100
                    if coupon.max_discount_amount and coupon_discount_applied > float(coupon.max_discount_amount):
                        coupon_discount_applied = float(coupon.max_discount_amount)
                    
                    final_total -= coupon_discount_applied
                    active_coupon = coupon

        # Wallet Deduction
        use_wallet = request.POST.get('use_wallet')
        wallet_deducted = 0
        
        if use_wallet == 'on' and profile and profile.wallet_balance > 0:
            if profile.wallet_balance >= final_total:
                wallet_deducted = final_total
                profile.wallet_balance -= final_total
                final_total = 0
            else:
                wallet_deducted = profile.wallet_balance
                final_total -= profile.wallet_balance
                profile.wallet_balance = 0
            profile.save()

        # Order Create karna
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name, mobile_number=mobile, address=address,
            total_amount=final_total, applied_coupon=active_coupon, status='Pending'
        )

        if wallet_deducted > 0:
            WalletTransaction.objects.create(
                user=request.user,
                transaction_type='DEBIT',
                amount=wallet_deducted,
                description=f"Used for Order #{order.id}"
            )
        
        for pid, item in cart.items():
            if isinstance(item, dict):
                OrderItem.objects.create(order=order, product_name=item['name'], price=item['price'], quantity=item['quantity'])
            
        items_str = "\n".join(order_items_list)
        coupon_text = f"\n*Coupon Discount:* ₹{coupon_discount_applied}" if coupon_discount_applied > 0 else ""
        wa_text = f"📢 *Naya Order Aaya Hai!*\n\n*Order ID:* #{order.id}\n*Customer:* {name}\n*Mobile:* {mobile}\n*Address:* {address}\n\n*Items:*\n{items_str}\n*Delivery Charge:* ₹{delivery_fee}{coupon_text}\n*Wallet Used:* ₹{wallet_deducted}\n*Total Payable:* ₹{final_total}"
        
        whatsapp_url = f"https://wa.me/917357073316?{urlencode({'text': wa_text})}"

        request.session['cart'] = {}
        return render(request, 'products/order_success.html', {
            'order': order, 
            'whatsapp_url': whatsapp_url 
        })

    saved_addresses = Address.objects.filter(user=request.user) if request.user.is_authenticated else []

    context = {
        'cart_total': subtotal,
        'total_mrp': total_mrp,
        'regular_discount': regular_discount,
        'hidden_discount_total': hidden_discount_total,
        'delivery_fee': delivery_fee,
        'final_total': final_total,
        'total_savings': total_savings,
        'saved_addresses': saved_addresses,
        'profile': profile,
    }
    return render(request, 'products/checkout.html', context)

# 👤 5. Premium Profile Page
@login_required(login_url='/login/')
def profile_page(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('home')
        
    profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            
            profile.mobile_number = request.POST.get('mobile_number', '')
            
            if 'profile_photo' in request.FILES:
                profile.profile_photo = request.FILES['profile_photo']
                
            profile.save()
            messages.success(request, "✅ Profile updated successfully!")
            
        elif action == 'add_address':
            Address.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                mobile_number=request.POST.get('mobile'),
                pincode=request.POST.get('pincode'),
                locality=request.POST.get('locality'),
                full_address=request.POST.get('full_address'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                address_type=request.POST.get('address_type', 'Home')
            )
            messages.success(request, "✅ New address added!")
            
        return redirect('profile')

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    addresses = Address.objects.filter(user=request.user)
    transactions = WalletTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'profile': profile,
        'orders': orders,
        'addresses': addresses,
        'transactions': transactions 
    }
    return render(request, 'products/profile.html', context)

# 🗑️ Delete Account
@login_required(login_url='/login/')
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Aapka account hamesha ke liye delete kar diya gaya hai.")
        return redirect('home')
    return redirect('profile')

# 🔍 6. AJAX NAYA UNIVERSAL COUPON CHECK
def check_coupon_ajax(request):
    code = request.GET.get('code', '').strip().upper()
    try:
        cart_total = float(request.GET.get('cart_total', 0))
    except ValueError:
        cart_total = 0

    if not code:
        return JsonResponse({'status': 'not_found', 'message': 'Please enter a coupon code.'})

    coupon = Coupon.objects.filter(code=code, is_active=True).first()

    if not coupon:
        return JsonResponse({'status': 'not_found', 'message': 'Invalid or expired coupon code.'})

    now = timezone.now()
    if coupon.valid_from and now < coupon.valid_from:
        return JsonResponse({'status': 'error', 'message': 'Coupon is not yet active.'})
    if coupon.valid_to and now > coupon.valid_to:
        return JsonResponse({'status': 'error', 'message': 'Coupon has expired.'})

    if cart_total < coupon.min_order_amount:
        return JsonResponse({'status': 'error', 'message': f'Min. order amount of ₹{coupon.min_order_amount} required.'})

    discount_amount = (cart_total * coupon.discount_percentage) / 100
    if coupon.max_discount_amount and discount_amount > float(coupon.max_discount_amount):
        discount_amount = float(coupon.max_discount_amount)

    return JsonResponse({
        'status': 'found', 
        'discount_percentage': coupon.discount_percentage,
        'discount_amount': discount_amount,
        'message': f'Coupon {code} applied successfully!'
    })

# 📄 7. Static Pages
def about_page(request): return render(request, 'products/about.html')
def contact_page(request): return render(request, 'products/contact.html')

def custom_logout(request):
    logout(request)
    return redirect('home')

def make_admin(request):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@cgsmart.in', 'Admin@1234')
        return HttpResponse("""
            <div style='text-align:center; margin-top:50px; font-family:sans-serif;'>
                <h2 style='color: green;'>✅ Admin Account Successfully Created!</h2>
                <a href='/secret-cgs-main/' style='padding:10px 20px; background:#2874f0; color:white; text-decoration:none; border-radius:5px;'>Go to Admin Panel</a>
            </div>
        """)
    else:
        return HttpResponse("""
            <div style='text-align:center; margin-top:50px; font-family:sans-serif;'>
                <h2 style='color: orange;'>⚠️ Admin Account Maujood Hai!</h2>
                <a href='/secret-cgs-main/' style='padding:10px 20px; background:#2874f0; color:white; text-decoration:none; border-radius:5px;'>Go to Admin Panel</a>
            </div>
        """)

def trigger_import(request): return render(request, 'products/import_trigger.html')

def register_page(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            # 1. User ko database me save karein, par abhi activate na karein
            user = form.save(commit=False)
            user.is_active = False  # Bina OTP verify kiye user login na kar paye
            user.save()

            # 2. OTP Generate aur database me save karein
            otp = str(random.randint(100000, 999999))
            OTPVerification.objects.create(user=user, otp=otp)

            # 3. User ko Email bhejein (yahan user.email form me hona zaroori hai)
            subject = 'CGSmart - Account Verification OTP'
            message = f'Hello {user.username},\n\nAapka account verification OTP hai: {otp}\n\nKripya is OTP ko website par daalkar apna account verify karein.'
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)

            # 4. Session me user ki ID save karein aur Verify page par bhej dein
            request.session['verify_user_id'] = user.id
            messages.success(request, 'Account successfully ban gaya hai! Kripya apne email par aaya OTP daalein.')
            return redirect('verify_otp')
    else:
        form = CustomRegisterForm()
        
    return render(request, 'registration/register.html', {'form': form})

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

# 📄 10. Download Smart PDF Invoice / Bill of Supply
@login_required(login_url='/login/')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = OrderItem.objects.filter(order=order)
    
    # 🌟 Admin panel se custom details fetch kar rahe hain
    store_settings = StoreSetting.objects.first()
    company_name = store_settings.company_name if store_settings else 'Chachan General Store'
    tagline = store_settings.tagline if store_settings else 'Premium Corporate Retail & Essentials'
    store_address = store_settings.store_address if store_settings else ''
    store_phone = store_settings.store_phone if store_settings else ''
    gstin = store_settings.gstin if store_settings else ''
    
    bill_no = f"#INV-2026-{order.id}"

    # QR & Barcode Setup
    qr = qrcode.make(bill_no)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode("utf-8")

    CODE128 = barcode.get_barcode_class('code128')
    bc = CODE128(bill_no, writer=ImageWriter())
    bc_buffer = BytesIO()
    bc.write(bc_buffer, options={'write_text': False}) 
    barcode_base64 = base64.b64encode(bc_buffer.getvalue()).decode("utf-8")
    
    template_path = 'products/invoice_pdf.html'
    
    context = {
        'order': order, 
        'items': items,
        'company_name': company_name,
        'tagline': tagline,
        'store_address': store_address,
        'store_phone': store_phone,
        'gstin': gstin,
        'bill_no': bill_no,
        'customer_name': order.customer_name,
        'customer_phone': order.mobile_number,
        'customer_address': order.address,
        'date': order.created_at.strftime('%d %b, %Y') if hasattr(order, 'created_at') else '',
        'status': order.status,
        'qr_code_base64': qr_base64,
        'barcode_base64': barcode_base64,
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CGSmart_Bill_{order.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Document generate karne mein error aayi: <pre>' + html + '</pre>')
    return response

@login_required(login_url='/login/')
def export_products_csv(request):
    if not request.user.is_superuser:
        messages.error(request, "⛔ Access Denied!")
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

@login_required(login_url='/login/')
def import_products_csv(request):
    if not request.user.is_superuser:
        messages.error(request, "⛔ Access Denied!")
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
                if row.get('Price'): product.price = row['Price']
                if row.get('Weight'): product.weight = row['Weight']
                cat_id = row.get('Category_ID')
                if cat_id:
                    try:
                        category = Category.objects.get(id=cat_id)
                        product.category = category
                    except Category.DoesNotExist: pass 
                product.save()
                success_count += 1
            except Product.DoesNotExist: error_count += 1
            except Exception as e: error_count += 1
                
        messages.success(request, f"✅ Bulk Update Complete! {success_count} products update hue.")
        return redirect('home')
        
    return render(request, 'products/import_csv.html')

@login_required(login_url='/login/')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if created: messages.success(request, f"{product.name} aapki Wishlist mein add ho gaya!")
    else: messages.info(request, "Yeh product pehle se aapki Wishlist mein hai.")
    return redirect('home')

@login_required(login_url='/login/')
def view_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    return render(request, 'products/wishlist.html', {'wishlist': wishlist})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})

def update_cart_item(request, item_key, action):
    cart = request.session.get('cart', {})
    if item_key in cart:
        if action == 'increase': cart[item_key]['quantity'] += 1
        elif action == 'decrease':
            if cart[item_key]['quantity'] > 1: cart[item_key]['quantity'] -= 1
            else: cart.pop(item_key, None)
        elif action == 'remove': cart.pop(item_key, None)
        
        request.session['cart'] = cart
        request.session.modified = True
        
    return redirect('cart_detail')

@login_required(login_url='/login/')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, f"✅ Order #{order.id} successfully cancel ho gaya hai.")
    else:
        messages.error(request, f"❌ Order #{order.id} ab cancel nahi kiya ja sakta.")
    return redirect('profile')

# 📍 Address Management Logic
@login_required(login_url='/login/')
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "✅ Address deleted successfully!")
    return redirect('profile')

# (Edit ke liye hum simple update logic use karenge)
@login_required(login_url='/login/')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.name = request.POST.get('name')
        address.mobile_number = request.POST.get('mobile')
        address.pincode = request.POST.get('pincode')
        address.locality = request.POST.get('locality')
        address.full_address = request.POST.get('full_address')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.save()
        messages.success(request, "✅ Address updated!")
        return redirect('profile')
    return render(request, 'products/edit_address.html', {'address': address})

def verify_otp(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('login') # Agar direct access kare toh login par bhej do

    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            # Check karein ki OTP sahi hai ya nahi
            otp_obj = OTPVerification.objects.get(user=user, otp=entered_otp)
            otp_obj.is_verified = True
            otp_obj.save()

            # OTP sahi hai toh user ko active kar dein
            user.is_active = True
            user.save()

            del request.session['verify_user_id'] # Session saaf kar dein
            messages.success(request, 'Account successfully verified! Ab aap login kar sakte hain.')
            return redirect('login')
        except OTPVerification.DoesNotExist:
            messages.error(request, 'Galat OTP! Kripya sahi OTP daalein.')

    return render(request, 'products/verify_otp.html', {'email': user.email})