from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, Coupon, Order, OrderItem

# 🏠 1. Homepage View with Search Functionality
def product_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        products = Product.objects.filter(name__icontains=search_query)
    else:
        products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

# 🛒 2. Add to Cart Logic using Session
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    product_id_str = str(product_id)
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += 1
    else:
        cart[product_id_str] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1
        }
    
    request.session['cart'] = cart
    messages.success(request, f"{product.name} cart me add ho gaya hai!")
    return redirect('home')

# 📊 3. Cart Detail View (With Safe Subscript Check)
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    
    # Agar data structure corrupt ho toh use handle karne ke liye safe dynamic loop
    for pid, item in list(cart.items()):
        # Check agar item ek dictionary hai ya nahi (int object check handle karne ke liye)
        if isinstance(item, dict) and 'price' in item and 'quantity' in item:
            product = get_object_or_404(Product, id=int(pid))
            total_price = item['price'] * item['quantity']
            cart_total += total_price
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total_price': total_price
            })
        else:
            # Agar koi purana format integer ya kharab data hai, toh use clear kar dein
            cart.pop(pid, None)
            request.session['cart'] = cart
        
    return render(request, 'products/cart_detail.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })

# 💳 4. Checkout Page with Mobile Coupon Verification & Order Creation
def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Aapka cart khali hai!")
        return redirect('home')
        
    cart_total = 0
    for pid, item in cart.items():
        cart_total += item['price'] * item['quantity']
        
    if request.method == 'POST':
        name = request.POST.get('name')
        mobile = request.POST.get('mobile_number')
        address = request.POST.get('address')
        
        # 🎟️ Verification check: Unused coupon validation
        active_coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
        final_total = float(cart_total)
        
        if active_coupon:
            discount_amount = (final_total * active_coupon.discount_percentage) / 100
            final_total -= discount_amount
            active_coupon.is_used = True
            active_coupon.save()

        # 📦 Order create karna (ERP ke data consumption ke liye)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=name,
            mobile_number=mobile,
            address=address,
            total_amount=final_total,
            applied_coupon=active_coupon,
            status='Pending'
        )
        
        # 🛒 Individual items ko map karke pipeline me daalna
        for pid, item in cart.items():
            OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                price=item['price'],
                quantity=item['quantity']
            )
            
        # 🎁 Next time promotion generation structure
        new_coupon = None
        if final_total >= 999:
            new_code = f"CGS10-{order.id}"
            new_coupon = Coupon.objects.create(code=new_code, mobile_number=mobile, discount_percentage=10)
        elif final_total >= 699:
            new_code = f"CGS08-{order.id}"
            new_coupon = Coupon.objects.create(code=new_code, mobile_number=mobile, discount_percentage=8)

        # Session cart ko drop karna billing cycle hone par
        request.session['cart'] = {}
        
        # Trigger dynamic simple inline summary for customer acknowledgment
        return render(request, 'products/order_success.html', {
            'order': order, 
            'new_coupon': new_coupon
        })

    return render(request, 'products/checkout.html', {'cart_total': cart_total})

# 🔍 5. AJAX Endpoint to scan active coupon backend records instantly
def check_coupon_ajax(request):
    mobile = request.GET.get('mobile', '')
    coupon = Coupon.objects.filter(mobile_number=mobile, is_used=False).first()
    if coupon:
        return JsonResponse({
            'status': 'found', 
            'discount': coupon.discount_percentage, 
            'code': coupon.code
        })
    return JsonResponse({'status': 'not_found'})

# 📄 6. Static Pages Views
def about_page(request):
    return render(request, 'products/about.html')

def contact_page(request):
    return render(request, 'products/contact.html')

# 👤 7. Custom Safe Authentication System
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

# 🤫 8. Hidden ERP / Superuser Automation Actions
def make_admin(request):
    # Aapka dynamic inline logic configuration code
    return render(request, 'products/admin_trigger.html')

def trigger_import(request):
    # Bulk import engine runtime script execution code
    return render(request, 'products/import_trigger.html')