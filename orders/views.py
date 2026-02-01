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

def calculate_shipping(city):
    # Simple logic for now
    if not city:
        return 2500
    city = city.lower()
    if 'lagos' in city:
        return 1000
    return 2500

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(Product, id=product_id)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = quantity
            cart_item.save()
            
            # Calculate total items
            total_items = sum(item.quantity for item in cart.items.all())
            
            return JsonResponse({
                'status': 'success', 
                'cart_count': total_items,
                'message': 'Item added to cart successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {
        'cart': cart,
        'cart_items': cart.items.all(),
        'total_price': cart.total_price
    })

@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        item.delete()
        
        return JsonResponse({
            'status': 'success', 
            'cart_total': float(cart.total_price),
            'cart_count': cart.items.count()
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_cart_quantity(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        action = data.get('action')
        
        cart = get_object_or_404(Cart, user=request.user)
        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        
        if action == 'increase':
            item.quantity += 1
        elif action == 'decrease':
            item.quantity -= 1
            if item.quantity < 1:
                item.delete()
                return JsonResponse({
                    'status': 'success',
                    'cart_total': float(cart.total_price),
                    'cart_count': cart.items.count(),
                    'removed': True
                })
        
        item.save()
        
        return JsonResponse({
            'status': 'success',
            'item_total': float(item.total_price),
            'cart_total': float(cart.total_price),
            'cart_count': cart.items.count(),
            'quantity': item.quantity
        })
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        return redirect('cart')
        
    context = {
        'cart': cart,
        'flutterwave_public_key': settings.FLUTTERWAVE_PUBLIC_KEY
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

@csrf_exempt
@login_required
def verify_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        transaction_id = data.get('transaction_id')
        tx_ref = data.get('tx_ref')
        
        try:
            # Verify with Flutterwave
            headers = {
                'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            response = requests.get(
                f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify',
                headers=headers
            )
            response_data = response.json()
            
            if response_data['status'] == 'success':
                amount = response_data['data']['amount']
                
                order = Order.objects.get(order_id=tx_ref)
                
                # Check if amount matches (allowing for small floating point differences)
                if abs(float(order.total_amount) - float(amount)) < 1.0:
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
            
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def order_history(request):
    return redirect('profile')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})
