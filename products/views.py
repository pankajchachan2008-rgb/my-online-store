from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Order, OrderItem

# 1. Homepage View (With Search and Cart Count)
def product_list(request):
    query = request.GET.get('search')
    
    # Agar user ne kuch search kiya hai toh filter karo, nahi toh saare products dikhao
    if query:
        all_products = Product.objects.filter(name__icontains=query)
    else:
        all_products = Product.objects.all()
        
    # Cart me total kitne items hain count karne ke liye
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    
    return render(request, 'products/product_list.html', {
        'products': all_products,
        'cart_count': cart_count,
        'query': query
    })

# 2. Add to Cart View
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1
        
    request.session['cart'] = cart
    return redirect('home')

# 3. Cart Details & Checkout View
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_amount = 0
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        total_amount += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
        
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if cart_items:
            # Order database me save karein
            order = Order.objects.create(
                customer_name=name,
                phone=phone,
                address=address,
                total_amount=total_amount
            )
            
            # Har ek item ko order se connect karein aur stock kam karein
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['product'].price,
                    quantity=item['quantity']
                )
                item['product'].stock -= item['quantity']
                item['product'].save()
                
            # Checkout ke baad cart khali karein
            request.session['cart'] = {}
            return render(request, 'products/order_success.html', {'order': order})

    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })