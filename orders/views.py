from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Cart, CartItem, Order, OrderItem
from store.models import Product
import json
import requests
import uuid

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
        
        if product.stock_quantity < quantity:
            return JsonResponse({'error': 'Not enough stock'}, status=400)
            
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
            
        cart_item.save()
        
        return JsonResponse({'message': 'Item added to cart', 'cart_count': cart.items.count()})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({'message': 'Item removed'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def update_cart_quantity(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity'))
        
        if quantity < 1:
            return JsonResponse({'error': 'Quantity must be positive'}, status=400)
            
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if cart_item.product.stock_quantity < quantity:
            return JsonResponse({'error': 'Not enough stock'}, status=400)
            
        cart_item.quantity = quantity
        cart_item.save()
        return JsonResponse({'message': 'Cart updated'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def calculate_shipping(city):
    # Simple logic: Lagos = 1000, others = 2500
    if city and 'lagos' in city.lower():
        return 1000.00
    return 2500.00

@login_required
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        return redirect('cart')
        
    context = {
        'cart': cart,
        'flutterwave_public_key': settings.FLUTTERWAVE_PUBLIC_KEY,
        'user': request.user
    }
    return render(request, 'checkout.html', context)

@login_required
def place_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        address = data.get('address')
        city = data.get('city')
        state = data.get('state')
        
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
             return JsonResponse({'error': 'Cart is empty'}, status=400)

        shipping_fee = calculate_shipping(city)
        total_amount = float(cart.total_price) + shipping_fee
        
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            shipping_fee=shipping_fee,
            shipping_address=address,
            city=city,
            state=state,
            status='Pending'
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.discount_price if item.product.discount_price else item.product.price,
                quantity=item.quantity
            )
            
        return JsonResponse({
            'message': 'Order created',
            'order_id': order.order_id,
            'tx_ref': order.order_id,
            'amount': total_amount,
            'email': request.user.email,
            'phone': request.user.profile.phone if hasattr(request.user, 'profile') else '',
            'name': request.user.get_full_name()
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        order_id = data.get('order_id')

        if not transaction_id or not order_id:
            return JsonResponse({'error': 'Missing transaction_id or order_id'}, status=400)

        # Verify transaction with Flutterwave
        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        
        response = requests.get(url, headers=headers)
        res_data = response.json()
        
        if res_data['status'] == 'success' and res_data['data']['status'] == 'successful':
            amount_paid = res_data['data']['amount']
            currency = res_data['data']['currency']
            tx_ref = res_data['data']['tx_ref']
            
            # Verify order matches
            if tx_ref != order_id:
                 return JsonResponse({'error': 'Transaction reference mismatch'}, status=400)

            order = get_object_or_404(Order, order_id=order_id)
            
            if float(amount_paid) >= float(order.total_amount) and currency == 'NGN':
                if order.status != 'Paid':
                    order.status = 'Paid'
                    order.flutterwave_ref = str(transaction_id)
                    order.save()
                    
                    # Reduce stock
                    for item in order.items.all():
                        item.product.stock_quantity -= item.quantity
                        item.product.save()
                        
                    # Clear cart
                    Cart.objects.filter(user=request.user).delete()
                    
                return JsonResponse({'status': 'success', 'message': 'Payment verified successfully'})
            else:
                return JsonResponse({'error': 'Payment verification failed: Amount mismatch'}, status=400)
        else:
            return JsonResponse({'error': 'Payment verification failed at gateway'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})
