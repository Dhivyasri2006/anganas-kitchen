
import re
import uuid

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction

from .models import Product, CartItem, Order, OrderItem

User = get_user_model()


def home(request):
    return render(request, 'home.html')


def all_products(request):
    q = request.GET.get('q', '').strip()

    if q:
        products = Product.objects.filter(name__icontains=q)
    else:
        products = Product.objects.all()

    return render(request, 'all_products.html', {
        'products': products,
        'q': q
    })



def category_products(request, category):
    products = Product.objects.filter(category=category)
    return render(request, 'category_products.html', {
        'products': products,
        'category': category
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


def register(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not full_name or not email or not password or not confirm_password:
            messages.error(request, 'Please fill in all fields.')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif not re.search(r'[A-Za-z]', password):
            messages.error(request, 'Password must contain at least one alphabet.')
        elif not re.search(r'[0-9]', password):
            messages.error(request, 'Password must contain at least one number.')
        elif not re.search(r'[^A-Za-z0-9\s]', password):
            messages.error(request, 'Password must contain at least one special symbol.')
        else:
            new_user = User(
                username=email,
                email=email,
                first_name=full_name
            )
            new_user.set_password(password)
            new_user.save()
            login(request, new_user)
            messages.success(request, 'Your account has been created successfully!')

            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)

            return redirect('home')

    return render(request, 'register.html', {'next': next_url})


def customer_login(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')

            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)

            return redirect('home')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html', {'next': next_url})


def customer_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        messages.error(request, 'Please select a valid quantity.')
        return redirect('product_detail', product_id=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    messages.success(request, f'{quantity} × {product.name} added to your cart!')
    return redirect('cart')


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('product')

    total = sum(item.total_price for item in cart_items)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required
def update_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart')

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    action = request.POST.get('action')

    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, 'Quantity increased.')

    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, 'Quantity decreased.')
        else:
            messages.info(request, 'Minimum quantity is 1.')

    return redirect('cart')


@login_required
def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart')

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    product_name = cart_item.product.name
    cart_item.delete()

    messages.success(request, f'{product_name} removed from your cart.')
    return redirect('cart')


@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('product')

    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    total = sum(item.total_price for item in cart_items)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total
    })


@login_required
def place_order(request):
    if request.method != 'POST':
        return redirect('checkout')

    customer_name = request.POST.get('customer_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not customer_name or not email or not phone or not address:
        messages.error(request, 'Please fill in all delivery details.')
        return redirect('checkout')

    if not re.fullmatch(r'[0-9]{10}', phone):
        messages.error(request, 'Please enter a valid 10-digit phone number.')
        return redirect('checkout')

    with transaction.atomic():
        cart_items = list(
            CartItem.objects.filter(
                user=request.user
            ).select_related('product')
        )

        if not cart_items:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')

        total = sum(item.total_price for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            order_number=f"AK-{uuid.uuid4().hex[:10].upper()}",
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            total_amount=total,
            status='processing'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                pack_size=item.product.quantity,
                price=item.product.price,
                quantity=item.quantity
            )

        CartItem.objects.filter(user=request.user).delete()

    messages.success(request, 'Your demo order has been placed successfully!')
    return redirect('order_success', order_number=order.order_number)


@login_required
def order_success(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )

    return render(request, 'order_success.html', {'order': order})
@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'my_orders.html', {
        'orders': orders
    })
def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')

@login_required
def my_profile(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()

        if not full_name or not email:
            messages.error(request, 'Please fill in all fields.')

        elif User.objects.filter(email__iexact=email).exclude(
            pk=request.user.pk
        ).exists():
            messages.error(request, 'This email is already registered.')

        elif User.objects.filter(username__iexact=email).exclude(
            pk=request.user.pk
        ).exists():
            messages.error(request, 'This email is already in use.')

        else:
            request.user.first_name = full_name
            request.user.email = email
            request.user.username = email
            request.user.save()

            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('my_profile')

    return render(request, 'my_profile.html', {
        'profile_user': request.user
    })
